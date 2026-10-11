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
3. **Read every cell as text.** A literal when the first non-blank character is
   `[`, `{` or `(`, also behind a Python assignment (`cat_day = {`), which is
   stripped: `json.loads` first, then `ast.literal_eval` for a Python literal
   (single quotes, trailing commas, tuples, `True` / `False` / `None`; a name or
   a call is refused, and a bracket count that skips quoted strings and `#`
   comments refuses more than `MAX_NESTING` levels before anything is
   evaluated). Both give one of four shapes: an array of flat records
   (`json_records`), an object of equally long column lists (`json_columns`),
   or an object of scalars or an array of `[category, value]` pairs
   (`json_pairs`: the columns `category` and `value`, one row per entry, in the
   pasted order; the keys stay text, the values are typed); nesting depth at
   most 2; `null`, `NaN` and `Infinity` are missing; a key repeated in an object
   keeps its last value, with a warning. Text that starts with a bare `(` and is
   neither JSON nor a Python literal (a header such as `(in %) Land`, or prose
   in parentheses) is delimited text instead, like everything that starts
   otherwise, see `sniff_delimiter`.
   Fully blank lines (also `;;;`-style lines of empty fields) are skipped; a row
   with fewer fields than the header is padded with missing cells (one warning);
   a row with more non-empty fields than the header is `unparseable`.
4. **Clean every cell.** Remove invisible format characters (Unicode category
   `Cf`: zero-width characters, bidi controls, BOMs inside the text, tag
   characters), turn line and paragraph separators (U+2028, U+2029) into spaces,
   turn CRLF and CR inside a quoted cell into LF, strip surrounding whitespace,
   and map `MISSING_VALUES` to an empty cell. One warning per column that lost
   invisible characters. A cell (header or value) longer than
   `MAX_INPUT_CELL_CHARS` after cleaning is `cell_too_long`, checked before any
   typing reads the cell. A column without a header whose cells are all missing
   (the trailing-delimiter column of many spreadsheet exports) is dropped with a
   warning before the 50-column check.
5. **Type each column**, see `_type_column`: dates, then booleans, integers,
   numbers, then the same numbers behind one unit shared by every cell (`65 %`,
   `15,6 h`, `€ 5`, also with a no-break space; the unit leaves the cells),
   otherwise text.
6. **Canonicalise the headers**, see `canonical_headers`. A column whose cells
   carried a unit is named `<name> (<unit>)` there, so the duplicate suffixes and
   the 64-character cap cover the new name too (one warning per such column); a
   header that already names the unit (`Anteil (%)`, `Preis in €`) keeps its name.
7. **Write the canonical `data.csv`** (comma, dot decimal, ISO dates, canonical
   headers, missing as an empty cell, `\\n` line ends) and profile it.

The loader reads the result with
`pd.read_csv("data.csv", dtype=pandas_dtypes(column_dtypes), parse_dates=parse_dates)`
and gets the typed frame back: `MISSING_VALUES` contains every token pandas reads
as missing by default, so no such token survives into `data.csv` as text.

`text_columns` names columns that skip step 6 and stay text whatever their cells
hold: the `prepare_data` operation `set_type text` keeps a column of years or ids as
a category through the re-parse of every later version (`prepare.py`), and the
result records them in `ParsedDataset.text_columns`, so the store carries them on.

Error messages never quote the user's data; at most they name a column.
"""

import ast
import csv
import io
import json
import math
import re
import statistics
import tokenize
import unicodedata
from collections import Counter
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

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
MAX_NESTING = 50  # bracket levels a literal may open; counted before `ast.literal_eval` sees the text
PAIR_HEADERS = ("category", "value")  # the columns of an object of scalars or an array of pairs

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
    "too_long", "unparseable", "no_table", "too_many_columns", "too_many_rows", "cell_too_long", "control_chars"
]
"""`no_table` is text with no table in it (no columns, or a header line without rows: prose,
a list on one line); the route hands such text to the transcriber. `unparseable` is a table
that is broken (ragged rows, malformed quoting, invalid JSON), which stays a refusal."""

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")
_HEADER_BREAKS = re.compile(r"[\t\r\n]+")
_PHYSICAL_LINE = re.compile(r"\r\n|\r|\n")
_WHITESPACE_RUN = re.compile(r"\s+")

# ASCII digits only: `\d` and `int()` also accept other scripts' digits, which pandas does not.
_INTEGER = re.compile(r"[+-]?[0-9]+")
_LEADING_ZERO = re.compile(r"[+-]?0[0-9]+")
_FLOAT = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")
# A thousands-grouped number never starts with a zero group: `0.125` is a dot decimal.
_DECIMAL_COMMA = re.compile(r"[+-]?(?:[1-9][0-9]{0,2}(?:\.[0-9]{3})+|[0-9]+)(?:,[0-9]+)?")
_THOUSANDS_DOT = re.compile(r"[+-]?(?:[1-9][0-9]{0,2}(?:\.[0-9]{3})+|[0-9]+)")
_AMBIGUOUS_COMMA = re.compile(r"[+-]?[0-9]{1,3},[0-9]{3}")

# A number with one unit. The number part only has to look like one here: the rules above
# then type it. A trailing unit (`65 %`, `15,6 h`, `20°C`, `3 Std.`, `100 m²`, `12 CHF`,
# `5 €`) is `%`, `‰`, `°`, `°C`, `°F`, a currency sign or one to four letters (ASCII plus
# the micro sign in both its code points) with an optional `²` or `³` and an optional
# abbreviating dot; a leading unit (`€ 5`, `-$ 3,50`, `CHF 1.200`) is a currency sign or
# code, with the number's sign allowed before it. The space between is optional and may
# be a no-break or thin space (U+00A0, U+202F, U+2009), which localised spreadsheets and
# web tables write; a line break or a tab is not a space here.
_NUMBER_PART = r"[+-]?(?:[0-9][0-9.,]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?"
_UNIT_SPACE = r"[^\S\r\n\t]?"
_CURRENCY = r"[€$£]|CHF|EUR|USD|GBP"
_TRAILING_UNIT = re.compile(
    rf"(?P<number>{_NUMBER_PART}){_UNIT_SPACE}(?P<unit>%|‰|°[CF]?|[€$£]|[A-Za-zµμ]{{1,4}}[²³]?\.?)"
)
_LEADING_UNIT = re.compile(rf"(?P<sign>[+-])?(?P<unit>{_CURRENCY}){_UNIT_SPACE}(?P<number>{_NUMBER_PART})")

# Letters after a number that are no unit: a month (`5 Jan` is a date fragment), a boolean,
# a missing-value token, an ordinal suffix (`1st`) or a meridiem (`5 pm`). Compared without
# case and without the abbreviating dot; such a column stays text.
_UNIT_STOP_WORDS: frozenset[str] = frozenset(
    word.casefold()
    for word in (
        *("Jan", "Feb", "Mar", "Apr", "May", "Mai", "Jun", "June", "Juni", "Jul", "July", "Juli"),
        *("Aug", "Sep", "Sept", "Oct", "Okt", "Nov", "Dec", "Dez"),
        *("true", "false", "st", "nd", "rd", "th", "am", "pm"),
        *MISSING_VALUES,
    )
)

# The tokens of a header, for whether it already names a unit (`Anteil (%)`, `Preis in €`).
_HEADER_TOKENS = re.compile(r"[^\s()\[\]{},;:]+")

# Text that is a literal: an optional Python assignment, then `[`, `{` or `(`.
_LITERAL_START = re.compile(r"(?:[^\W\d]\w*\s*=\s*)?(?=[\[{(])")

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
AMBIGUOUS_DATE_ORDER = "day and month order is ambiguous; read as DD/MM/YYYY"
"""The note of a slash date column read day first by guess; `prepare.py` finds those columns by it."""
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
    text_columns: list[str] = field(default_factory=list)
    """The columns kept text by request (`parse_dataset(text_columns=...)`), in column order."""


@dataclass
class _Column:
    """One column on its way from cleaned text to canonical cells; "" is missing in both."""

    name: str
    source: list[str]  # cleaned cells, as pasted
    cells: list[str]  # canonical cells for data.csv, set by the typing step
    invisible: bool = False
    text_only: bool = False  # the `category` column of `json_pairs`: keys are names, never typed
    dtype: ColumnDtype = "text"
    unit: str | None = None  # the unit every cell carried, now part of the name
    bare: list[str] = field(default_factory=list)  # the cells the number typing read: `source`, or the number parts
    numbers: list[float] = field(default_factory=list)
    dates: list[datetime] = field(default_factory=list)
    with_time: bool = False
    decimal_comma: bool = False
    notes: list[str] = field(default_factory=list)


def pandas_dtypes(column_dtypes: Mapping[str, ColumnDtype]) -> dict[str, str]:
    """The loader's `dtype=` mapping: every column except the datetime ones, which `parse_dates` takes."""
    return {name: PANDAS_DTYPES[dtype] for name, dtype in column_dtypes.items() if dtype != "datetime"}


def parse_dataset(text: str, *, text_columns: Collection[str] = ()) -> ParsedDataset:
    """Parse pasted CSV, TSV, semicolon or pipe text, JSON or a Python literal into the canonical dataset.

    `text_columns` names (canonical) columns that stay text instead of being typed by
    their cells; a name that is no column is ignored.
    """
    _check_size(text)
    text = text.removeprefix(_BOM)
    _check_controls(text)
    text = unicodedata.normalize("NFC", text)
    stripped = text.strip()
    if not stripped:
        raise ParseError("unparseable", "the data is empty")

    warnings: list[str] = []
    table: tuple[list[str], list[list[str]], SourceFormat] | None = None
    literal = _LITERAL_START.match(stripped)
    if literal:
        assignment, body = literal.group(), stripped[literal.end() :]
        table = _read_literal(body, warnings)
        if table is None and (assignment or not body.startswith("(")):
            raise ParseError("unparseable", "the data starts like JSON or a Python literal but is neither")
        # A bare `(` that neither reader accepts is delimited text: `(in %) Land;Wert`, prose in parentheses.
    if table is None:
        table = _read_delimited(text, warnings)
    headers, rows, source_format = table
    return _build(headers, rows, source_format, warnings, frozenset(text_columns))


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


def _read_literal(text: str, warnings: list[str]) -> tuple[list[str], list[list[str]], SourceFormat] | None:
    """JSON, or a Python literal when the JSON reader refuses the text, tabulated alike; None when it is neither."""
    if _too_deep(text):
        raise ParseError("unparseable", f"the data is nested more than {MAX_NESTING} levels deep")
    decoded = _decode_literal(text)
    if decoded is None:
        return None
    data, repeated = decoded
    if repeated:
        warnings.append(f"{_count(repeated, 'key')} repeated; only the last value of a repeated key is kept")
    return _tabulate(data, warnings)


def _too_deep(text: str) -> bool:
    """Whether the brackets open more than `MAX_NESTING` levels, counted over Python's tokens.

    `tokenize` reads the text the way `ast.literal_eval` will (strings with any quoting,
    triple quotes and prefixes included, comments, line continuations), without
    evaluating or nesting anything, so a bracket inside a string or a comment never
    counts and a string cannot hide real nesting (a closer never takes the count below
    zero). JSON tokenizes the same way. Text the tokenizer refuses (an unclosed string,
    a stray character) is left to the readers, which refuse it on their own terms behind
    their `RecursionError` guard.
    """
    depth = 0
    try:
        for token in tokenize.generate_tokens(io.StringIO(text).readline):
            if token.type != tokenize.OP:
                continue
            if token.string in ("[", "{", "("):
                depth += 1
                if depth > MAX_NESTING:
                    return True
            elif token.string in ("]", "}", ")") and depth:
                depth -= 1
    except (tokenize.TokenError, SyntaxError, ValueError):
        return False
    return False


def _decode_literal(text: str) -> tuple[Any, int] | None:
    """The decoded value and the number of repeated object keys; None when neither reader accepts the text.

    `json.loads` first, then `ast.literal_eval`, which evaluates literals only: a name
    or a call is a ValueError, never run. Both keep the last value of a repeated key,
    so the count lets the caller say that rows went missing.
    """
    repeated = 0

    def objects(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        nonlocal repeated
        repeated += len(pairs) - len({key for key, _ in pairs})
        return dict(pairs)

    try:
        return json.loads(text, parse_constant=lambda _: None, object_pairs_hook=objects), repeated
    except (ValueError, RecursionError):
        pass
    try:
        tree = ast.parse(text, mode="eval")
        value = ast.literal_eval(tree)
    except (ValueError, SyntaxError, TypeError, RecursionError, MemoryError):
        return None
    return value, _repeated_keys(tree)


def _repeated_keys(tree: ast.AST) -> int:
    """How many dict keys of an evaluated literal repeat an earlier key of the same dict."""
    repeated = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            keys = [ast.literal_eval(key) for key in node.keys if key is not None]
            repeated += len(keys) - len(set(keys))
    return repeated


def _tabulate(data: Any, warnings: list[str]) -> tuple[list[str], list[list[str]], SourceFormat]:
    """Headers and rows from the decoded value; a tuple counts as a list."""
    if isinstance(data, (list, tuple)):
        if not data:
            raise ParseError("unparseable", "the array is empty")
        if len(data) > MAX_ROWS:
            raise ParseError("too_many_rows", f"the data has more than {MAX_ROWS:,} rows")
        if all(isinstance(record, dict) for record in data):
            return _records(data, warnings)
        if all(isinstance(pair, (list, tuple)) and len(pair) == 2 for pair in data):
            return _pairs(data)
        raise ParseError("unparseable", "an array must hold objects, one per row, or [category, value] pairs")

    if isinstance(data, dict):
        if not data:
            raise ParseError("unparseable", "the object is empty")
        if all(isinstance(values, (list, tuple)) for values in data.values()):
            return _column_lists(data)
        if all(_scalar(value) for value in data.values()):
            if len(data) > MAX_ROWS:
                raise ParseError("too_many_rows", f"the data has more than {MAX_ROWS:,} rows")
            return _pairs(data.items())
        raise ParseError(
            "unparseable", "an object must map every name to a list of values, or every category to one value"
        )

    raise ParseError(
        "unparseable", "the data must be an array of records or pairs, or an object of column lists or values"
    )


def _records(
    records: Sequence[Mapping[Any, Any]], warnings: list[str]
) -> tuple[list[str], list[list[str]], SourceFormat]:
    keys: dict[Any, int] = {}
    for record in records:
        for key in record:
            if key not in keys:
                keys[key] = len(keys)
                if len(keys) > MAX_COLUMNS:
                    raise ParseError("too_many_columns", f"the data has more than {MAX_COLUMNS} columns")
    headers = [_json_key(key, position) for key, position in keys.items()]
    rows: list[list[str]] = []
    incomplete = 0
    for record in records:
        if len(record) < len(keys):
            incomplete += 1
        rows.append([_json_cell(record[key], position) if key in record else "" for key, position in keys.items()])
    if incomplete:
        verb = "lacks" if incomplete == 1 else "lack"
        warnings.append(f"{_count(incomplete, 'record')} {verb} some keys; those cells are empty")
    return headers, rows, "json_records"


def _column_lists(data: Mapping[Any, Sequence[Any]]) -> tuple[list[str], list[list[str]], SourceFormat]:
    if len(data) > MAX_COLUMNS:
        raise ParseError("too_many_columns", f"the data has {len(data)} columns; at most {MAX_COLUMNS} are supported")
    lengths = {len(values) for values in data.values()}
    if len(lengths) != 1:
        raise ParseError("unparseable", "the column lists have different lengths")
    if lengths.pop() > MAX_ROWS:
        raise ParseError("too_many_rows", f"the data has more than {MAX_ROWS:,} rows")
    headers = [_json_key(key, position) for position, key in enumerate(data)]
    columns = [[_json_cell(value, position) for value in values] for position, values in enumerate(data.values())]
    return headers, [list(row) for row in zip(*columns, strict=True)], "json_columns"


def _pairs(pairs: Iterable[Sequence[Any]]) -> tuple[list[str], list[list[str]], SourceFormat]:
    """`category` and `value` from an object's items or an array's two-element entries, in order."""
    rows = [[_json_cell(pair[0], 0), _json_cell(pair[1], 1)] for pair in pairs]
    return list(PAIR_HEADERS), rows, "json_pairs"


def _scalar(value: object) -> bool:
    return value is None or isinstance(value, (str, int, float))  # a bool is an int


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


def _json_key(key: object, position: int) -> str:
    """A column name: JSON keys are text, a Python literal's may be numbers too."""
    if isinstance(key, str):
        return _json_text(key, f"the name of column {position + 1}")
    if isinstance(key, (int, float)):
        return _json_cell(key, position)
    raise ParseError("unparseable", f"the name of column {position + 1} is not text")


def _json_cell(value: object, position: int) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value) if math.isfinite(value) else ""
    if isinstance(value, str):
        return _json_text(value, f"a value in column {position + 1}")
    raise ParseError(
        "unparseable", f"column {position + 1} holds nested values; only text, numbers, booleans and null are supported"
    )


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


def _clean_key(raw: str) -> tuple[str, bool]:
    """A pair key (`json_pairs` category) is a name: cleaned like a cell, but `NA` or `null` stays text."""
    text, invisible = _strip_invisible(raw)
    return text.replace("\r\n", "\n").replace("\r", "\n").strip(), invisible


def canonical_names(headers: Sequence[str]) -> list[str]:
    """The column names `parse_dataset` gives these raw headers when no cell carries a unit.

    The same cleaning and canonicalisation as the parse (`_clean_header`, then
    `canonical_headers`), for a caller that writes a CSV and must name its columns as
    the re-parse will: `prepare.py` keeps `text_columns` by those names.
    """
    return canonical_headers([_clean_header(raw)[0] for raw in headers])[0]


def _clean_header(raw: str) -> tuple[str, bool, bool]:
    """The header text, whether invisible characters went, and whether tabs or line breaks became spaces."""
    text, invisible = _strip_invisible(raw)
    text = text.strip()
    spaced = _HEADER_BREAKS.sub(" ", text)
    return spaced, invisible, spaced != text


def canonical_headers(headers: Sequence[str], units: Sequence[str | None] | None = None) -> tuple[list[str], list[str]]:
    """Canonical column names and one warning per rename.

    The input is the cleaned header text (NFC, invisible characters removed, tabs and
    line breaks turned into spaces, surrounding whitespace stripped), and optionally
    the unit each column's values carried (None for none). An empty name becomes
    `column_N` (N is the 1-based position); a unit is appended as ` (<unit>)`; a name
    over 64 characters is cut to 64, the unit suffix kept whole; a repeated name gets
    `_2`, `_3`, ... (the first occurrence keeps it), cut so the suffixed name still
    fits in 64 characters. Names compare case-sensitively, as pandas does.
    """
    names: list[str] = []
    warnings: list[str] = []
    used: set[str] = set()
    for position, header in enumerate(headers, start=1):
        name = header
        unit = units[position - 1] if units else None
        unit_suffix = f" ({unit})" if unit else ""
        if not name:
            name = f"column_{position}"
            warnings.append(f"column {position}: empty header named '{name}'")
        elif len(name) > MAX_COLUMN_NAME_CHARS:
            name = name[: MAX_COLUMN_NAME_CHARS - len(unit_suffix)].rstrip()
            warnings.append(
                f"column {position}: header longer than {MAX_COLUMN_NAME_CHARS} characters "
                f"shortened to '{name}{unit_suffix}'"
            )
        elif len(name) + len(unit_suffix) > MAX_COLUMN_NAME_CHARS:
            name = name[: MAX_COLUMN_NAME_CHARS - len(unit_suffix)].rstrip()
            warnings.append(
                f"column {position}: header shortened to '{name}{unit_suffix}' "
                f"so the unit fits within {MAX_COLUMN_NAME_CHARS} characters"
            )
        name += unit_suffix
        if name in used:
            # The duplicate suffix goes before the unit suffix, so `_2` never cuts into ` (%)`.
            base, suffix = name, 2
            stem = name[: len(name) - len(unit_suffix)]
            while name in used:
                tail = f"_{suffix}"
                room = MAX_COLUMN_NAME_CHARS - len(tail) - len(unit_suffix)
                name = stem[:room].rstrip() + tail + unit_suffix
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
    5. **integer or number with a unit**: every cell is a number next to one unit
       that all cells share (`65 %`, `15,6 h`, `€ 5`, see `_split_units`), and the
       number parts pass rules 3 and 4 (so `007 kg` keeps its text). The cells keep
       the number; the unit goes into the column name, see `canonical_headers`.
    6. **text**: everything else, every column without a non-missing cell, and the
       `category` column of `json_pairs`, whose cells are the keys (`text_only`).
    """
    column.cells = list(column.source)
    column.bare = column.source
    present = [cell for cell in column.source if cell]
    if not present or column.text_only:
        return
    if _as_dates(column, present):
        return
    if all(cell.casefold() in ("true", "false") for cell in present):
        column.dtype = "boolean"
        column.cells = [("True" if cell.casefold() == "true" else "False") if cell else "" for cell in column.source]
        return
    if _as_plain_numbers(column, column.source, present):
        return
    split = _split_units(present)
    if split is None:
        return
    unit, numbers = split
    bare = [numbers[cell] if cell else "" for cell in column.source]
    if _as_plain_numbers(column, bare, [numbers[cell] for cell in present]):
        column.unit = unit
        column.bare = bare


def _as_plain_numbers(column: _Column, cells: list[str], present: list[str]) -> bool:
    """Rules 3 and 4 of `_type_column` on `cells` (`present` is its non-missing cells); False leaves text."""
    if all(_INTEGER.fullmatch(cell) for cell in present):
        if any(_LEADING_ZERO.fullmatch(cell) for cell in present):
            column.notes.append("numbers with leading zeros kept as text")
            return False
        if _as_integers(column, cells):
            return True
    if all(_FLOAT.fullmatch(cell) for cell in present):
        return _as_numbers(column, cells)
    if all(_DECIMAL_COMMA.fullmatch(cell) for cell in present) and any("," in cell for cell in present):
        if _as_numbers(column, [cell.replace(".", "").replace(",", ".") for cell in cells]):
            column.decimal_comma = True
            commas = [cell for cell in present if "," in cell]
            if all(_AMBIGUOUS_COMMA.fullmatch(cell) for cell in commas) and not any("." in cell for cell in present):
                column.notes.append("commas read as decimal commas; remove them first if they separate thousands")
            return True
    return False


def _split_units(present: list[str]) -> tuple[str, dict[str, str]] | None:
    """The one unit every cell carries and each distinct cell's number part; None when they differ.

    A unit is read exactly (`kg` and `Kg` differ); the same unit before and after the
    number is one unit. A sign before a leading currency belongs to the number (`-€ 5`
    is -5), and a cell with a sign in both places is no number. Letters that are a
    month, a boolean, a missing-value token, an ordinal suffix or a meridiem are no
    unit (`_UNIT_STOP_WORDS`): `5 Jan` and `1st` keep their text.
    """
    unit: str | None = None
    numbers: dict[str, str] = {}
    for cell in present:
        if cell in numbers:
            continue
        split = _split_unit(cell)
        if split is None or (unit is not None and split[1] != unit):
            return None
        numbers[cell], unit = split
    return None if unit is None else (unit, numbers)


def _split_unit(cell: str) -> tuple[str, str] | None:
    match = _TRAILING_UNIT.fullmatch(cell)
    if match:
        unit = match["unit"]
        if unit.rstrip(".").casefold() in _UNIT_STOP_WORDS:
            return None
        return match["number"], unit
    match = _LEADING_UNIT.fullmatch(cell)
    if match is None:
        return None
    sign, number = match["sign"] or "", match["number"]
    if sign and number[0] in "+-":
        return None
    return sign + number, match["unit"]


def _retype_thousands_dots(column: _Column) -> None:
    """In a file with decimal commas, a dot-number column of `1.234` shapes holds thousands separators."""
    present = [cell for cell in column.bare if cell]
    if not (all(_THOUSANDS_DOT.fullmatch(cell) for cell in present) and any("." in cell for cell in present)):
        return
    cells = [cell.replace(".", "") for cell in column.bare]
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
            column.notes.append(AMBIGUOUS_DATE_ORDER)

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
    raw_headers: list[str],
    raw_rows: list[list[str]],
    source_format: SourceFormat,
    warnings: list[str],
    text_columns: frozenset[str] = frozenset(),
) -> ParsedDataset:
    headers: list[str] = []
    columns: list[_Column] = []
    renamed_by_breaks: list[int] = []
    for position, raw in enumerate(raw_headers):
        header, invisible, broken = _clean_header(raw)
        text_only = source_format == "json_pairs" and position == 0  # the keys of an object are names
        cells: list[str] = []
        for row in raw_rows:
            cell, cell_invisible = (_clean_key if text_only else _clean_cell)(row[position])
            cells.append(cell)
            invisible = invisible or cell_invisible
        if not header and not any(cells):
            continue
        if broken:
            renamed_by_breaks.append(len(headers))
        headers.append(header)
        columns.append(_Column(name="", source=cells, cells=[], invisible=invisible, text_only=text_only))

    dropped = len(raw_headers) - len(headers)
    if dropped:
        warnings.append(f"{_count(dropped, 'empty column')} without a header dropped")
    if not columns:
        raise ParseError("no_table", "the data has no columns")
    if len(columns) > MAX_COLUMNS:
        raise ParseError(
            "too_many_columns", f"the data has {len(columns)} columns; at most {MAX_COLUMNS} are supported"
        )
    if not raw_rows:
        raise ParseError("no_table", "the data has a header but no rows")
    # The length checks come before typing: `int()` on a cell of thousands of digits raises
    # a ValueError of its own, which this limit exists to keep from the route.
    for position, (header, column) in enumerate(zip(headers, columns, strict=True), start=1):
        if len(header) > MAX_INPUT_CELL_CHARS:
            raise ParseError(
                "cell_too_long", f"the header of column {position} has more than {MAX_INPUT_CELL_CHARS} characters"
            )
        if any(len(cell) > MAX_INPUT_CELL_CHARS for cell in column.source):
            named = _clip(header, MAX_COLUMN_NAME_CHARS) if header else f"column_{position}"
            raise ParseError(
                "cell_too_long", f"a cell in column '{named}' has more than {MAX_INPUT_CELL_CHARS} characters"
            )

    # Typing comes before naming: a column whose cells carried a unit is named after it. A
    # column kept text by request is found by its name without a unit: it gets none, since it
    # is never typed, and the only text that carries such a request is the canonical CSV of an
    # earlier version, whose headers are unique already, so that name is its final name.
    plain_names, _ = canonical_headers(headers) if text_columns else ([], [])
    for index, column in enumerate(columns):
        if text_columns and plain_names[index] in text_columns:
            column.cells = list(column.source)  # kept text by request: the cells as cleaned, never typed
        else:
            _type_column(column)
    if any(column.decimal_comma for column in columns):
        for column in columns:
            if column.dtype == "number" and not column.decimal_comma:
                _retype_thousands_dots(column)

    # A header that already names the unit (`Anteil (%)`, `Preis in €`) gets no suffix, unless it is
    # longer than a name may be: then the suffix is passed so the cut keeps the unit at the end.
    carried = [
        bool(column.unit) and column.unit in _HEADER_TOKENS.findall(header)
        for header, column in zip(headers, columns, strict=True)
    ]
    units = [
        column.unit if column.unit and (not carries or len(header) > MAX_COLUMN_NAME_CHARS) else None
        for header, column, carries in zip(headers, columns, carried, strict=True)
    ]
    names, header_warnings = canonical_headers(headers, units)
    for index in renamed_by_breaks:
        warnings.append(f"column '{names[index]}': tabs or line breaks in the header replaced with spaces")
    warnings.extend(header_warnings)
    if all(_looks_like_value(name) for name in names):
        warnings.append("every header looks like a value; the first row may be data rather than column names")

    for position, (header, name, carries, column) in enumerate(
        zip(headers, names, carried, columns, strict=True), start=1
    ):
        column.name = name
        if column.invisible:
            warnings.append(f"column '{name}': invisible formatting characters (zero-width or bidi) removed")
        if column.unit and carries:
            warnings.append(
                f"column '{name}': unit '{column.unit}' removed from the values; the name already carries it"
            )
        elif column.unit:
            before = header or f"column_{position}"
            warnings.append(f"column '{before}': unit '{column.unit}' moved from the values into the name '{name}'")
        warnings.extend(f"column '{name}': {note}" for note in column.notes)

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
        text_columns=[column.name for column in columns if column.name in text_columns],
    )


def _profile_column(column: _Column) -> ColumnProfile:
    present = [cell for cell in column.cells if cell]
    minimum: float | str | None = None
    maximum: float | str | None = None
    mean: float | None = None
    median: float | None = None
    top: list[str] = []
    if column.dtype in ("integer", "number") and column.numbers:
        minimum, maximum = min(column.numbers), max(column.numbers)
        mean, median = _statistics(column.numbers)
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
        mean=mean,
        median=median,
        top=top,
    )


def _statistics(numbers: Sequence[float]) -> tuple[float | None, float | None]:
    """The mean and the median at six significant digits; None for one that no float holds.

    `fsum` of two `1e308` values raises `OverflowError`, and the sum of the two middle
    values can be infinite, so each is computed within the float range or left out
    rather than failing the parse of a dataset whose values are all finite.
    """
    try:
        mean: float | None = statistics.fmean(numbers)
    except OverflowError:
        mean = None
    ordered = sorted(numbers)
    middle = len(ordered) // 2
    median = ordered[middle] if len(ordered) % 2 else ordered[middle - 1] / 2 + ordered[middle] / 2
    return (
        _rounded(mean) if mean is not None and math.isfinite(mean) else None,
        _rounded(median) if math.isfinite(median) else None,
    )


def _rounded(value: float) -> float:
    """A statistic at six significant digits, so a mean never carries float noise into the profile."""
    return float(f"{value:.6g}")


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


def display_copy(cell: str) -> str:
    """The copy of a cell the profile shows (sample rows and top values): one line, at most 40 characters."""
    return _clip(cell)


def _cap_warnings(warnings: list[str]) -> list[str]:
    """At most `MAX_WARNINGS`, the last slot noting how many were left out; each within `MAX_NOTE_CHARS`."""
    notes = [_clip(warning, MAX_NOTE_CHARS) for warning in warnings]
    if len(notes) <= MAX_WARNINGS:
        return notes
    kept = notes[: MAX_WARNINGS - 1]
    return [*kept, f"{len(notes) - len(kept)} more warnings omitted"]


def _count(number: int, noun: str) -> str:
    return f"{number} {noun}" if number == 1 else f"{number} {noun}s"
