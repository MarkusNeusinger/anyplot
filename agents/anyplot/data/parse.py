"""Deterministic parse of pasted data into a canonical `data.csv` and a `DatasetProfile`.

The design is docs/concepts/agent-network.md, "Parse". The module imports neither
ADK nor pandas: it reads with `csv`, `json` and explicit regular expressions, so
every typing rule is written here instead of left to pandas' inference (which
would, for example, read `01.02.2024` as a number under `thousands='.'`).

`parse_dataset` runs these steps in order:

1. **Limits on the raw text.** At most `MAX_INPUT_BYTES` (200 KiB) of UTF-8
   (`too_long`); no control character other than tab, line feed and carriage
   return (`control_chars`: every Unicode `Cc` character, which is C0, DEL and C1).
2. **Normalise.** Strip a leading BOM and apply NFC.
3. **Read every cell as text.** JSON when the first non-blank character is `[` or
   `{`: an array of flat records (`json_records`) or an object of equally long
   column lists (`json_columns`), nesting depth at most 2; `null`, `NaN` and
   `Infinity` are missing. Anything else is delimited text, see `sniff_delimiter`.
   Fully blank lines (also `;;;`-style lines of empty fields) are skipped; a row
   with fewer fields than the header is padded with missing cells (one warning);
   a row with more non-empty fields than the header is `unparseable`.
4. **Clean every cell.** Remove invisible format characters (Unicode category
   `Cf`: zero-width characters, bidi controls, BOMs inside the text, tag
   characters), turn line and paragraph separators (U+2028, U+2029) into spaces,
   turn CRLF and CR inside a quoted cell into LF, strip surrounding whitespace,
   and map `MISSING_VALUES` to an empty cell. One warning per column that lost
   invisible characters. A cell (header or value) longer than
   `MAX_INPUT_CELL_CHARS` after cleaning is `cell_too_long`.
5. **Canonicalise the headers**, see `canonical_headers`. A column without a
   header whose cells are all missing (the trailing-delimiter column of many
   spreadsheet exports) is dropped with a warning before the 50-column check.
6. **Type each column**, see `_type_column`: dates, then booleans, integers,
   numbers, otherwise text.
7. **Write the canonical `data.csv`** (comma, dot decimal, ISO dates, canonical
   headers, missing as an empty cell, `\\n` line ends) and profile it.

The loader reads the result with
`pd.read_csv("data.csv", dtype=pandas_dtypes(column_dtypes), parse_dates=parse_dates)`
and gets the typed frame back: `MISSING_VALUES` contains every token pandas reads
as missing by default, so no such token survives into `data.csv` as text.

Error messages never quote the user's data; at most they name a column.
"""

import csv
import io
import json
import math
import re
import unicodedata
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from ..schemas import (
    MAX_CELL_CHARS,
    MAX_COLUMN_NAME_CHARS,
    MAX_COLUMNS,
    MAX_NOTE_CHARS,
    MAX_ROWS,
    MAX_SAMPLE_ROWS,
    MAX_TOP_VALUES,
    MAX_WARNINGS,
    ColumnDtype,
    ColumnProfile,
    DatasetProfile,
    SourceFormat,
)


MAX_INPUT_BYTES = 200 * 1024  # "200 KB", counted like the schemas' 24 KiB: 204,800 UTF-8 bytes
MAX_INPUT_CELL_CHARS = 200  # per header or cell, after cleaning; the profile's own cells stop at MAX_CELL_CHARS
PREVIEW_ROWS = 20
SNIFF_LINES = 10

# Candidate delimiters in tie-break order, with the source format each one reports.
DELIMITERS: tuple[tuple[str, SourceFormat], ...] = ((",", "csv"), (";", "semicolon"), ("\t", "tsv"), ("|", "pipe"))

# A cell is missing when, after cleaning, it is exactly one of these. The set is the
# design's list (empty, `NA`, `NaN`, `null`, `-`) plus every other token pandas reads as
# missing by default (`pandas._libs.parsers.STR_NA_VALUES`), so that a plain
# `pd.read_csv` of `data.csv` never turns a text cell into NaN behind the profile's back.
MISSING_VALUES: frozenset[str] = frozenset(
    {
        "",
        "-",
        "NA",
        "N/A",
        "n/a",
        "NaN",
        "nan",
        "-NaN",
        "-nan",
        "null",
        "NULL",
        "None",
        "<NA>",
        "#N/A",
        "#N/A N/A",
        "#NA",
        "1.#IND",
        "-1.#IND",
        "1.#QNAN",
        "-1.#QNAN",
    }
)

# The `dtype=` argument of the loader's `pd.read_csv`; datetime columns go to `parse_dates`.
# The nullable `Int64` and `boolean` keep missing cells without turning the column into floats.
PANDAS_DTYPES: dict[ColumnDtype, str] = {"integer": "Int64", "number": "float64", "boolean": "boolean", "text": "str"}

ParseErrorCode = Literal[
    "too_long", "unparseable", "too_many_columns", "too_many_rows", "cell_too_long", "control_chars"
]

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")
_HEADER_BREAKS = re.compile(r"[\t\r\n]+")
_PHYSICAL_LINE = re.compile(r"\r\n|\r|\n")
_WHITESPACE_RUN = re.compile(r"\s+")

# ASCII digits only: `\d` and `int()` also accept other scripts' digits, which pandas does not.
_INTEGER = re.compile(r"[+-]?[0-9]+")
_LEADING_ZERO = re.compile(r"[+-]?0[0-9]+")
_FLOAT = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")
_DECIMAL_COMMA = re.compile(r"[+-]?(?:[0-9]{1,3}(?:\.[0-9]{3})+|[0-9]+)(?:,[0-9]+)?")
_THOUSANDS_DOT = re.compile(r"[+-]?(?:[0-9]{1,3}(?:\.[0-9]{3})+|[0-9]+)")
_AMBIGUOUS_COMMA = re.compile(r"[+-]?[0-9]{1,3},[0-9]{3}")

_ISO_TIME = r"(?:[T ]([0-9]{2}):([0-9]{2})(?::([0-9]{2}))?)?"
_LOCAL_TIME = r"(?: ([0-9]{1,2}):([0-9]{2})(?::([0-9]{2}))?)?"
_ISO_DATE = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})" + _ISO_TIME)
_DOT_DATE = re.compile(r"([0-9]{1,2})\.([0-9]{1,2})\.([0-9]{4})" + _LOCAL_TIME)
_SLASH_DATE = re.compile(r"([0-9]{1,2})/([0-9]{1,2})/([0-9]{4})" + _LOCAL_TIME)

_DATE_FORMATS: tuple[tuple[re.Pattern[str], str], ...] = (
    (_ISO_DATE, "iso"),
    (_DOT_DATE, "dot"),
    (_SLASH_DATE, "slash"),
)

_INT64_MIN, _INT64_MAX = -(2**63), 2**63 - 1
_BOM = "\N{ZERO WIDTH NO-BREAK SPACE}"
_NO_DELIMITER = "\x00"  # NUL never survives the control-character check, so it never splits a line


class ParseError(Exception):
    """A dataset the parser refuses; `code` maps to the route's error, `message` is safe to show."""

    def __init__(self, code: ParseErrorCode, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code: ParseErrorCode = code
        self.message = message


@dataclass(frozen=True)
class ParsedDataset:
    """The parse result: profile, canonical `data.csv` text, preview and the loader's typing."""

    profile: DatasetProfile
    csv: str
    preview: list[list[str]]
    column_dtypes: dict[str, ColumnDtype]
    parse_dates: list[str]
    warnings: list[str]


@dataclass
class _Column:
    """One column on its way from cleaned text to canonical cells; "" is missing in both."""

    name: str
    source: list[str]  # cleaned cells, as pasted
    cells: list[str]  # canonical cells for data.csv, set by the typing step
    invisible: bool = False
    dtype: ColumnDtype = "text"
    numbers: list[float] = field(default_factory=list)
    dates: list[datetime] = field(default_factory=list)
    with_time: bool = False
    decimal_comma: bool = False
    notes: list[str] = field(default_factory=list)


def pandas_dtypes(column_dtypes: Mapping[str, ColumnDtype]) -> dict[str, str]:
    """The loader's `dtype=` mapping: every column except the datetime ones, which `parse_dates` takes."""
    return {name: PANDAS_DTYPES[dtype] for name, dtype in column_dtypes.items() if dtype != "datetime"}


def parse_dataset(text: str) -> ParsedDataset:
    """Parse pasted CSV, TSV, semicolon or pipe text or JSON into the canonical dataset."""
    _check_size(text)
    text = text.removeprefix(_BOM)
    _check_controls(text)
    text = unicodedata.normalize("NFC", text)
    stripped = text.strip()
    if not stripped:
        raise ParseError("unparseable", "the data is empty")

    warnings: list[str] = []
    if stripped[0] in "[{":
        headers, rows, source_format = _read_json(stripped, warnings)
    else:
        headers, rows, source_format = _read_delimited(text, warnings)
    return _build(headers, rows, source_format, warnings)


# --- Limits ------------------------------------------------------------------------------


def _check_size(text: str) -> None:
    try:
        size = len(text.encode("utf-8"))
    except UnicodeEncodeError:
        raise ParseError("unparseable", "the data is not valid Unicode text") from None
    if size > MAX_INPUT_BYTES:
        raise ParseError("too_long", f"the data is larger than {MAX_INPUT_BYTES // 1024} KB")


def _check_controls(text: str) -> None:
    match = _CONTROL.search(text)
    if match:
        line = len(_PHYSICAL_LINE.findall(text, 0, match.start())) + 1
        raise ParseError(
            "control_chars", f"the data contains a control character (U+{ord(match.group()):04X}) on line {line}"
        )


# --- Readers -----------------------------------------------------------------------------


def sniff_delimiter(text: str) -> tuple[str | None, SourceFormat]:
    """Pick the delimiter from the first `SNIFF_LINES` non-blank lines.

    Each candidate (`,` `;` tab `|`) splits those lines with the csv module, quotes
    honoured. A candidate counts only if it splits the header line into at least two
    fields. Among those, the one under which the most sampled lines have exactly the
    header's field count wins, then the one with more header fields, then the earlier
    candidate in that order. When no candidate splits the header, the text is a single
    column (returned as `None`, reported as `csv`). A semicolon file with decimal
    commas therefore never sniffs as comma-separated: its header has no comma.
    """
    lines = [line for line in _PHYSICAL_LINE.split(text) if line.strip()][:SNIFF_LINES]
    sample = "\n".join(lines)
    best: tuple[int, int] | None = None
    choice: tuple[str | None, SourceFormat] = (None, "csv")
    for delimiter, source_format in DELIMITERS:
        try:
            rows = [row for row in csv.reader(io.StringIO(sample), delimiter=delimiter, skipinitialspace=True) if row]
        except csv.Error:
            continue
        if not rows or len(rows[0]) < 2:
            continue
        width = len(rows[0])
        key = (sum(1 for row in rows[1:] if len(row) == width), width)
        if best is None or key > best:
            best, choice = key, (delimiter, source_format)
    return choice


def _read_delimited(text: str, warnings: list[str]) -> tuple[list[str], list[list[str]], SourceFormat]:
    delimiter, source_format = sniff_delimiter(text)
    reader = csv.reader(
        io.StringIO(text, newline=""), delimiter=delimiter or _NO_DELIMITER, skipinitialspace=True, strict=True
    )
    header: list[str] | None = None
    rows: list[list[str]] = []
    padded = 0
    try:
        for record in reader:
            if not any(cell.strip() for cell in record):
                continue
            if header is None:
                header = record
                continue
            if len(rows) == MAX_ROWS:
                raise ParseError("too_many_rows", f"the data has more than {MAX_ROWS:,} rows")
            width = len(header)
            if len(record) < width:
                record = record + [""] * (width - len(record))
                padded += 1
            elif len(record) > width:
                if any(cell.strip() for cell in record[width:]):
                    raise ParseError("unparseable", f"line {reader.line_num} has more fields than the header")
                record = record[:width]
            rows.append(record)
    except csv.Error as exc:
        raise ParseError("unparseable", f"the quoting is malformed near line {reader.line_num}") from exc
    if header is None:
        raise ParseError("unparseable", "the data is empty")
    if padded:
        warnings.append(f"{_count(padded, 'row')} had fewer fields than the header; the missing cells are empty")
    return header, rows, source_format


def _read_json(text: str, warnings: list[str]) -> tuple[list[str], list[list[str]], SourceFormat]:
    try:
        data = json.loads(text, parse_constant=lambda _: None)
    except (ValueError, RecursionError):
        raise ParseError("unparseable", "the data starts like JSON but is not valid JSON") from None

    if isinstance(data, list):
        if not data:
            raise ParseError("unparseable", "the JSON array is empty")
        if len(data) > MAX_ROWS:
            raise ParseError("too_many_rows", f"the data has more than {MAX_ROWS:,} rows")
        if not all(isinstance(record, dict) for record in data):
            raise ParseError("unparseable", "a JSON array must hold objects, one per row")
        keys: dict[str, int] = {}
        for record in data:
            for key in record:
                if key not in keys:
                    keys[key] = len(keys)
                    if len(keys) > MAX_COLUMNS:
                        raise ParseError("too_many_columns", f"the data has more than {MAX_COLUMNS} columns")
        headers = [_json_key(key, position) for key, position in keys.items()]
        rows: list[list[str]] = []
        incomplete = 0
        for record in data:
            if len(record) < len(keys):
                incomplete += 1
            rows.append([_json_cell(record[key], position) if key in record else "" for key, position in keys.items()])
        if incomplete:
            warnings.append(f"{_count(incomplete, 'record')} lack some keys; those cells are empty")
        return headers, rows, "json_records"

    if isinstance(data, dict):
        if not data:
            raise ParseError("unparseable", "the JSON object is empty")
        if len(data) > MAX_COLUMNS:
            raise ParseError(
                "too_many_columns", f"the data has {len(data)} columns; at most {MAX_COLUMNS} are supported"
            )
        if not all(isinstance(values, list) for values in data.values()):
            raise ParseError("unparseable", "a JSON object must map each column name to a list of values")
        lengths = {len(values) for values in data.values()}
        if len(lengths) != 1:
            raise ParseError("unparseable", "the JSON column lists have different lengths")
        if lengths.pop() > MAX_ROWS:
            raise ParseError("too_many_rows", f"the data has more than {MAX_ROWS:,} rows")
        headers = [_json_key(key, position) for position, key in enumerate(data)]
        columns = [[_json_cell(value, position) for value in values] for position, values in enumerate(data.values())]
        return headers, [list(row) for row in zip(*columns, strict=True)], "json_columns"

    raise ParseError("unparseable", "JSON data must be an array of records or an object of column lists")


def _json_text(text: str, what: str) -> str:
    """A decoded JSON string passes the raw-text checks too: its escapes can hide controls or lone surrogates."""
    match = _CONTROL.search(text)
    if match:
        raise ParseError("control_chars", f"{what} contains a control character (U+{ord(match.group()):04X})")
    try:
        text.encode("utf-8")
    except UnicodeEncodeError:
        raise ParseError("unparseable", f"{what} is not valid Unicode text") from None
    return text


def _json_key(key: str, position: int) -> str:
    return _json_text(key, f"the name of column {position + 1}")


def _json_cell(value: object, position: int) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, str):
        return _json_text(value, f"a value in column {position + 1}")
    raise ParseError("unparseable", f"column {position + 1} holds nested values; only flat records are supported")


# --- Cleaning and headers ----------------------------------------------------------------


def _strip_invisible(text: str) -> tuple[str, bool]:
    """Remove `Cf` characters and turn U+2028 and U+2029 into spaces; report whether anything changed."""
    if text.isascii():
        return text, False
    kept: list[str] = []
    changed = False
    for char in text:
        category = unicodedata.category(char)
        if category == "Cf":
            changed = True
        elif category in ("Zl", "Zp"):
            kept.append(" ")
            changed = True
        else:
            kept.append(char)
    return ("".join(kept), True) if changed else (text, False)


def _clean_cell(raw: str) -> tuple[str, bool]:
    text, invisible = _strip_invisible(raw)
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    return ("" if text in MISSING_VALUES else text), invisible


def _clean_header(raw: str) -> tuple[str, bool, bool]:
    """The header text, whether invisible characters went, and whether tabs or line breaks became spaces."""
    text, invisible = _strip_invisible(raw)
    text = text.strip()
    spaced = _HEADER_BREAKS.sub(" ", text)
    return spaced, invisible, spaced != text


def canonical_headers(headers: Sequence[str]) -> tuple[list[str], list[str]]:
    """Canonical column names and one warning per rename.

    The input is the cleaned header text (NFC, invisible characters removed, tabs and
    line breaks turned into spaces, surrounding whitespace stripped). An empty name
    becomes `column_N` (N is the 1-based position); a name over 64 characters is cut
    to 64; a repeated name gets `_2`, `_3`, ... (the first occurrence keeps it), cut
    so the suffixed name still fits in 64 characters. Names compare case-sensitively,
    as pandas does.
    """
    names: list[str] = []
    warnings: list[str] = []
    used: set[str] = set()
    for position, header in enumerate(headers, start=1):
        name = header
        if not name:
            name = f"column_{position}"
            warnings.append(f"column {position}: empty header named '{name}'")
        elif len(name) > MAX_COLUMN_NAME_CHARS:
            name = name[:MAX_COLUMN_NAME_CHARS].rstrip()
            warnings.append(
                f"column {position}: header longer than {MAX_COLUMN_NAME_CHARS} characters shortened to '{name}'"
            )
        if name in used:
            base, suffix = name, 2
            while name in used:
                tail = f"_{suffix}"
                name = base[: MAX_COLUMN_NAME_CHARS - len(tail)] + tail
                suffix += 1
            warnings.append(f"column {position}: duplicate header '{base}' renamed to '{name}'")
        used.add(name)
        names.append(name)
    return names, warnings


# --- Typing ------------------------------------------------------------------------------


def _type_column(column: _Column) -> None:
    """Give the column its dtype and canonical cells, in this order of attempts.

    1. **datetime**: every non-missing cell matches one format: ISO
       `YYYY-MM-DD[(T| )HH:MM[:SS]]`, `DD.MM.YYYY`, or `DD/MM/YYYY` / `MM/DD/YYYY`,
       the last three with an optional ` HH:MM[:SS]` and one- or two-digit day and
       month. A slash column is day-first when a first part exceeds 12, month-first
       when a second part does, not a date when both happen, and day-first with a
       warning when neither does. Written as `YYYY-MM-DD`, or `YYYY-MM-DDTHH:MM:SS`
       for the whole column when any cell has a time.
    2. **boolean**: `true` / `false` in any letter case, written `True` / `False`.
    3. **integer**: ASCII digits with an optional sign within int64. A column with a
       leading zero (`007`) stays text, because the zeros are part of the value.
    4. **number**: dot decimals with an optional exponent, written in Python's
       shortest round-trip form; then decimal commas when every cell has the
       `1.234,56` or `1234,56` shape and at least one has a comma. Dates were tried
       first, so `DD.MM.YYYY` never reads as a thousands-dot number.
    5. **text**: everything else, and every column without a non-missing cell.
    """
    column.cells = list(column.source)
    present = [cell for cell in column.source if cell]
    if not present:
        return
    if _as_dates(column, present):
        return
    if all(cell.casefold() in ("true", "false") for cell in present):
        column.dtype = "boolean"
        column.cells = [("True" if cell.casefold() == "true" else "False") if cell else "" for cell in column.source]
        return
    if all(_INTEGER.fullmatch(cell) for cell in present):
        if any(_LEADING_ZERO.fullmatch(cell) for cell in present):
            column.notes.append("numbers with leading zeros kept as text")
            return
        if _as_integers(column, column.source):
            return
    if all(_FLOAT.fullmatch(cell) for cell in present):
        _as_numbers(column, column.source)
        return
    if all(_DECIMAL_COMMA.fullmatch(cell) for cell in present) and any("," in cell for cell in present):
        if _as_numbers(column, [cell.replace(".", "").replace(",", ".") for cell in column.source]):
            column.decimal_comma = True
            commas = [cell for cell in present if "," in cell]
            if all(_AMBIGUOUS_COMMA.fullmatch(cell) for cell in commas) and not any("." in cell for cell in present):
                column.notes.append("commas read as decimal commas; remove them first if they separate thousands")


def _retype_thousands_dots(column: _Column) -> None:
    """In a file with decimal commas, a dot-number column of `1.234` shapes holds thousands separators."""
    present = [cell for cell in column.source if cell]
    if not (all(_THOUSANDS_DOT.fullmatch(cell) for cell in present) and any("." in cell for cell in present)):
        return
    cells = [cell.replace(".", "") for cell in column.source]
    if not _as_integers(column, cells):
        _as_numbers(column, cells)
    column.decimal_comma = True
    column.notes.append("dots read as thousands separators, as in the file's decimal-comma columns")


def _as_integers(column: _Column, cells: list[str]) -> bool:
    values = [int(cell) if cell else None for cell in cells]
    if any(value is not None and not _INT64_MIN <= value <= _INT64_MAX for value in values):
        return False
    column.dtype = "integer"
    column.cells = ["" if value is None else str(value) for value in values]
    column.numbers = [float(value) for value in values if value is not None]
    return True


def _as_numbers(column: _Column, cells: list[str]) -> bool:
    values = [float(cell) if cell else None for cell in cells]
    finite = [value for value in values if value is not None]
    if not all(math.isfinite(value) for value in finite):
        return False
    column.dtype = "number"
    column.cells = ["" if value is None else repr(value) for value in values]
    column.numbers = finite
    return True


def _match_all(pattern: re.Pattern[str], cells: list[str]) -> dict[str, tuple[int, ...]] | None:
    """Each distinct cell's date and time fields as integers (an absent time is 0), or None on a miss."""
    fields: dict[str, tuple[int, ...]] = {}
    for cell in cells:
        match = pattern.fullmatch(cell)
        if match is None:
            return None
        fields[cell] = tuple(int(part) if part else 0 for part in match.groups())
    return fields


def _as_dates(column: _Column, present: list[str]) -> bool:
    kind, fields = "", None
    for pattern, candidate in _DATE_FORMATS:
        fields = _match_all(pattern, present)
        if fields is not None:
            kind = candidate
            break
    if fields is None:
        return False

    day_first = True
    if kind == "slash":
        first_big = any(parts[0] > 12 for parts in fields.values())
        second_big = any(parts[1] > 12 for parts in fields.values())
        if first_big and second_big:
            return False
        day_first = not second_big
        if not first_big and not second_big and any(parts[0] != parts[1] for parts in fields.values()):
            column.notes.append("day and month order is ambiguous; read as DD/MM/YYYY")

    parsed: dict[str, datetime] = {}
    for cell, parts in fields.items():
        if kind == "iso":
            year, month, day = parts[0], parts[1], parts[2]
        elif day_first:
            day, month, year = parts[0], parts[1], parts[2]
        else:
            month, day, year = parts[0], parts[1], parts[2]
        try:
            parsed[cell] = datetime(year, month, day, parts[3], parts[4], parts[5])
        except ValueError:
            return False
    column.dtype = "datetime"
    column.with_time = any(":" in cell for cell in present)
    column.dates = [parsed[cell] for cell in column.source if cell]
    column.cells = [_iso(parsed[cell], column.with_time) if cell else "" for cell in column.source]
    return True


def _iso(value: datetime, with_time: bool) -> str:
    return value.isoformat(timespec="seconds") if with_time else value.date().isoformat()


# --- Build -------------------------------------------------------------------------------


def _build(
    raw_headers: list[str], raw_rows: list[list[str]], source_format: SourceFormat, warnings: list[str]
) -> ParsedDataset:
    headers: list[str] = []
    columns: list[_Column] = []
    renamed_by_breaks: list[int] = []
    for position, raw in enumerate(raw_headers):
        header, invisible, broken = _clean_header(raw)
        cells: list[str] = []
        for row in raw_rows:
            cell, cell_invisible = _clean_cell(row[position])
            cells.append(cell)
            invisible = invisible or cell_invisible
        if not header and not any(cells):
            continue
        if broken:
            renamed_by_breaks.append(len(headers))
        headers.append(header)
        columns.append(_Column(name="", source=cells, cells=[], invisible=invisible))

    dropped = len(raw_headers) - len(headers)
    if dropped:
        warnings.append(f"{_count(dropped, 'empty column')} without a header dropped")
    if not columns:
        raise ParseError("unparseable", "the data has no columns")
    if len(columns) > MAX_COLUMNS:
        raise ParseError(
            "too_many_columns", f"the data has {len(columns)} columns; at most {MAX_COLUMNS} are supported"
        )
    if not raw_rows:
        raise ParseError("unparseable", "the data has a header but no rows")
    for position, header in enumerate(headers, start=1):
        if len(header) > MAX_INPUT_CELL_CHARS:
            raise ParseError(
                "cell_too_long", f"the header of column {position} has more than {MAX_INPUT_CELL_CHARS} characters"
            )

    names, header_warnings = canonical_headers(headers)
    for index in renamed_by_breaks:
        warnings.append(f"column '{names[index]}': tabs or line breaks in the header replaced with spaces")
    warnings.extend(header_warnings)
    if all(_looks_like_value(name) for name in names):
        warnings.append("every header looks like a value; the first row may be data rather than column names")

    for name, column in zip(names, columns, strict=True):
        column.name = name
        if any(len(cell) > MAX_INPUT_CELL_CHARS for cell in column.source):
            raise ParseError(
                "cell_too_long", f"a cell in column '{name}' has more than {MAX_INPUT_CELL_CHARS} characters"
            )
    for column in columns:
        _type_column(column)
    if any(column.decimal_comma for column in columns):
        for column in columns:
            if column.dtype == "number" and not column.decimal_comma:
                _retype_thousands_dots(column)
    for column in columns:
        if column.invisible:
            warnings.append(f"column '{column.name}': invisible formatting characters (zero-width or bidi) removed")
        warnings.extend(f"column '{column.name}': {note}" for note in column.notes)

    rows = [list(row) for row in zip(*(column.cells for column in columns), strict=True)]
    capped = _cap_warnings(warnings)
    profile = DatasetProfile(
        rows=len(rows),
        columns=[_profile_column(column) for column in columns],
        sample=[[_clip(cell) for cell in row] for row in rows[:MAX_SAMPLE_ROWS]],
        source_format=source_format,
        decimal="," if any(column.decimal_comma for column in columns) else ".",
        warnings=capped,
    )
    return ParsedDataset(
        profile=profile,
        csv=_write_csv(names, rows),
        preview=[[_clip(cell) for cell in row] for row in rows[:PREVIEW_ROWS]],
        column_dtypes={column.name: column.dtype for column in columns},
        parse_dates=[column.name for column in columns if column.dtype == "datetime"],
        warnings=capped,
    )


def _profile_column(column: _Column) -> ColumnProfile:
    present = [cell for cell in column.cells if cell]
    minimum: float | str | None = None
    maximum: float | str | None = None
    top: list[str] = []
    if column.dtype in ("integer", "number") and column.numbers:
        minimum, maximum = min(column.numbers), max(column.numbers)
    elif column.dtype == "datetime" and column.dates:
        minimum, maximum = _iso(min(column.dates), column.with_time), _iso(max(column.dates), column.with_time)
    elif column.dtype in ("text", "boolean"):
        for value, _ in Counter(present).most_common():
            clipped = _clip(value)
            if clipped not in top:
                top.append(clipped)
            if len(top) == MAX_TOP_VALUES:
                break
    return ColumnProfile(
        name=column.name,
        dtype=column.dtype,
        missing=len(column.cells) - len(present),
        unique=len(set(present)),
        min=minimum,
        max=maximum,
        top=top,
    )


def _write_csv(names: list[str], rows: list[list[str]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(names)
    writer.writerows(rows)
    return buffer.getvalue()


def _looks_like_value(name: str) -> bool:
    return bool(
        _FLOAT.fullmatch(name)
        or _DECIMAL_COMMA.fullmatch(name)
        or _ISO_DATE.fullmatch(name)
        or _DOT_DATE.fullmatch(name)
        or _SLASH_DATE.fullmatch(name)
    )


def _clip(text: str, limit: int = MAX_CELL_CHARS) -> str:
    """A display copy for the preview, the sample and top values: one line, at most `limit` characters."""
    text = _WHITESPACE_RUN.sub(" ", text)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _cap_warnings(warnings: list[str]) -> list[str]:
    """At most `MAX_WARNINGS`, the last slot noting how many were left out; each within `MAX_NOTE_CHARS`."""
    notes = [_clip(warning, MAX_NOTE_CHARS) for warning in warnings]
    if len(notes) <= MAX_WARNINGS:
        return notes
    kept = notes[: MAX_WARNINGS - 1]
    return [*kept, f"{len(notes) - len(kept)} more warnings omitted"]


def _count(number: int, noun: str) -> str:
    return f"{number} {noun}" if number == 1 else f"{number} {noun}s"
