"""Deterministic parse of pasted data into a canonical `data.csv` and a `DatasetProfile`.

The design is docs/concepts/agent-network.md, "Parse". The module imports neither
ADK nor pandas: it reads with `csv`, `json` and explicit regular expressions, so
every typing rule is written here instead of left to pandas' inference (which
would, for example, read `01.02.2024` as a number under `thousands='.'`).

`parse_dataset` runs these steps in order:

1. **Limits on the raw text.** At most `MAX_INPUT_BYTES` (1 MiB) of UTF-8, or
   `MAX_COMPUTED_BYTES` (2 MiB) for a table the service computed (`too_long`; the
   canonical CSV the parse writes is checked against `MAX_CANONICAL_BYTES` too); no control character other than tab, line feed and carriage
   return (`control_chars`: every Unicode `Cc` character, which is C0, DEL and C1).
2. **Normalise.** Strip a leading BOM and apply NFC, with one warning that counts the
   lines NFC changed (a decomposed `e` and accent became `é`: the text reads the same).
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
   pasted order; the keys stay text, the values are typed); `null`, `NaN` and
   `Infinity` are missing; a float keeps the text it was written with (`_SourceFloat`),
   so the typing sees every digit; a key repeated in an object keeps its last value, with
   a warning. Since 2026-10-15 a record's nested objects become columns named with
   dots (`country.value`), down to `MAX_FLATTEN_DEPTH` levels (`_flatten`), and a field
   that holds a list of values expands to one row per value (`_records`); the records
   may come wrapped with metadata as an API answers them, `[{page metadata}, [records]]`
   (the World Bank) or `{"data": [records], "meta": {...}}`, whose other fields become
   notes (`_api_records`), or as a schema with rows of cells (`_schema_rows`). A JSON-stat 2.0 dataset (`json_stat`,
   since 2026-10-14: what the statistics offices' APIs return, BFS PxWeb,
   Eurostat, Statistik Austria, Statistics Norway), or a JSON-stat 1.x bundle
   of one dataset, is the one shape nested deeper than 2 (dimension, category,
   index: about five levels): it is checked strictly and flattened into a long
   table, one column per dimension with more than one category (named by its
   label, the category labels as cells, kept text), then `value`, in the order of
   `value`; see `_json_stat`. Its one-category dimensions, label, source and
   notes become `context_lines`. The `MAX_NESTING` bracket count below applies
   to it as to everything else. Text that starts with a bare `(` and is
   neither JSON nor a Python literal (a header such as `(in %) Land`, or prose
   in parentheses) is delimited text instead, like everything that starts
   otherwise, see `sniff_delimiter`.
   Fully blank lines (also `;;;`-style lines of empty fields) are skipped. Delimited
   text is first narrowed to its table (`table_block`, since 2026-10-14): a title, an
   export's metadata or a note above the header, a source line or a note below the
   last row, and up to three summary rows (`Total`, `Summe`, `Mittelwert`…) at the end
   are left out, each kind with one warning. A row with fewer fields than the header
   is padded with missing cells (one warning); a row with more non-empty fields than
   the header is `unparseable`. The lines left out above and below the table (not the
   summary rows, which are data) are kept as `ParsedDataset.context_lines`, the notes
   the user pasted with the data, see `_context_lines` (owner rule of 2026-10-14).
   Text that holds two or more tables, each under its own header after a blank line (a
   report sheet; live test round 5 of 2026-10-15), is narrowed to one of them first, the
   first unless `table` names another, with a warning naming the others and a label per
   table in `ParsedDataset.tables` (`_one_table`).
   Since 2026-10-15 a table aligned with runs of two or more spaces (a weather or
   statistics office's `.txt`), or a table of numbers separated by single spaces, is read
   too when no real delimiter finds a table (`whitespace`, see `sniff_delimiter` and
   `_space_block`), a short row of a fixed-width layout placed by position (`_aligned`);
   a line that declares the missing-value mark (`Missing values: -999`) makes that mark
   missing in number and date columns (`_declared_missing`, `_blank_marks`).
4. **Clean every cell.** Remove invisible format characters (Unicode category
   `Cf`: zero-width characters, bidi controls, BOMs inside the text, tag
   characters), turn line and paragraph separators (U+2028, U+2029) into spaces,
   turn CRLF and CR inside a quoted cell into LF, strip surrounding whitespace,
   and map `MISSING_VALUES` to an empty cell. One warning per column that lost
   invisible characters; in a column that stays text, one warning counts the cells
   whose surrounding whitespace went (not in a space-aligned table, whose padding is
   layout); in every column one warning counts the cells read as missing, naming the
   tokens (`NA`, `None`, `-`; until live test round 5 of 2026-10-15 only a text column
   said so, `_fidelity_notes`). A cell (header or value) longer than
   `MAX_INPUT_CELL_CHARS` after cleaning is `cell_too_long`, checked before any
   typing reads the cell. A column without a header whose cells are all missing
   (the trailing-delimiter column of many spreadsheet exports) is dropped with a
   warning before the 50-column check. So is a pasted column with a header whose cells
   are all missing (an API export's unused schema fields), with one warning naming them,
   unless every column is empty (`_without_empty_columns`, since 2026-10-15; a canonical
   re-parse keeps it). So is a first column of row names that only number the rows (R's
   `write.csv`, pandas' `to_csv`: an empty header and `1` to `n`), with a warning that
   counts its cells (`_without_row_names`, live test round 5 of 2026-10-15).
5. **Type each column**, see `_type_column`: dates, then booleans, integers,
   numbers (also with unambiguous thousands groups: `7.184.003`, `1'234'567`,
   `1 234,5`, `1,234,567`, see `_as_grouped_numbers`; a column of `1,234` shapes reads
   as comma thousands only beside a comma-grouped column, `_commas_as_thousands`), then the
   same numbers behind one unit shared by every cell (`65 %`, `15,6 h`, `€ 5`, also
   with a no-break space; the unit leaves the cells), otherwise text. A whole number
   written without a fraction in a number column keeps that form (`87000` beside
   `120500.5`, `number_text`; live test round 5 of 2026-10-15).
6. **Canonicalise the headers**, see `canonical_headers`. A column whose cells
   carried a unit is named `<name> (<unit>)` there, so the duplicate suffixes and
   the 64-character cap cover the new name too (one warning per such column); a
   header that already names the unit (`Anteil (%)`, `Preis in €`) keeps its name.
7. **Constant text columns move to the notes** (since 2026-10-14, `_constants_to_notes`):
   a pasted text column with the same value in every row (`Kanton` = `Schweiz`) leaves
   the table and `<name>: <value>` joins `context_lines`, as a JSON-stat dimension of one
   category does, unless fewer than `MIN_KEPT_COLUMNS` columns would remain.
8. **Write the canonical `data.csv`** (comma, dot decimal, ISO dates, canonical
   headers, missing as an empty cell, `\\n` line ends) and profile it. The profile
   names the months of a text column of month names (`ColumnProfile.months`) and, for
   JSON records whose list fields expanded into rows, the columns that came from those
   lists (`DatasetProfile.list_columns`; live test round 4 of 2026-10-15).

The loader reads the result with
`pd.read_csv("data.csv", dtype=pandas_dtypes(column_dtypes), parse_dates=parse_dates)`,
plus per-column `na_values` with `keep_default_na=False` when a column is text
(`code/loader.py`), and gets the typed frame back: in a text column only the empty cell
is missing. `data.csv` can hold a text cell that pandas would read as missing by
default: a `json_pairs` key or a JSON-stat category such as `NA` (Namibia), a pasted `NA`
in a column of letter codes (`_keep_na_codes`), and any text cell of a canonical re-parse
(`parse_dataset(canonical=True)`). Every other pasted token of `MISSING_VALUES` is an
empty cell already.

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
import sys
import tokenize
import unicodedata
from collections import Counter
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from itertools import pairwise, product
from typing import Any, Literal

from ..schemas import (
    MAX_CELL_CHARS,
    MAX_COLUMN_NAME_CHARS,
    MAX_COLUMNS,
    MAX_MESSAGE_CHARS,
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
from .months import named_months


MAX_INPUT_BYTES = 1024 * 1024
"""The paste cap, "1 MB": 1,048,576 UTF-8 bytes (owner decision of 2026-10-14; 200 KB before). Measured on a
914,795-byte paste of 19,999 rows and six columns: the parse takes 0.5 s, the pre-filter over every cell 0.22 s,
and the dataset judge still reads one part, because it sees the headers and a sample, never every row."""
MAX_COMPUTED_BYTES = 2 * 1024 * 1024
"""The cap of a table the service computed itself (`run_data_code`, `generate_data`, `prepare_data`), which
re-parses pass as `max_bytes` (owner decision of 2026-10-14). A float at full precision takes 16 to 19 bytes: a
10,000-step ODE with `t, x, y, z` was 637,727 bytes, and 10,001 rows of six normal floats 1,138,766 bytes, over
the paste cap. Writing fewer significant digits would fit them under it, but it is lossy for large values that
differ only in their decimals, so computed data keeps full precision under its own cap: 2 MiB holds 10,001 rows of
about ten float columns. Rows and columns keep their caps (`MAX_ROWS`, `MAX_COLUMNS`)."""
MAX_CANONICAL_BYTES = 4 * 1024 * 1024
"""The canonical `data.csv` a parse may produce, also the render job's `data_csv` cap (`renderer/wire.py`
`MAX_DATA_CSV_CHARS`, pinned equal by a test): ISO dates and dot decimals can grow a paste, so the size is checked
after the parse rather than assumed (`too_long`)."""
MAX_INPUT_CELL_CHARS = 200  # per header or cell, after cleaning; the profile's own cells stop at MAX_CELL_CHARS
PREVIEW_ROWS = 20
SNIFF_LINES = 50  # enough to see a table below an export's metadata or a few lines of notes
VALUE_SHARE = 0.5
"""The share of filled cells that must read as values in a value column (`table_block`). Half, not a
large majority: in a short table, the header and a note split into the table's width at its commas
weigh as much as the few data rows."""
MAX_SUMMARY_ROWS = 3  # summary rows at the end of a table that `table_block` leaves out
SUMMARY_LABELS: frozenset[str] = frozenset(
    {
        *("total", "totals", "grand total", "subtotal", "sum", "sum total", "average", "avg", "mean"),
        *("median", "min", "max", "minimum", "maximum", "count", "std", "std dev", "result"),
        *("summe", "gesamt", "gesamtsumme", "insgesamt", "zwischensumme", "durchschnitt", "mittel"),
        *("mittelwert", "anzahl", "ergebnis"),
    }
)
"""The first filled cell of a summary row, compared without case and without a trailing colon."""
MAX_CONTEXT_CHARS = MAX_MESSAGE_CHARS
"""The notes kept around a table (`context_lines`), all lines and their line breaks together: they
reach the root as user text, so they get no more room than a chat message."""
CONTEXT_JOINERS: dict[str | None, str] = {",": ", ", ";": "; ", "\t": " ", "|": " | ", None: " "}
"""How the fields of a left-out record join back into one line: a sentence that its commas split
reads as it was pasted, a tab becomes a space so the line stays one line on the page."""
MAX_NESTING = 50  # bracket levels a literal may open; counted before `ast.literal_eval` sees the text
PAIR_HEADERS = ("category", "value")  # the columns of an object of scalars or an array of pairs
NA_TOKEN = "NA"
MIN_OTHER_CODES = 2
"""The distinct letter codes beside `NA` that make a pasted `NA` a code rather than missing (`_keep_na_codes`)."""
MAX_RAW_COLUMNS = 4 * MAX_COLUMNS
"""The keys a JSON table may carry before its empty columns are dropped (`_without_empty_columns`): an API's
records name every field of its schema, also the unused ones, and the cap of `MAX_COLUMNS` applies to the
columns left; this bound keeps the work before that check small. Delimited text is bounded by its size alone."""
MAX_FLATTEN_DEPTH = 3
"""The levels of nested objects a JSON record's fields are read from (`_flatten`): `country.value` is one level,
`a.b.c.d` three. API records nest one level (the World Bank's `country`, `indicator`), rarely two."""
MAX_NAMED_FIELDS = 5  # the left-out fields a warning names before it ends with `…`
MIN_KEPT_COLUMNS = 2
"""The columns a paste keeps at least when constant text columns move to the notes (`_constants_to_notes`):
a category or a time and a value, the least a plot needs."""

# Candidate delimiters in tie-break order, with the source format each one reports.
DELIMITERS: tuple[tuple[str, SourceFormat], ...] = ((",", "csv"), (";", "semicolon"), ("\t", "tsv"), ("|", "pipe"))
SPACE_RUN = "  "
"""The pseudo delimiter of a table aligned with runs of two or more spaces (`_space_block`): a single space
inside a header or a cell (`Max Temp`, `Zürich / Fluntern`) stays part of it."""
SINGLE_SPACE = " "
"""The pseudo delimiter of a table whose fields are separated by single spaces (`x y z`), tried only when the
space-run reading finds no table, and read only for a table of numbers and dates (`_space_block`): a single space
also sits inside a two-word name (`Anna Lee`), which no rule can tell from a separator."""
_SPACE_RUN_FIELD = re.compile(r"[^ ]+(?: [^ ]+)*")  # a field between runs of 2+ spaces; a tab is no separator here
_SPACE_FIELD = re.compile(r"[^ ]+")  # a field between single spaces
MIN_SPACE_ROWS = 2  # the data rows a space-separated table needs at least: one aligned line is no table
_QUOTED = re.compile(r"\"([^\"]*)\"|'([^']*)'")  # a whole field in matching quotes, `"New York"`
_YEAR = re.compile(r"1[0-9]{3}|20[0-9]{2}")
MAX_DECLARED_MISSING_CHARS = 12
_MISSING_DECLARATION = re.compile(
    r"(?:missing(?:[ _-]?(?:values?|data|value code))?|no[ _-]?data(?:[ _-]?values?)?|fill[ _-]?values?"
    r"|na[ _-]?values?|fehlwerte?|fehlende werte|valeurs? manquantes?)"
    rf"\s*[:=]\s*(?P<mark>\S{{1,{MAX_DECLARED_MISSING_CHARS}}})",
    re.IGNORECASE,
)
"""A note line that declares the file's missing-value mark (`Missing values: NA`, `nodata = -999`)."""
_DECLARED_MARK = re.compile(r"[+-]?[0-9]+(?:[.,][0-9]+)?|[^\w\s]{1,3}|[A-Za-z]{1,3}")
_MARK_NUMBER = re.compile(r"[+-]?[0-9]+(?:[.,][0-9]+)?")
MIN_SENTINEL = 999  # a positive missing-value number this large or larger reads as a sentinel (`9999`), never `1`
_NOT_A_MARK: frozenset[str] = frozenset({"no", "yes", "ja", "nein", "non", "oui", "si"})
"""Words after `Missing values:` that answer whether values are missing, not which mark stands for them."""

# A cell is missing when, after cleaning, it is exactly one of these. The set is the
# design's list (empty, `NA`, `NaN`, `null`, `-`) plus every other token pandas reads as
# missing by default (`pandas._libs.parsers.STR_NA_VALUES`): a pasted token that pandas reads as
# missing is missing in the profile too. The few text cells that keep such a token (`NA` as a
# code, see the module docstring) survive the loader through `keep_default_na=False`.
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
_OMITTED = re.compile(r"([0-9]+) more warnings omitted")  # the last line of a capped list (`_cap_warnings`)

# ASCII digits only: `\d` and `int()` also accept other scripts' digits, which pandas does not.
_INTEGER = re.compile(r"[+-]?[0-9]+")
_LEADING_ZERO = re.compile(r"[+-]?0[0-9]+")
_FLOAT = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")
# A thousands-grouped number never starts with a zero group: `0.125` is a dot decimal.
_DECIMAL_COMMA = re.compile(r"[+-]?(?:[1-9][0-9]{0,2}(?:\.[0-9]{3})+|[0-9]+)(?:,[0-9]+)?")
_THOUSANDS_DOT = re.compile(r"[+-]?(?:[1-9][0-9]{0,2}(?:\.[0-9]{3})+|[0-9]+)")
_AMBIGUOUS_COMMA = re.compile(r"[+-]?[0-9]{1,3},[0-9]{3}")
# A cell that is a whole number or `1,234` (a comma before one group of three digits): beside a column whose
# commas group thousands unambiguously, the comma groups thousands here too (`_commas_as_thousands`).
_COMMA_GROUP = re.compile(r"[+-]?(?:[1-9][0-9]{0,2},[0-9]{3}|0|[1-9][0-9]*)")
# The thousands separators `_as_grouped_numbers` reads, and what its notes call them. A space-like mark
# (space, no-break, narrow no-break, thin space) or an apostrophe never separates decimals, so one group
# already says thousands; a dot or a comma does, so it needs two groups or the other mark as the decimal.
GROUP_MARKS: dict[str, str] = {
    ".": "dots",
    ",": "commas",
    "'": "apostrophes",
    "\N{RIGHT SINGLE QUOTATION MARK}": "apostrophes",
    " ": "spaces",
    "\N{NO-BREAK SPACE}": "spaces",
    "\N{NARROW NO-BREAK SPACE}": "spaces",
    "\N{THIN SPACE}": "spaces",
}
_GROUPED: dict[str, re.Pattern[str]] = {
    mark: re.compile(
        rf"[+-]?(?:[1-9][0-9]{{0,2}}(?:{re.escape(mark)}[0-9]{{3}})+|0|[1-9][0-9]*)(?:(?P<decimal>[.,])[0-9]+)?"
    )
    for mark in GROUP_MARKS
}
_IPV4 = re.compile(r"(?:25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})(?:\.(?:25[0-5]|2[0-4][0-9]|1[0-9]{2})){3}")
"""Four dot groups, each at most 255 (the last three of three digits, as a group needs): an IPv4 address."""
_NAME_WORDS = re.compile(r"[^\W_]+")
ID_WORDS: frozenset[str] = frozenset(
    {
        *("id", "ids", "code", "codes", "version", "ver", "phone", "tel", "telefon", "telephone", "mobile"),
        *("handy", "plz", "zip", "postcode", "postal", "sku", "ip", "iban", "ean", "isbn", "gtin", "nr", "no"),
    }
)
"""Words of a column name that say its cells are ids, codes, versions or phone numbers: their digit groups
(`123 456`, `1.200.300`) are part of the value, so no thousands reading applies (review of 2026-10-15)."""
_LETTER_CODE = re.compile(r"[A-Z]{2,3}")  # a country, region or currency code (`CH`, `EU`, `USA`)
_INTEGER_INDEX = re.compile(r"0|[1-9][0-9]{0,8}")  # a position key of a sparse JSON-stat `value` object

# A number with one unit. The number part only has to look like one here: the rules above
# then type it. A trailing unit (`65 %`, `15,6 h`, `20°C`, `3 Std.`, `100 m²`, `12 CHF`,
# `5 €`) is `%`, `‰`, `°`, `°C`, `°F`, a currency sign or one to four letters (ASCII plus
# the micro sign in both its code points) with an optional `²` or `³` and an optional
# abbreviating dot; a leading unit (`€ 5`, `-$ 3,50`, `CHF 1.200`) is a currency sign or
# code, with the number's sign allowed before it. The space between is optional and may
# be a no-break or thin space (U+00A0, U+202F, U+2009), which localised spreadsheets and
# web tables write; a line break or a tab is not a space here.
_NUMBER_PART = r"[+-]?(?:[0-9][0-9.,'’]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?"  # `'` and `’`: Swiss `CHF 1'200`
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

_ISO_STAMP = re.compile(
    r"([0-9]{4})-([0-9]{2})-([0-9]{2})"
    r"(?:[T ]([0-9]{2}):([0-9]{2})(?::([0-9]{2})(?:[.,]([0-9]{1,9}))?)?(Z|[+-][0-9]{2}(?::?[0-9]{2})?)?)?"
)
"""An ISO date, or a timestamp with seconds, a fraction of up to nine digits and an offset (`_as_iso_stamps`)."""

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
    context_lines: list[str] = field(default_factory=list)
    """The lines `find_table` left out above and below the table (a title, an export's metadata, a source
    line, a note), each as one cleaned text line, at most `MAX_CONTEXT_CHARS` in all: the user's notes about
    the data. Summary rows are not among them. Empty for `find_table=False` and for a literal, except a
    JSON-stat dataset, whose label, source, notes and one-category dimensions are its lines (`_json_stat`).
    A pasted text column with the same value in every row adds `<name>: <value>` (`_constants_to_notes`)."""
    tables: list[str] = field(default_factory=list)
    """One label per table (its header names and its row count) when the paste held two or more tables, each
    under its own header after a blank line (`_one_table`); empty for one table. `table` is the one read (1-based)."""
    table: int = 1
    with_constants: "ParsedDataset | None" = field(default=None, repr=False, compare=False)
    """The same table with its constant columns still in it, when `_constants_to_notes` moved any: the notes
    carry their values only while the notes are kept, so a path that drops the notes takes this one instead
    (`with_constant_columns`), and the dataset judge reads it."""


def with_constant_columns(parsed: ParsedDataset) -> ParsedDataset:
    """`parsed` with the constant columns that moved to its notes back in the table, and without those notes."""
    return parsed.with_constants if parsed.with_constants is not None else parsed


def without_context(parsed: ParsedDataset, warning: str) -> ParsedDataset:
    """`parsed` without its context lines and with `warning` first among its warnings (profile included).

    The route drops the notes this way when the pre-filter or the scope judge refuses them;
    the table itself is unchanged, except that constant columns whose values had moved into
    the notes are columns again (`with_constant_columns`), so no value is lost with the notes.
    """
    parsed = with_constant_columns(parsed)
    kept = list(parsed.warnings)
    omitted = 0
    if kept and (match := _OMITTED.fullmatch(kept[-1])):
        omitted = int(match.group(1))
        kept.pop()
    lines = [_clip(warning, MAX_NOTE_CHARS), *kept]
    if omitted or len(lines) > MAX_WARNINGS:
        keep = MAX_WARNINGS - 1
        omitted += len(lines) - keep
        lines = [*lines[:keep], f"{omitted} more warnings omitted"]
    warnings = lines
    profile = parsed.profile.model_copy(update={"warnings": warnings})
    return replace(parsed, profile=profile, warnings=warnings, context_lines=[])


@dataclass
class _Column:
    """One column on its way from cleaned text to canonical cells; "" is missing in both."""

    name: str
    source: list[str]  # cleaned cells, as pasted
    cells: list[str]  # canonical cells for data.csv, set by the typing step
    invisible: bool = False
    text_only: bool = False  # `json_pairs` category, `json_stat` dimension: keys are names, never typed
    dtype: ColumnDtype = "text"
    unit: str | None = None  # the unit every cell carried, now part of the name
    bare: list[str] = field(default_factory=list)  # the cells the number typing read: `source`, or the number parts
    numbers: list[float] = field(default_factory=list)
    dates: list[datetime] = field(default_factory=list)
    date_texts: list[str] = field(default_factory=list)  # the canonical text of each of `dates`, for exact min/max
    date_rests: list[int] = field(default_factory=list)  # nanoseconds past each of `dates`' microsecond, for order
    with_time: bool = False
    decimal_comma: bool = False
    notes: list[str] = field(default_factory=list)
    na_rows: list[int] = field(default_factory=list)  # the rows whose cell was `NA`, read as missing so far
    mark_rows: list[int] = field(default_factory=list)  # the rows whose cell is a declared missing-value mark
    id_like: bool = False  # the name says ids, codes, versions or phone numbers (`_id_like`): no thousands reading
    group_mark: str | None = None  # the thousands mark `_as_grouped_numbers` read, evidence for other columns
    integers: list[int] = field(default_factory=list)  # an integer column's values, exact (`numbers` are floats)
    rounded: int = 0  # the cells a number column holds only rounded: more digits than a float64 keeps
    respelled: int = 0  # the number cells that keep their value but not their spelling (`1.50` as `1.5`)
    trimmed: int = 0  # the cells whose surrounding whitespace the cleaning removed
    missing_tokens: Counter[str] = field(default_factory=Counter)  # `MISSING_VALUES` tokens read as missing
    mark_tokens: Counter[str] = field(default_factory=Counter)  # those of them that are a declared mark too
    from_list: bool = False  # a list field of JSON records, expanded into one row per value (`_records`)


def pandas_dtypes(column_dtypes: Mapping[str, ColumnDtype]) -> dict[str, str]:
    """The loader's `dtype=` mapping: every column except the datetime ones, which `parse_dates` takes."""
    return {name: PANDAS_DTYPES[dtype] for name, dtype in column_dtypes.items() if dtype != "datetime"}


def parse_dataset(
    text: str,
    *,
    text_columns: Collection[str] = (),
    find_table: bool = True,
    max_bytes: int = MAX_INPUT_BYTES,
    canonical: bool = False,
    table: int = 1,
) -> ParsedDataset:
    """Parse pasted CSV, TSV, semicolon or pipe text, JSON or a Python literal into the canonical dataset.

    `table` chooses among the tables of a paste that holds several (`_one_table`, 1-based, at
    most `MAX_TABLES`); a number past the tables found is `unparseable`. The result lists them
    in `ParsedDataset.tables` when there are two or more.

    `text_columns` names (canonical) columns that stay text instead of being typed by
    their cells; a name that is no column is ignored. `find_table` narrows pasted text to
    its table (`table_block`); a caller that re-reads a CSV the service wrote itself (a
    prepared, generated or transcribed table) passes False, so every row it holds stays,
    also a category named `Total` that a sort moved to the end. `max_bytes` is the paste
    cap; a caller that re-reads a table the service computed passes `MAX_COMPUTED_BYTES`.

    `canonical` says the text is a CSV the service wrote from a frame (`prepare_data`,
    `generate_data`, `run_data_code`, `.to_long()`): there only an empty cell is missing,
    so a text cell `NA` stays a category, and a column with the same text in every row stays
    a column, because an operation or the user's code made it on purpose. A paste (and the
    transcriber's table, which a model wrote from the user's text) keeps the default: the
    tokens of `MISSING_VALUES` are missing, except `NA` in a column of letter codes
    (`_keep_na_codes`), and a constant text column moves to the notes (`_constants_to_notes`).
    """
    _check_size(text, max_bytes)
    text = text.removeprefix(_BOM)
    _check_controls(text)
    composed = unicodedata.normalize("NFC", text)
    stripped = composed.strip()
    if not stripped:
        raise ParseError("unparseable", "the data is empty")

    warnings: list[str] = []
    if composed != text:
        # The same letters, one code point instead of two (`e` + U+0301 is `é`): said, as every change to the text is.
        changed = sum(1 for line in text.splitlines() if not unicodedata.is_normalized("NFC", line))
        warnings.append(
            f"{_count(changed, 'line')} held decomposed characters (such as e and a separate accent), now written "
            "in Unicode's composed form (NFC); the text reads the same"
        )
    text = composed
    context: list[str] = []
    read: tuple[list[str], list[list[str]], SourceFormat] | None = None
    listed: set[str] = set()  # the headers of list fields that `_records` expanded into rows
    literal = _LITERAL_START.match(stripped)
    if literal:
        assignment, body = literal.group(), stripped[literal.end() :]
        read = _read_literal(body, warnings, context, listed)
        if read is None and (assignment or not body.startswith("(")):
            raise ParseError("unparseable", "the data starts like JSON or a Python literal but is neither")
        # A bare `(` that neither reader accepts is delimited text: `(in %) Land;Wert`, prose in parentheses.
    declared: set[str] = set()
    tables: list[str] = []
    if read is None:
        read = _read_delimited(
            text, warnings, find_table=find_table, context=context, declared=declared, table=table, tables=tables
        )
    elif table > 1:
        raise ParseError("unparseable", f"the data holds one table; there is no table {table}")
    marks = frozenset(declared)
    headers, rows, source_format = read
    parsed = _build(
        headers,
        rows,
        source_format,
        warnings,
        frozenset(text_columns),
        canonical=canonical,
        context=context,
        missing_marks=marks,
        listed=frozenset(listed),
    )
    if len(parsed.csv.encode("utf-8")) > MAX_CANONICAL_BYTES:
        raise ParseError("too_long", f"the data is larger than {MAX_CANONICAL_BYTES // 1024:,} KB once written out")
    if tables:
        parsed = replace(parsed, tables=tables, table=table)
        if parsed.with_constants is not None:
            parsed = replace(parsed, with_constants=replace(parsed.with_constants, tables=tables, table=table))
    return replace(parsed, context_lines=context) if context else parsed


# --- Limits ------------------------------------------------------------------------------


def _check_size(text: str, max_bytes: int = MAX_INPUT_BYTES) -> None:
    try:
        size = len(text.encode("utf-8"))
    except UnicodeEncodeError:
        raise ParseError("unparseable", "the data is not valid Unicode text") from None
    if size > max_bytes:
        raise ParseError("too_long", f"the data is larger than {max_bytes // 1024:,} KB")


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

    Pasted data often carries lines that are not part of the table: a title, an export's
    metadata, a sentence explaining the columns (owner rule of 2026-10-14). So the table
    decides, not the first line: each candidate (`,` `;` tab `|`) splits the sample with
    the csv module, quotes honoured, and its table is the lines of its most common field
    count (at least two fields). The candidate whose table holds the most cells that read
    as a value (a number or a date, `_value_like`) wins, then the one with more such
    lines, then more fields, then the earlier candidate in that order. A semicolon file
    with decimal commas therefore never sniffs as comma-separated: split at its commas,
    its cells are no numbers. A candidate's table counts only when the line above its
    first data row has the table's width, so it can be the header: a single column of
    decimal commas (`v`, `1,5`, `2,3`) is no two-column table without a header.

    Spaces are tried only when none of the four finds a table (since 2026-10-15, live test of
    a MeteoSwiss `.txt`; review of 2026-10-15: a CSV or TSV whose text fields hold spaces must
    never be split at them): runs of two or more spaces (`SPACE_RUN`, so `Max Temp` stays one
    header), then single spaces (`SINGLE_SPACE`), each only with the stricter evidence of
    `_space_block`. Their source format is `whitespace`.

    When no candidate's table holds a value (text-only tables, prose), the header rule
    decides as before (`_sniff_by_header`).
    """
    lines = [line for line in _PHYSICAL_LINE.split(text) if line.strip()][:SNIFF_LINES]
    sample = "\n".join(lines)
    best: tuple[int, int, int] | None = None
    choice: tuple[str | None, SourceFormat] = (None, "csv")
    for delimiter, source_format in DELIMITERS:
        try:
            rows = [row for row in csv.reader(io.StringIO(sample), delimiter=delimiter, skipinitialspace=True) if row]
        except csv.Error:
            continue
        block = table_block(rows)
        if not block.values or len(rows[block.start]) < block.width:
            continue
        count = sum(1 for row in rows if len(row) == block.width)
        key = (block.values, count, block.width)
        if best is None or key > best:
            best, choice = key, (delimiter, source_format)
    if best is not None:
        return choice
    # A table aligned with spaces only where no real delimiter finds one: runs of two or more spaces first,
    # single spaces only when the runs find no table (`_space_block`).
    for delimiter in (SPACE_RUN, SINGLE_SPACE):
        spaced = [fields for line in lines if (fields := _space_fields(line, delimiter))]
        if _space_block(spaced, single=delimiter == SINGLE_SPACE) is not None:
            return delimiter, "whitespace"
    return _sniff_by_header(sample)


def _space_spans(line: str, delimiter: str) -> list[tuple[int, int]]:
    """Where the fields of a space-aligned line sit: runs of two or more spaces (`SPACE_RUN`) or any space between."""
    pattern = _SPACE_RUN_FIELD if delimiter == SPACE_RUN else _SPACE_FIELD
    return [match.span() for match in pattern.finditer(line)]


def _space_fields(line: str, delimiter: str) -> list[str]:
    return [_unquoted(line[start:end]) for start, end in _space_spans(line, delimiter)]


def _unquoted(field_text: str) -> str:
    """A field of a space-aligned table without the quotes around all of it (`"New York"`)."""
    match = _QUOTED.fullmatch(field_text)
    if match is None:
        return field_text
    return match.group(1) if match.group(1) is not None else match.group(2)


def _space_block(records: Sequence[Sequence[str]], *, single: bool) -> "TableBlock | None":
    """The table among space-separated records, or None when spaces are no reliable delimiter here.

    Spaces also separate the words of prose, the items of a list (`Hund 7`) and the keys and
    values of a metadata block (`Station:   Zürich`), which the transcriber or the notes read
    better, so a space-aligned table needs more evidence than a comma one (review of
    2026-10-15: a silent misread is the worst outcome, a refusal beats a guess):

    * a value column (`table_block`) and at least `MIN_SPACE_ROWS` data rows;
    * a header right above the first data row, at the table's width, that is no data row
      itself: none of its cells reads as a value, except two or more years (`Land  2020
      2021`, a wide table);
    * no key-value block: neither the header's first cell nor every first cell of the rows
      ends with a colon (`Station:`, `Altitude:`).

    Single spaces split every word, so there the table must be numbers and dates only: every
    record from the header to the last row has the header's width, every cell of a data row
    reads as a value or is missing, and no two neighbours read as one value together (`1 234`,
    a thousands group; `2024-01-01 12:00`, a timestamp). A table with a text column (`Anna
    Lee 30`) is the transcriber's.
    """
    block = table_block(records)
    if not block.values or block.end - block.start - 1 < MIN_SPACE_ROWS:
        return None
    header = records[block.start]
    if len(header) != block.width:
        return None
    values = [cell for cell in header if _value_like(cell)]
    if values and (len(values) < 2 or len(values) == len(header) or not all(_YEAR.fullmatch(cell) for cell in values)):
        return None
    body = records[block.start + 1 : block.end]
    if header[0].endswith(":") or all(record[0].endswith(":") for record in body if record):
        return None
    if not single:
        return block
    if any(len(record) != block.width for record in records[block.start : block.end + block.summary]):
        return None
    if not all(_missing(cell) or _value_like(cell) for record in body for cell in record):
        return None
    if any(_value_like(f"{left} {right}") for record in body for left, right in pairwise(record)):
        return None
    return block


def _sniff_by_header(sample: str) -> tuple[str | None, SourceFormat]:
    """The delimiter of a table without values: a candidate counts only if it splits the
    header line into at least two fields. Among those, the one under which the most sampled
    lines have exactly the header's field count wins, then the one with more header fields,
    then the earlier candidate. When no candidate splits the header, the text is a single
    column (returned as `None`, reported as `csv`)."""
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


def _read_delimited(
    text: str,
    warnings: list[str],
    *,
    find_table: bool = True,
    context: list[str] | None = None,
    declared: set[str] | None = None,
    table: int = 1,
    tables: list[str] | None = None,
) -> tuple[list[str], list[list[str]], SourceFormat]:
    """The header, the rows and the format of delimited text; the left-out lines go to `context` when given.

    Text that holds several tables, each under its own header after a blank line (a report
    sheet: two tables one below the other), is narrowed to table number `table` first
    (`_one_table`, live test round 5 of 2026-10-15); `tables` gets one label per table found
    when there are two or more.

    A space-aligned table (`SPACE_RUN`, `SINGLE_SPACE`) is split line by line, a field in
    matching quotes losing them, and a row with fewer fields than the header (a blank cell
    in a fixed-width layout) has its fields placed under the header's columns by their
    position (`_aligned`), never padded at the end, which would shift its values into the
    wrong columns. The missing-value marks a line of the paste declares (`_declared_missing`)
    go to `declared` when given, and count as missing while the table is found, so a row of
    marks (`.` under `Fehlwerte: .`) stays a row.
    """
    delimiter, source_format = sniff_delimiter(text)
    spaced = delimiter in (SPACE_RUN, SINGLE_SPACE)
    records: list[tuple[int, list[str]]] = []
    spans: list[list[tuple[int, int]]] = []
    breaks: set[int] = set()  # the records that follow a blank line
    blank = False
    if delimiter is not None and spaced:
        for line_num, line in enumerate(_PHYSICAL_LINE.split(text), start=1):
            if line_spans := _space_spans(line, delimiter):
                if blank and records:
                    breaks.add(len(records))
                blank = False
                records.append((line_num, [_unquoted(line[start:end]) for start, end in line_spans]))
                spans.append(line_spans)
            else:
                blank = True
        if delimiter == SINGLE_SPACE:
            warnings.append("single spaces read as the column separator; check that no value was split in two")
    else:
        reader = csv.reader(
            io.StringIO(text, newline=""), delimiter=delimiter or _NO_DELIMITER, skipinitialspace=True, strict=True
        )
        try:
            for record in reader:
                if any(cell.strip() for cell in record):
                    if blank and records:
                        breaks.add(len(records))
                    blank = False
                    records.append((reader.line_num, record))
                else:
                    blank = True
        except csv.Error as exc:
            raise ParseError("unparseable", f"the quoting is malformed near line {reader.line_num}") from exc
    if not records:
        raise ParseError("unparseable", "the data is empty")
    marks = (
        _declared_missing(_WHITESPACE_RUN.sub(" ", " ".join(record)).strip() for _, record in records)
        if find_table
        else frozenset()
    )
    if declared is not None:
        declared.update(marks)
    if find_table:
        records, spans = _one_table(records, spans, breaks, table, warnings, tables)
    elif table > 1:
        raise ParseError("unparseable", f"the data holds one table; there is no table {table}")
    block = (
        table_block([record for _, record in records], extra_missing=marks)
        if find_table
        else TableBlock(0, len(records))
    )
    extents: list[list[int]] = []
    if spaced:
        extents = _column_extents(spans, block.start, block.end, len(records[block.start][1]))
        if find_table and not block.summary:
            block = _with_trailing_short_rows(block, records, spans, extents)
    if block.above:
        warnings.append(f"left out {_count(block.above, 'line')} above the table (a title, notes or metadata)")
    if block.below:
        warnings.append(f"left out {_count(block.below, 'line')} below the table (notes or a source line)")
    if block.summary:
        warnings.append(
            f"left out {_count(block.summary, 'summary row')} at the end of the table (a total, sum, mean or similar)"
        )
    if context is not None and (block.above or block.below):
        left_out = [record for _, record in (*records[: block.start], *records[block.end + block.summary :])]
        lines, cut = _context_lines(left_out, delimiter)
        context.extend(lines)
        if cut:
            warnings.append(f"the notes around the table were cut at {MAX_CONTEXT_CHARS:,} characters")
    header = records[block.start][1]
    width = len(header)
    rows: list[list[str]] = []
    padded = 0
    for index in range(block.start + 1, block.end):
        line_num, record = records[index]
        if len(rows) == MAX_ROWS:
            raise ParseError("too_many_rows", f"the data has more than {MAX_ROWS:,} rows")
        if len(record) < width:
            record = (
                _aligned(record, spans[index], extents, line_num) if spaced else record + [""] * (width - len(record))
            )
            padded += 1
        elif len(record) > width:
            if any(cell.strip() for cell in record[width:]):
                raise ParseError("unparseable", f"line {line_num} has more fields than the header")
            record = record[:width]
        rows.append(record)
    if padded and spaced:
        warnings.append(
            f"{_count(padded, 'row')} had fewer fields than the header; their cells were placed under the header's "
            "columns by their position, and the cells left over are empty"
        )
    elif padded:
        warnings.append(f"{_count(padded, 'row')} had fewer fields than the header; the missing cells are empty")
    return header, rows, source_format


MIN_TABLE_ROWS = 2
"""The rows right under a header after a blank line that make it a table of its own (`_table_starts`)."""
MAX_TABLES = 10
"""The tables of one paste that can be chosen (`parse_dataset(table=...)`) and are labelled; a later one is counted
in the warning only, never read and never joined to the tenth."""
MAX_TABLE_LABEL_CHARS = 80
MAX_TABLES_NAMED = 3  # the left-out tables the warning names before it counts the rest


def _one_table(
    records: list[tuple[int, list[str]]],
    spans: list[list[tuple[int, int]]],
    breaks: Collection[int],
    table: int,
    warnings: list[str],
    tables: list[str] | None,
) -> tuple[list[tuple[int, list[str]]], list[list[tuple[int, int]]]]:
    """The records of table number `table` (1-based) when the text holds two or more tables, else all of them.

    A report sheet often holds several tables one below the other (live test round 5 of
    2026-10-15: a title, a revenue table, a blank row, a caption and a staff table), and
    `table_block` alone would read them as one, the second header a data row that turns
    every number column into text. A table of its own starts after a blank line (or at the
    top) with a header under at most a few one-field lines (a caption), see `_table_starts`.
    With two or more such tables, table `table` is read: its own lines from its blank line
    to the next table's, after the lines above the first table (a title, which belongs to
    every table), so `table_block` finds its header, its notes and its summary rows as for a
    single table. One warning names the table read and the ones left out; `tables` gets one
    label per table (its header and its row count), which the dataset route answers so the
    page can offer the others, as it offers a workbook's other sheets. Only the first
    `MAX_TABLES` can be chosen and are labelled; every table keeps its own boundaries, so a
    later one never joins the tenth (Copilot review of #12200). Fewer than two tables leave
    the records as they are.
    """
    starts = _table_starts([record for _, record in records], breaks)
    if len(starts) < 2:
        if table > 1:
            raise ParseError("unparseable", f"the data holds one table; there is no table {table}")
        return records, spans
    choosable = min(len(starts), MAX_TABLES)
    if table > choosable:
        raise ParseError("unparseable", f"the data holds {len(starts)} tables; table {table} cannot be read")
    lead = list(range(starts[0][1]))  # the lines above the first table's header: a title, notes
    regions: list[list[int]] = []
    for index, (group, _) in enumerate(starts[:choosable]):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(records)
        regions.append(list(range(end)) if index == 0 else [*lead, *range(group, end)])
    labels: list[str] = []
    for (_, header), region in zip(starts, regions, strict=False):
        block = table_block([records[index][1] for index in region])
        rows = block.end - block.start - 1
        names = ", ".join(name for cell in records[header][1] if (name := _clean_header(cell)[0]))
        labels.append(f"{_clip(names, MAX_TABLE_LABEL_CHARS)} · {_count(rows, 'row')}")
    if tables is not None:
        tables.extend(labels)
    others = [f"table {number} ({label})" for number, label in enumerate(labels, start=1) if number != table]
    named = ", ".join(others[:MAX_TABLES_NAMED])
    more = len(starts) - 1 - min(len(others), MAX_TABLES_NAMED)
    if more:
        named += f" and {_count(more, 'other table')}"
    warnings.append(
        f"the data holds {len(starts)} tables, each under its own header; read table {table} "
        f"({labels[table - 1]}) and left out {named}; the table picker in the data panel reads another one"
    )
    chosen = regions[table - 1]
    return [records[index] for index in chosen], [spans[index] for index in chosen] if spans else spans


def _table_starts(records: Sequence[Sequence[str]], breaks: Collection[int]) -> list[tuple[int, int]]:
    """Where each table of its own starts: the first record of its blank-line group and its header's index.

    The records between blank lines form groups. A group starts a table when, after at most
    a few lines of one filled field each (a caption such as `Personal und Fläche`), it holds
    a header (`_header_line`) and right below it `MIN_TABLE_ROWS` rows of the header's width
    with a value each (`_value_like`). A group of data rows under no header (a table with a
    blank line inside it), a group of notes, and an export's metadata of one row (Open-Meteo's
    `latitude,longitude` and its values above the real table) start none, so such text stays
    one table as before. Neither does a key-value block (`Station:,Zürich`): a header or every
    first cell of its rows ending with a colon.
    """
    bounds = [0, *sorted(index for index in breaks if 0 < index < len(records)), len(records)]
    starts: list[tuple[int, int]] = []
    for group, end in pairwise(bounds):
        header = group
        while header < end and sum(1 for cell in records[header] if cell.strip()) <= 1:
            header += 1
        if end - header - 1 < MIN_TABLE_ROWS or not _header_line(records[header]):
            continue
        width = len(records[header])
        rows = records[header + 1 : header + 1 + MIN_TABLE_ROWS]
        if not all(len(row) == width and any(_value_like(cell) for cell in row) for row in rows):
            continue
        if all(row[0].strip().endswith(":") for row in records[header + 1 : end] if row):
            continue
        starts.append((group, header))
    return starts


def _header_line(record: Sequence[str]) -> bool:
    """A record that reads as a table's header: two or more distinct filled names, none a missing mark, and no value
    among them except two or more years in a wide table (`Land,2020,2021`); its first name ends with no colon."""
    cells = [cell.strip() for cell in record]
    if len(cells) < 2 or not all(cells) or any(cell in MISSING_VALUES for cell in cells):
        return False
    if len({cell.casefold() for cell in cells}) < len(cells) or cells[0].endswith(":"):
        return False
    values = [cell for cell in cells if _value_like(cell)]
    return not values or (
        len(values) >= 2 and len(values) < len(cells) and all(_YEAR.fullmatch(cell) for cell in values)
    )


def _with_trailing_short_rows(
    block: "TableBlock",
    records: Sequence[tuple[int, list[str]]],
    spans: Sequence[Sequence[tuple[int, int]]],
    extents: Sequence[Sequence[int]],
) -> "TableBlock":
    """`block` extended over the short rows right below its last full row that line up under its columns.

    `table_block` ends a table at its last row of the full width, so a fixed-width table whose
    last rows have blank cells (`2022     4.7             6.9`) would lose them to the notes. A
    record below counts as a row while every field lines up under one column (`_lined_up`) and
    one of them reads as a value; a source line or a note, which holds no value or has a field
    under no column, still ends the table. A record that looks like a row (half its fields or
    more are values, each field under some column) but does not line up is `unparseable`, as
    such a row inside the table is (review of 2026-10-15): it is neither left out as a note nor
    placed by guess. A summary row (`Total`, `Summe`) ends the table too: up to
    `MAX_SUMMARY_ROWS` of them right below are left out as summary rows, as `table_block` does
    with full ones, neither data nor notes.
    """
    end = block.end
    while end < len(records):
        line_num, fields = records[end]
        if len(fields) >= len(extents) or not any(_value_like(cell) for cell in fields) or _summary_row(fields):
            break
        if _lined_up(fields, spans[end], extents) is None:
            under_some = all(
                any(min(right, high) > max(left, low) for low, high in extents) for left, right in spans[end]
            )
            if under_some and 2 * sum(_value_like(cell) for cell in fields) >= len(fields):
                raise ParseError("unparseable", f"line {line_num} does not line up with the columns of the header")
            break
        end += 1
    summary = 0
    while (
        summary < MAX_SUMMARY_ROWS
        and end + summary < len(records)
        and _summary_row(records[end + summary][1])
        and any(_value_like(cell) for cell in records[end + summary][1])
    ):
        summary += 1
    if end == block.end and not summary:
        return block
    return replace(block, end=end, summary=summary, below=len(records) - end - summary)


def _column_extents(spans: Sequence[Sequence[tuple[int, int]]], start: int, end: int, width: int) -> list[list[int]]:
    """The character range each column of a space-aligned table covers: its header and its full rows together."""
    extents = [[left, right] for left, right in spans[start]]
    for line_spans in spans[start + 1 : end]:
        if len(line_spans) != width:
            continue
        for extent, (left, right) in zip(extents, line_spans, strict=True):
            extent[0], extent[1] = min(extent[0], left), max(extent[1], right)
    return extents


def _aligned(
    fields: Sequence[str], spans: Sequence[tuple[int, int]], extents: Sequence[Sequence[int]], line_num: int
) -> list[str]:
    """A short row of a space-aligned table, each field under the one column whose range it overlaps; `unparseable`
    when the placement is no certainty (`_lined_up`), so no value is placed by guess."""
    cells = _lined_up(fields, spans, extents)
    if cells is None:
        raise ParseError("unparseable", f"line {line_num} does not line up with the columns of the header")
    return cells


def _lined_up(
    fields: Sequence[str], spans: Sequence[tuple[int, int]], extents: Sequence[Sequence[int]]
) -> list[str] | None:
    """The row's cells by position under the columns, or None when the placement is no certainty.

    That is: the columns' own ranges overlap (the full rows are not aligned, so no position
    is evidence), a field overlaps no column or more than one (`-12.5` reaching from one
    column into the next), or two fields share a column or come out of order.
    """
    if any(extents[index][1] > extents[index + 1][0] for index in range(len(extents) - 1)):
        return None
    cells = [""] * len(extents)
    last = -1
    for field_text, (left, right) in zip(fields, spans, strict=True):
        under = [index for index, (low, high) in enumerate(extents) if min(right, high) > max(left, low)]
        if len(under) != 1:
            return None
        column = under[0]
        if column <= last:
            return None
        cells[column] = field_text
        last = column
    return cells


@dataclass(frozen=True)
class TableBlock:
    """Where the table sits among the pasted records: `records[start]` is the header, the rows
    run to `end` (exclusive); `above`, `below` and `summary` count the records left out."""

    start: int
    end: int
    above: int = 0
    below: int = 0
    summary: int = 0
    width: int = 0
    """The table's field count; 0 when no table with a value column was found (every record kept)."""
    values: int = 0
    """The cells of the data rows that read as values."""


def table_block(records: Sequence[Sequence[str]], *, extra_missing: frozenset[str] = frozenset()) -> TableBlock:
    """The table among pasted records that may carry other lines (owner rule of 2026-10-14).

    Real pastes are rarely a bare table: an export starts with metadata (Open-Meteo writes
    `latitude,longitude,…` and its values above the header), a user adds a sentence that
    explains the columns, and a source line, a note or a total row follows the table. The
    table is found by its data: its width is the most common field count (at least two
    fields, the larger one on a tie), its value columns are the columns where at least
    `VALUE_SHARE` of the filled cells read as a value (`_value_like`) in the records of
    that width, and a data row is a record of that width with a value in at least half of
    the value columns.

    * The header is the record right above the first data row, past any wider record that
      also holds the data (a ragged table's full rows, whose header is wider than its short
      ones); everything above it is left out. When the first record already is a data row,
      it is the header, as before.
    * The rows end after the last data row and the records right below it that hold data at
      the table's width or wider, or whose value cells are missing (`2024-01-11,,`); anything after that is
      left out, such as a source line or a sentence, also one that its commas split into
      the table's width.
    * At most `MAX_SUMMARY_ROWS` rows at the end whose first filled cell is a summary label
      (`SUMMARY_LABELS`: total, sum, mean, Summe, Gesamt…) are left out.

    A table without a value column (text only, prose) and a table of fewer than three records
    of its width keep every record: the first is the header. `extra_missing` holds the marks the
    paste declares (`_declared_missing`), which count as missing cells here like `NA`.
    """
    whole = TableBlock(0, len(records))
    widths = Counter(len(record) for record in records if len(record) >= 2)
    if not widths:
        return whole
    width = max(widths.items(), key=lambda item: (item[1], item[0]))[0]
    sized = [record for record in records if len(record) == width]
    if len(sized) < 3:
        return whole
    # The first record of the width is left out of the vote: it may be the header.
    values = [j for j in range(width) if _mostly_values((row[j] for row in sized[1:]), extra_missing)]
    if not values:
        return whole

    def data_row(record: Sequence[str]) -> bool:
        return len(record) == width and 2 * sum(_value_like(record[j]) for j in values) >= len(values)

    def wide_data_row(record: Sequence[str]) -> bool:
        # A data row with more fields than the most common width: a ragged table's full rows
        # (`a,b,c` / `1,2,3` / `4,5` / `6,7`), whose header is wider than its short rows.
        return len(record) >= width and 2 * sum(_value_like(record[j]) for j in values) >= len(values)

    def sparse_row(record: Sequence[str]) -> bool:
        # A row of the table that lacks values (`2024-01-11,,`), not a sentence split at its commas.
        return len(record) == width and all(
            _missing(record[j], extra_missing) or _value_like(record[j]) for j in values
        )

    rows = [index for index, record in enumerate(records) if data_row(record)]
    first, last = rows[0], rows[-1]
    start = max(first - 1, 0)
    while start > 0 and wide_data_row(records[start]):
        start -= 1
    end = last + 1
    while end < len(records) and (sparse_row(records[end]) or wide_data_row(records[end])):
        end += 1
    below = len(records) - end
    summary = 0
    while summary < MAX_SUMMARY_ROWS and end - 1 > start and _summary_row(records[end - 1]):
        end -= 1
        summary += 1
    found = sum(_value_like(records[index][j]) for index in rows for j in range(width))
    return TableBlock(start, end, above=start, below=below, summary=summary, width=width, values=found)


def value_like(cell: str) -> bool:
    """Whether a cell reads as a number or a date, also behind a unit; the default bindings rank text of such cells last."""
    return _value_like(cell)


def _value_like(cell: str) -> bool:
    """A cell that reads as a number or a date, also behind a unit (`65 %`, `€ 5`)."""
    cell = cell.strip()
    return bool(cell and (_looks_like_value(cell) or _TRAILING_UNIT.fullmatch(cell) or _LEADING_UNIT.fullmatch(cell)))


def _missing(cell: str, marks: frozenset[str] = frozenset()) -> bool:
    cell = cell.strip()
    return cell in MISSING_VALUES or bool(marks and _matches_mark(cell, marks))


def _matches_mark(cell: str, marks: frozenset[str]) -> bool:
    """Whether a cleaned cell is a declared missing-value mark; a number matches by value (`-999.0` is `-999`)."""
    if cell in marks:
        return True
    if not _MARK_NUMBER.fullmatch(cell):
        return False
    value = float(cell.replace(",", "."))
    return any(_MARK_NUMBER.fullmatch(mark) and float(mark.replace(",", ".")) == value for mark in marks)


def _mostly_values(cells: Iterable[str], marks: frozenset[str] = frozenset()) -> bool:
    present = [cell for cell in cells if not _missing(cell, marks)]
    return bool(present) and sum(_value_like(cell) for cell in present) >= VALUE_SHARE * len(present)


def _summary_row(record: Sequence[str]) -> bool:
    label = next((cell.strip() for cell in record if not _missing(cell)), "")
    return label.rstrip(":").strip().casefold() in SUMMARY_LABELS


def _declared_missing(lines: Iterable[str]) -> frozenset[str]:
    """The missing-value marks the lines of a paste declare (`Missing values: NA`, `nodata = -999`).

    A weather or statistics export often names its mark in the metadata above the table, and
    the mark can be one the parser would otherwise read as a value (`-999`, `9999`, `M`). A
    line counts when it is only such a declaration. The mark is a sentinel number (negative,
    or 999 and more in size: `-999`, `-9999`, `9999`; review of 2026-10-15: `Missing values: 1`
    would blank every ordinary 1), one to three symbols (`.`, `*`, `--`) or one to three letters
    that are no answer (`no`, `ja`: `Missing values: none` says that nothing is missing). A
    number matches by value (`-999.0` is `-999`). The marks blank cells of number and date
    columns only (owner decision of 2026-10-15, `_build`): a text category `M` or `NA`
    (Namibia) stays.
    """
    marks: set[str] = set()
    for line in lines:
        match = _MISSING_DECLARATION.fullmatch(line.strip())
        if match is None:
            continue
        mark = match["mark"]
        if not _DECLARED_MARK.fullmatch(mark) or mark.casefold() in _NOT_A_MARK:
            continue
        if _MARK_NUMBER.fullmatch(mark):
            value = float(mark.replace(",", "."))
            if not (value < 0 or abs(value) >= MIN_SENTINEL):
                continue
        marks.add(mark)
    return frozenset(marks)


def _context_lines(records: Iterable[Sequence[str]], delimiter: str | None) -> tuple[list[str], bool]:
    """The left-out records as text lines, and whether the cap cut them.

    Each record becomes one line: its fields cleaned like cells (invisible format characters
    removed, any run of whitespace, line breaks inside a quoted field too, one space), the
    empty ones dropped, the rest joined with the delimiter's display form (`CONTEXT_JOINERS`),
    so `Source: DWD, station 433` reads as pasted. A record without text is dropped. All lines
    with their line breaks hold at most `MAX_CONTEXT_CHARS`: the first line past the cap is
    cut with `…` when a useful part of it fits, and every later one is dropped.
    """
    joiner = CONTEXT_JOINERS.get(delimiter, " ")
    lines: list[str] = []
    left = MAX_CONTEXT_CHARS
    for record in records:
        fields = (_WHITESPACE_RUN.sub(" ", _strip_invisible(cell)[0]).strip() for cell in record)
        line = joiner.join(cell for cell in fields if cell)
        if not line:
            continue
        need = len(line) + (1 if lines else 0)  # the line break before every line but the first
        if need > left:
            room = left - (1 if lines else 0)
            if room >= 20:  # a stub of a few characters says nothing
                lines.append(line[: room - 1].rstrip() + "…")
            return lines, True
        lines.append(line)
        left -= need
    return lines, False


def _read_literal(
    text: str, warnings: list[str], context: list[str], listed: set[str] | None = None
) -> tuple[list[str], list[list[str]], SourceFormat] | None:
    """JSON, or a Python literal when the JSON reader refuses the text, tabulated alike; None when it is neither.

    A JSON-stat dataset (`_json_stat`) is flattened instead, its title, source, notes and
    one-category dimensions going to `context`.
    """
    if _too_deep(text):
        raise ParseError("unparseable", f"the data is nested more than {MAX_NESTING} levels deep")
    decoded = _decode_literal(text)
    if decoded is None:
        return None
    data, repeated, constants = decoded
    if repeated:
        warnings.append(f"{_count(repeated, 'key')} repeated; only the last value of a repeated key is kept")
    if constants:
        # A number column holds finite values only (`data.csv` and the loader's float64 have no text for them).
        warnings.append(f"{_count(constants, 'value')} NaN, Infinity or -Infinity read as missing")
    dataset = _json_stat_dataset(data)
    if dataset is not None:
        return _json_stat(dataset, warnings, context)
    records = _api_records(data, warnings, context)
    return _tabulate(data if records is None else records, warnings, listed)


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


def _decode_literal(text: str) -> tuple[Any, int, int] | None:
    """The decoded value, the number of repeated object keys and of JSON's `NaN` and `Infinity` constants (each
    read as a missing value); None when neither reader accepts the text.

    `json.loads` first, then `ast.literal_eval`, which evaluates literals only: a name
    or a call is a ValueError, never run. Both keep the last value of a repeated key,
    so the count lets the caller say that rows went missing.
    """
    repeated = 0
    constants = 0

    def objects(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        nonlocal repeated
        repeated += len(pairs) - len({key for key, _ in pairs})
        return dict(pairs)

    def constant(_: str) -> None:
        nonlocal constants
        constants += 1  # `NaN`, `Infinity`, `-Infinity`: no finite value, so missing, and counted
        return None

    try:
        loaded = json.loads(text, parse_constant=constant, parse_float=_SourceFloat, object_pairs_hook=objects)
        return loaded, repeated, constants
    except (ValueError, RecursionError):
        pass
    try:
        tree = _FloatTexts(text).visit(ast.parse(text, mode="eval"))
        value = ast.literal_eval(tree)
    except (ValueError, SyntaxError, TypeError, RecursionError, MemoryError):
        return None
    return value, _repeated_keys(tree), 0


class _SourceFloat(float):
    """A float of a JSON or Python literal that remembers how it was written.

    `json.loads` and `ast.literal_eval` read `0.1234567890123456789` as a float64 of 17
    digits; the cell takes the written text instead (`_json_cell`), so the typing step
    sees every digit and says when a number column holds one only rounded.
    """

    text: str

    def __new__(cls, text: str) -> "_SourceFloat":
        digits = text.replace("_", "")  # Python's digit separators (`0.123_456`) are no part of the value
        number = super().__new__(cls, digits)
        number.text = digits
        return number


class _FloatTexts(ast.NodeTransformer):
    """Turn the float constants of a Python literal into `_SourceFloat`s of their written text.

    A signed float (`-0.5`) becomes one constant with its sign, since `literal_eval` applies
    a sign only to a plain `float`. A complex literal (`1.5+2j`) is left as Python reads it.
    The text is sliced by the node's UTF-8 offsets from lines split once: `ast.get_source_segment`
    splits the whole source for every call, quadratic in a paste of many floats (review of #12196).
    """

    def __init__(self, source: str) -> None:
        # The line breaks Python's tokenizer counts: LF, CRLF and a lone CR.
        self.lines = [line.encode("utf-8") for line in _PHYSICAL_LINE.split(source)]

    def _constant(self, node: ast.AST, sign: str, constant: ast.Constant) -> ast.AST:
        line, end_line = constant.lineno, constant.end_lineno
        if end_line != line or constant.end_col_offset is None or not 0 < line <= len(self.lines):
            return node  # a float literal never spans lines; anything else keeps Python's own value
        written = self.lines[line - 1][constant.col_offset : constant.end_col_offset].decode("utf-8")
        return ast.copy_location(ast.Constant(_SourceFloat(sign + written)), node)

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        return node

    def visit_UnaryOp(self, node: ast.UnaryOp) -> ast.AST:
        operand = node.operand
        if (
            isinstance(node.op, ast.USub | ast.UAdd)
            and isinstance(operand, ast.Constant)
            and type(operand.value) is float
        ):
            return self._constant(node, "-" if isinstance(node.op, ast.USub) else "", operand)
        return self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        return self._constant(node, "", node) if type(node.value) is float else node


def _repeated_keys(tree: ast.AST) -> int:
    """How many dict keys of an evaluated literal repeat an earlier key of the same dict."""
    repeated = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            keys = [ast.literal_eval(key) for key in node.keys if key is not None]
            repeated += len(keys) - len(set(keys))
    return repeated


def _tabulate(
    data: Any, warnings: list[str], listed: set[str] | None = None
) -> tuple[list[str], list[list[str]], SourceFormat]:
    """Headers and rows from the decoded value; a tuple counts as a list. `listed` collects expanded list fields."""
    if isinstance(data, (list, tuple)):
        if not data:
            raise ParseError("unparseable", "the array is empty")
        if len(data) > MAX_ROWS:
            raise ParseError("too_many_rows", f"the data has more than {MAX_ROWS:,} rows")
        if all(isinstance(record, dict) for record in data):
            return _records(data, warnings, listed)
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


def _api_records(data: Any, warnings: list[str], context: list[str]) -> list[dict[Any, Any]] | None:
    """The records of an API response that wraps them with metadata; None for any other shape.

    Two wrappings are common (live test of 2026-10-15: the World Bank API answers
    `[{page metadata}, [records]]` and was refused): an array of objects and exactly one
    list of records (`[{"page": 1, ...}, [{...}, ...]]`), and an object with exactly one
    list of records beside other fields (`{"data": [...], "meta": {...}}`, also under
    `results`, `records`, `items` or any other name). A list of records is a non-empty
    list whose every element is an object. The other objects, or the object's other
    fields, are metadata: their text, number and boolean fields, nested objects flattened
    with dots as in a record (`_flatten`), go to `context` as `<name>: <value>` lines, the
    notes the user pasted with the data, and fields that hold lists are left out; one
    warning counts them. Two lists of records are `unparseable`: the response holds two
    tables, and the parser takes none by guess. An array of only objects, or of only
    lists, is no wrapping and goes to `_tabulate` as before.
    """
    metadata: list[Mapping[Any, Any]]
    if isinstance(data, (list, tuple)):
        lists = [entry for entry in data if isinstance(entry, (list, tuple))]
        if not lists or len(lists) == len(data) or not all(isinstance(entry, (dict, list, tuple)) for entry in data):
            return None
        tables = [entry for entry in lists if _record_list(entry)]
        if not tables:
            raise ParseError("unparseable", "the response holds metadata but no list of records")
        if len(lists) > 1:
            raise ParseError("unparseable", f"the response holds {len(lists)} lists; paste one list of records")
        metadata = [entry for entry in data if isinstance(entry, dict)]
        records = tables[0]
    elif isinstance(data, dict):
        rows = _schema_rows(data)
        if rows is not None:
            metadata = [{key: value for key, value in data.items() if not isinstance(value, (list, tuple))}]
            records = rows
        else:
            keys = [key for key, value in data.items() if _record_list(value)]
            if not keys:
                return None
            if len(keys) == 2:
                # A list of field descriptors beside the records is their schema, but only when it holds nothing
                # but descriptor keys and names every field of the records; otherwise two tables, none by guess.
                schema = [key for key in keys if _schema_of(data[key], data[next(k for k in keys if k != key)])]
                if len(schema) == 1:
                    keys = [key for key in keys if key != schema[0]]
            if len(keys) > 1:
                raise ParseError(
                    "unparseable", f"the object holds {len(keys)} lists of records; paste one list of records at a time"
                )
            if all(_descriptor(item) for item in data[keys[0]]) and any(
                isinstance(value, (list, tuple)) and not value for value in data.values()
            ):
                raise ParseError(
                    "unparseable", "the list of records is empty; only the description of its fields is there"
                )
            metadata = [{key: value for key, value in data.items() if key != keys[0]}]
            records = data[keys[0]]
    else:
        return None
    lines: list[str] = []
    left_out = 0
    for entry in metadata:
        fields, entry_lists, dropped = _flatten(entry)
        left_out += len(dropped) + len(entry_lists)
        for name, value in fields.items():
            cell = _json_text(value, "a field beside the records") if isinstance(value, str) else _json_cell(value, 0)
            if cell.strip():
                lines.append(f"{name}: {cell}")
    if lines:
        warnings.append(
            f"{_count(len(lines), 'field')} beside the records (such as paging or a timestamp) moved to the notes"
        )
    if left_out:
        warnings.append(f"{_count(left_out, 'field')} beside the records that hold lists left out")
    kept, cut = _context_lines([[line] for line in lines], None)
    context.extend(kept)
    if cut:
        warnings.append(f"the notes from the fields beside the records were cut at {MAX_CONTEXT_CHARS:,} characters")
    return list(records)


def _record_list(value: Any) -> bool:
    """A non-empty list whose every element is an object: one table of records."""
    return isinstance(value, (list, tuple)) and bool(value) and all(isinstance(item, dict) for item in value)


DESCRIPTOR_KEYS: frozenset[str] = frozenset(
    {
        *("name", "type", "format", "description", "title", "label", "mode", "unit", "constraints", "id"),
        *("fieldName", "dataTypeName", "example", "rdfType", "fields", "info", "nullable"),
    }
)
"""The keys a field descriptor of a schema holds (Frictionless, BigQuery, CKAN, Socrata); a record with any other key
is data, also one that has a `name` and a `type` (`{"name": "Solar", "type": "renewable", "gwh": 420}`)."""


def _descriptor(item: Any) -> bool:
    """A field descriptor of a schema: an object with a text `name`, a `type` and no key outside `DESCRIPTOR_KEYS`."""
    return (
        isinstance(item, dict)
        and isinstance(item.get("name"), str)
        and "type" in item
        and all(isinstance(key, str) and key in DESCRIPTOR_KEYS for key in item)
    )


def _schema_of(descriptors: Sequence[Any], records: Sequence[Any]) -> bool:
    """Whether `descriptors` describe `records`: descriptors only, and their names cover every field of the records."""
    if not all(_descriptor(item) for item in descriptors):
        return False
    names = {item["name"] for item in descriptors}
    return all(isinstance(record, dict) and set(map(str, record)) <= names for record in records)


def _row_list(value: Any) -> bool:
    """A non-empty list whose every element is a list: rows of cells without names."""
    return isinstance(value, (list, tuple)) and bool(value) and all(isinstance(item, (list, tuple)) for item in value)


def _schema_names(data: Mapping[Any, Any]) -> list[str] | None:
    """The column names a schema-and-rows payload gives, from the first place it names them; None without one.

    `fields` or `columns` at the top (CKAN, pandas `orient="split"`), `schema.fields` (Frictionless,
    BigQuery, pandas `orient="table"`) or `meta.view.columns` (Socrata); each a list of names or of
    objects with a text `name` (Socrata: `fieldName` or `name`).
    """
    schema, meta = data.get("schema"), data.get("meta")
    view = meta.get("view") if isinstance(meta, dict) else None
    places = (
        data.get("fields"),
        data.get("columns"),
        schema.get("fields") if isinstance(schema, dict) else None,
        view.get("columns") if isinstance(view, dict) else None,
    )
    for place in places:
        if not isinstance(place, (list, tuple)) or not place:
            continue
        names = [
            item
            if isinstance(item, str)
            else item.get("fieldName") or item.get("name")
            if isinstance(item, dict)
            else None
            for item in place
        ]
        if all(isinstance(name, str) for name in names):
            return [name for name in names if isinstance(name, str)]
    return None


def _schema_rows(data: Mapping[Any, Any]) -> list[dict[str, Any]] | None:
    """The records of a schema-and-rows payload (`{"fields": [...], "rows": [[...], ...]}`); None for another shape.

    CKAN, Socrata, Frictionless and pandas (`orient="split"`) write the column names once
    (`_schema_names`) and the rows as lists of cells (review of 2026-10-15: the parser took the
    field list for the table and dropped the rows). An object with exactly one list of rows is
    read as one record per row, named by the schema; a list of rows without names that match
    its length, two lists of rows or a repeated name are `unparseable`, so the schema is never
    taken for the data. BigQuery's own `rows: [{"f": [{"v": ...}]}]` is no list of rows: its
    cells are a list of objects, which `_flatten` leaves out, and the paste is refused.
    """
    keys = [key for key, value in data.items() if _row_list(value)]
    if not keys:
        return None
    names = _schema_names(data)
    if len(keys) > 1 or names is None:
        raise ParseError("unparseable", "the object holds rows as lists of cells without column names that fit them")
    rows = data[keys[0]]
    if any(len(row) != len(names) for row in rows):
        raise ParseError(
            "unparseable", f"the rows do not all hold one cell for each of the {len(names)} column names of the schema"
        )
    if len(set(names)) != len(names):
        raise ParseError("unparseable", "the schema names a column twice")
    if len(rows) > MAX_ROWS:
        raise ParseError("too_many_rows", f"the data has more than {MAX_ROWS:,} rows")
    return [dict(zip(names, row, strict=True)) for row in rows]


def _flatten(record: Mapping[Any, Any]) -> tuple[dict[str, Any], dict[str, list[Any]], list[str]]:
    """A record's scalar fields with nested objects flattened, its list fields, and the names of the fields left out.

    A nested object's fields become fields named `<parent>.<field>` (`country.value`,
    `indicator.id`), down to `MAX_FLATTEN_DEPTH` levels: canonical data is one flat table
    (owner rule of 2026-10-11). A field that holds a list of text, numbers, booleans or null
    (`"x": [0, 1, 2]`) comes back on its own, for `_records` to expand into rows. A list of
    objects or of lists, and an object nested deeper, is left out and named in the third list.
    Two fields that get one name (`{"a.b": 1, "a": {"b": 2}}`, or the keys `1` and `'1'` of a
    literal) are `unparseable`: either value would be lost.
    """
    flat: dict[str, Any] = {}
    lists: dict[str, list[Any]] = {}
    dropped: list[str] = []

    def walk(mapping: Mapping[Any, Any], prefix: str, depth: int) -> None:
        for position, (key, value) in enumerate(mapping.items()):
            name = prefix + _json_key(key, position)
            if name in flat or name in lists:
                raise ParseError("unparseable", "two fields of a record get the same column name once flattened")
            if isinstance(value, dict) and depth < MAX_FLATTEN_DEPTH:
                walk(value, f"{name}.", depth + 1)
            elif isinstance(value, (list, tuple)) and all(_scalar(item) for item in value):
                lists[name] = list(value)
            elif isinstance(value, (dict, list, tuple)):
                dropped.append(name)
            else:
                flat[name] = value

    walk(record, "", 0)
    return flat, lists, dropped


RECORD_ID = "record_id"
"""The column `_records` adds when it expands list fields into rows and no field tells the records apart: the
1-based position of the record each row came from, so the rows of one curve stay one series."""


def _records(
    records: Sequence[Mapping[Any, Any]], warnings: list[str], listed: set[str] | None = None
) -> tuple[list[str], list[list[str]], SourceFormat]:
    """One column per field of any record, nested objects flattened and list fields expanded into rows.

    `listed`, when given, collects the headers of the list fields that expanded, so the
    profile can name them (`DatasetProfile.list_columns`, live test round 4 of 2026-10-15).

    Nested objects become dotted columns (`_flatten`). List fields expand to long format
    (owner decision of 2026-10-15, a measurement curve per record: `{"sample": "A", "x":
    [...], "y": [...]}`): a record whose lists all have the same length n gives n rows, the
    k-th row holding the k-th value of each list and the record's other fields repeated; a
    record whose non-empty lists differ in length is `unparseable`, the message naming the
    record, the fields and their lengths; an empty list leaves its cells empty in that
    record's rows, and a record whose lists are all empty gives one row. A field that is a
    list in one record and a single value in another is `unparseable`: repeating the value
    over the other record's points would be a guess. Independent lists of one length (`tags`
    and `scores`) are paired by position too; the warning names every expanded field. When
    the records expanded into several rows each and no text or whole-number field has a
    different value in every record (`_tells_apart`), a first column numbers the records
    (`RECORD_ID`, or `record_id_2` and so on when a field has that name), so each curve
    stays one series.

    The expanded rows keep `MAX_ROWS` (`_thinned`): when the lists hold more points, each
    record keeps evenly spaced points with its first and last one, with a warning that
    gives the counts, so nothing is cut silently and the root can say what keeps every point.
    """
    flattened: list[tuple[dict[str, Any], dict[str, list[Any]]]] = []
    dropped: dict[str, None] = {}
    nested = False
    for index, record in enumerate(records, start=1):
        fields, lists, left_out = _flatten(record)
        nested = nested or any(isinstance(value, dict) and value for value in record.values())
        dropped.update(dict.fromkeys(left_out))
        lengths = {name: len(values) for name, values in lists.items() if values}
        if len(set(lengths.values())) > 1:
            described = ", ".join(
                f"{_clip(name, MAX_COLUMN_NAME_CHARS)} ({length})" for name, length in lengths.items()
            )
            raise ParseError(
                "unparseable",
                f"record {index}: its lists differ in length ({described}); list fields of one record expand into "
                "rows together and need one length",
            )
        flattened.append((fields, lists))
    list_fields = {name for _, lists in flattened for name in lists}
    mixed = sorted(name for name in list_fields if any(fields.get(name) is not None for fields, _ in flattened))
    if mixed:
        raise ParseError(
            "unparseable",
            f"the field {_clip(mixed[0], MAX_COLUMN_NAME_CHARS)} holds a list in some records and a single value "
            "in others; it needs the same shape in every record",
        )
    if dropped and not any(fields or lists for fields, lists in flattened):
        raise ParseError(
            "unparseable", "no field of the records holds text, a number, a boolean or null, or a list of them"
        )
    if nested:
        warnings.append("fields of nested objects became columns named with a dot, such as parent.field")
    if dropped:
        names = [_clip(name, MAX_COLUMN_NAME_CHARS) for name in dropped]
        shown = ", ".join(names[:MAX_NAMED_FIELDS]) + (", …" if len(names) > MAX_NAMED_FIELDS else "")
        warnings.append(
            f"{_count(len(names), 'field')} holding a list of objects or lists, or objects nested more than "
            f"{MAX_FLATTEN_DEPTH} levels deep, left out: {shown}"
        )
    if not any(lists for _, lists in flattened):
        return _flat_records([fields for fields, _ in flattened], warnings)
    table = _flat_records(_expanded(flattened, warnings), warnings)
    if listed is not None:
        listed.update(header for header in table[0] if header in list_fields)
    return table


def _expanded(
    flattened: Sequence[tuple[dict[str, Any], dict[str, list[Any]]]], warnings: list[str]
) -> list[dict[str, Any]]:
    """The records with their list fields expanded into rows, thinned to `MAX_ROWS` and numbered when needed."""
    points = [max((len(values) for values in lists.values()), default=0) for _, lists in flattened]
    kept = _thinned(points)
    all_fields = {name for fields, lists in flattened for name in (*fields, *lists)}
    numbered = (
        len(flattened) > 1
        and any(count > 1 for count in points)
        and not any(_tells_apart(name, [fields for fields, _ in flattened]) for name in flattened[0][0])
    )
    id_name = RECORD_ID
    suffix = 2
    while id_name in all_fields:
        id_name = f"{RECORD_ID}_{suffix}"
        suffix += 1
    rows: list[dict[str, Any]] = []
    for position, ((fields, lists), count, indices) in enumerate(zip(flattened, points, kept, strict=True), start=1):
        base = {id_name: position, **fields} if numbered else fields
        if count == 0:
            rows.append({**base, **dict.fromkeys(lists)})
            continue
        for at in indices:
            rows.append({**base, **{name: values[at] if values else None for name, values in lists.items()}})
    expanded = dict.fromkeys(name for _, record_lists in flattened for name in record_lists)
    names = ", ".join(_clip(name, MAX_COLUMN_NAME_CHARS) for name in expanded)
    paired = " (lists of one record are paired by position)" if len(expanded) > 1 else ""
    warnings.append(f"list fields expanded into one row per value{paired}: {names}")
    if numbered:
        warnings.append(f"column '{id_name}' added: it numbers the records, so the rows of each stay together")
    total = sum(points)
    if sum(len(indices) for indices in kept) < sum(max(count, 1) for count in points):
        remedy = "paste fewer points" if len(flattened) == 1 else "paste fewer records or fewer points per record"
        warnings.append(
            f"the lists hold {total:,} values, more than the {MAX_ROWS:,} rows a table may have: "
            f"{sum(len(indices) for indices in kept):,} evenly spaced values are kept, the first and last of each "
            f"record among them; {remedy} to keep every value"
        )
    return rows


def _thinned(points: Sequence[int]) -> list[list[int]]:
    """For each record of `points` values, the positions kept so all rows fit `MAX_ROWS`: evenly spaced, both ends kept.

    Every position while everything fits. Otherwise each record keeps about one in k of its
    values, the smallest k that fits, always its first and its last one (a curve keeps its
    range); a record of no values still takes one row. When even two values per record do not
    fit, the data is `too_many_rows`.
    """

    def keep(count: int, step: int) -> int:
        return min(count, max(math.ceil(count / step), 2)) if count else 1

    if sum(max(count, 1) for count in points) <= MAX_ROWS:
        return [list(range(count)) for count in points]
    if sum(keep(count, max(points)) for count in points) > MAX_ROWS:
        raise ParseError(
            "too_many_rows", f"the lists give more than {MAX_ROWS:,} rows, even with two values per record"
        )
    low, high = 2, max(points)  # the kept rows shrink as the step grows: the smallest step that fits, by halving
    while low < high:
        middle = (low + high) // 2
        if sum(keep(count, middle) for count in points) > MAX_ROWS:
            low = middle + 1
        else:
            high = middle
    step = low
    kept: list[list[int]] = []
    for count in points:
        size = keep(count, step) if count else 0
        if size <= 1:
            kept.append(list(range(size)))
            continue
        kept.append(sorted({round(index * (count - 1) / (size - 1)) for index in range(size)}))
    return kept


def _tells_apart(name: str, records: Sequence[Mapping[str, Any]]) -> bool:
    """Whether the field `name` identifies the records: text or whole numbers, every record a different value.

    Decided on the values as `data.csv` will hold them (review of 2026-10-15): `A` and `A ` or
    `NA` and `N/A` clean to the same cell and do not tell two curves apart. A number with a
    fraction (a temperature, a mass) is a measurement, never an identifier, even when unique;
    so is a boolean.
    """
    cells: list[str] = []
    for record in records:
        value = record.get(name)
        if isinstance(value, bool) or not isinstance(value, (str, int)):
            return False
        cell = str(value) if isinstance(value, int) else _clean_cell(value)[0]
        if not cell:
            return False
        cells.append(cell)
    return len(set(cells)) == len(cells)


def _flat_records(
    records: Sequence[Mapping[Any, Any]], warnings: list[str]
) -> tuple[list[str], list[list[str]], SourceFormat]:
    keys: dict[Any, int] = {}
    for record in records:
        for key in record:
            if key not in keys:
                keys[key] = len(keys)
                if len(keys) > MAX_RAW_COLUMNS:
                    raise ParseError("too_many_columns", f"the data has more than {MAX_RAW_COLUMNS} columns")
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
    if len(data) > MAX_RAW_COLUMNS:
        raise ParseError(
            "too_many_columns", f"the data has {len(data)} columns; at most {MAX_COLUMNS} with values are supported"
        )
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
    if isinstance(value, _SourceFloat) and _FLOAT.fullmatch(value.text):
        return value.text  # every written digit: a JSON number's text is a dot-decimal number already
    if isinstance(value, float):
        return repr(value) if math.isfinite(value) else ""
    if isinstance(value, str):
        return _json_text(value, f"a value in column {position + 1}")
    raise ParseError(
        "unparseable", f"column {position + 1} holds nested values; only text, numbers, booleans and null are supported"
    )


# --- JSON-stat ---------------------------------------------------------------------------


def _json_stat_dataset(data: Any) -> dict[Any, Any] | None:
    """The JSON-stat dataset in `data`, None when `data` is no JSON-stat document.

    A JSON-stat 2.0 dataset is an object with a `dimension` object and a `value`, marked by
    `"class": "dataset"` or, as in some 1.x-style responses, by a top-level `id`. A JSON-stat 1.x
    bundle (`{"<name>": {"dimension": ..., "value": ...}}`) yields its dataset when it holds one.
    A 2.0 collection or dimension, or a bundle of several datasets, holds no single table:
    `unparseable`. Anything else (`{"class": "a"}` is an object of values) is None and goes to
    `_tabulate` as before.
    """
    if not isinstance(data, dict) or not data:
        return None
    kind = data.get("class")
    if isinstance(data.get("dimension"), dict) and "value" in data and (kind == "dataset" or "id" in data):
        return data
    if kind == "collection" and isinstance(data.get("link"), dict):
        raise ParseError("unparseable", "a JSON-stat collection lists datasets but holds no values; paste one dataset")
    if kind == "dimension" and isinstance(data.get("category"), dict):
        raise ParseError("unparseable", "a JSON-stat dimension holds no values; paste a dataset")
    if all(
        isinstance(entry, dict) and isinstance(entry.get("dimension"), dict) and "value" in entry
        for entry in data.values()
    ):
        if len(data) > 1:
            raise ParseError(
                "unparseable", f"the JSON-stat bundle holds {len(data)} datasets; paste one dataset at a time"
            )
        (only,) = data.values()
        return dict(only)
    return None


def _json_stat_refusal(reason: str) -> ParseError:
    return ParseError("unparseable", f"the JSON-stat dataset is inconsistent: {reason}")


def _json_stat(
    dataset: Mapping[Any, Any], warnings: list[str], context: list[str]
) -> tuple[list[str], list[list[str]], SourceFormat]:
    """A JSON-stat dataset as a long table: one column per dimension with more than one category, then `value`.

    Every check comes before the rows are built: `id` and `size` name the dimensions in the
    same order (a 1.x dataset keeps both inside `dimension`), the product of the sizes is at
    most `MAX_ROWS` and equals the number of values (`value` as an array, or as a sparse
    object of positions whose missing ones are empty), and every dimension lists as many
    categories as its size (`category.index` as an array of codes or an object of code to
    position; a dimension of one category may give only `category.label`).

    A dimension's column is named by its `label` (else its id), its cells are the category
    labels (else the codes), cleaned like the keys of `json_pairs` and kept text: `NA`
    (Namibia) or `2024` is a name, never a missing cell or a number, and only `value` is
    typed. A label shared by two categories in that cleaned form gets its code in
    parentheses, with a warning. The rows run row-major over `id`, the order of `value`.
    The value column is `value` whatever the dataset's units, and a dimension named
    `value` in any case is renamed `<label> (dimension)` so the measure keeps the name: a measure dimension (`metric`, or a
    component such as births and deaths) stays a column of the long table, which
    `prepare_data` can pivot later. A dimension of one category is the same in every row,
    so it is no column: `<label>: <category>` joins the dataset's `label`, `source` and
    `note` lines in `context`, the notes the user pasted with the data, which the route
    screens before any model reads them; the warning gives only their count. `status`
    symbols are ignored, with one warning.
    """
    dimension = dataset["dimension"]
    ids = dataset["id"] if "id" in dataset else dimension.get("id")
    sizes = dataset["size"] if "size" in dataset else dimension.get("size")
    if not isinstance(ids, (list, tuple)) or not ids or not all(isinstance(name, str) for name in ids):
        raise _json_stat_refusal("`id` must be a list of dimension names")
    if len(set(ids)) != len(ids):
        raise _json_stat_refusal("`id` names a dimension twice")
    if len(ids) > MAX_COLUMNS:
        raise ParseError(
            "too_many_columns", f"the dataset has {len(ids)} dimensions; at most {MAX_COLUMNS} are supported"
        )
    if not isinstance(sizes, (list, tuple)) or len(sizes) != len(ids):
        raise _json_stat_refusal("`size` must give one size per dimension in `id`")
    if not all(type(size) is int and size >= 1 for size in sizes):
        raise _json_stat_refusal("every size must be a whole number of at least 1")
    total = 1
    for size in sizes:
        total *= size
        if total > MAX_ROWS:
            raise ParseError("too_many_rows", f"the data has more than {MAX_ROWS:,} rows")

    headers: list[str] = []
    categories: list[list[str]] = []
    constants: list[str] = []
    for position, (name, size) in enumerate(zip(ids, sizes, strict=True), start=1):
        header, cells, relabelled = _json_stat_dimension(dimension.get(name), name, size, position)
        if size == 1:
            constants.append(f"{header}: {cells[0]}")
            continue
        if (cleaned := _key_form(_clean_header(header)[0])).casefold() == PAIR_HEADERS[1]:
            # `value` is the measure's name: a dimension labelled so would take it, or sit
            # next to it as `Value`, and the measure would become `value_2` or lose its binding.
            header = f"{cleaned} (dimension)"
            warnings.append(f"column '{header}': a dimension named like the value column renamed")
        headers.append(header)
        categories.append(cells)
        if relabelled:
            warnings.append(
                f"column '{_clip(header, MAX_COLUMN_NAME_CHARS)}': labels shared by two categories carry their codes"
            )
    headers.append(PAIR_HEADERS[1])
    values = _json_stat_values(dataset.get("value"), total, len(headers) - 1)

    if dataset.get("status"):
        warnings.append("the dataset's status symbols (such as provisional or estimated) are ignored")
    if constants:
        warnings.append(
            f"{_count(len(constants), 'dimension')} with a single category left out of the columns; "
            "the notes name each one with its category"
        )
    notes: list[str] = []
    for key, what in (("label", "the dataset's label"), ("source", "the dataset's source")):
        if isinstance(dataset.get(key), str) and dataset[key].strip():
            text = _json_text(dataset[key], what)
            notes.append(text if key == "label" else f"Source: {text}")
    note = dataset.get("note")
    for line in note if isinstance(note, (list, tuple)) else [note]:
        if isinstance(line, str) and line.strip():
            notes.append(_json_text(line, "a note of the dataset"))
    notes.extend(constants)
    lines, cut = _context_lines([[line] for line in notes], None)
    context.extend(lines)
    if cut:
        warnings.append(f"the dataset's notes were cut at {MAX_CONTEXT_CHARS:,} characters")

    rows = [[*combination, value] for combination, value in zip(product(*categories), values, strict=True)]
    return headers, rows, "json_stat"


def _json_stat_dimension(entry: Any, name: str, size: int, position: int) -> tuple[str, list[str], bool]:
    """A dimension's column name and its category labels in index order; whether codes were added to labels."""
    where = f"dimension {position} of `id`"
    if not isinstance(entry, dict) or not isinstance(entry.get("category"), dict):
        raise _json_stat_refusal(f"{where} has no `category` object")
    category = entry["category"]
    index, labels = category.get("index"), category.get("label")
    if labels is not None and not isinstance(labels, dict):
        raise _json_stat_refusal(f"the `category.label` of {where} must be an object")
    codes: list[Any]
    if index is None:
        if size != 1 or not isinstance(labels, dict) or len(labels) != 1:
            raise _json_stat_refusal(f"{where} has no `category.index`")
        codes = list(labels)
    elif isinstance(index, (list, tuple)):
        codes = list(index)
    elif isinstance(index, dict):
        positions = list(index.values())
        if not all(type(at) is int for at in positions) or sorted(positions) != list(range(len(positions))):
            raise _json_stat_refusal(f"the `category.index` of {where} must number its categories from 0")
        codes = sorted(index, key=index.__getitem__)
    else:
        raise _json_stat_refusal(f"the `category.index` of {where} must be a list or an object")
    if not all(isinstance(code, str) for code in codes) or len(set(codes)) != len(codes):
        raise _json_stat_refusal(f"the categories of {where} must be distinct text codes")
    if len(codes) != size:
        raise _json_stat_refusal(f"{where} has {len(codes)} categories where `size` gives {size}")
    cells: list[str] = []
    for code in codes:
        label = labels.get(code) if labels else None
        if label is not None and not isinstance(label, str):
            raise _json_stat_refusal(f"a category label of {where} is not text")
        cells.append(_key_form(_json_text(code if label is None else label, f"a category of {where}")))
    # Compared in the form `_build` writes (`_clean_key`, NFC), so `Other` and `Other` behind a
    # zero-width space, which would be one category in `data.csv`, count as shared too.
    relabelled = len(set(cells)) != len(cells)
    if relabelled:
        cells = [f"{cell} ({code})" for cell, code in zip(cells, codes, strict=True)]
    title = entry.get("label")
    header = title if isinstance(title, str) and title.strip() else name
    return _json_text(header, f"the name of {where}"), cells, relabelled


def _key_form(text: str) -> str:
    """A category or a dimension name as `data.csv` holds it: cleaned like a key (`_clean_key`), in NFC."""
    return unicodedata.normalize("NFC", _clean_key(text)[0])


def _json_stat_values(raw: Any, total: int, position: int) -> list[str]:
    """The cells of the value column: an array of `total` values, or a sparse object of positions to values."""
    if isinstance(raw, (list, tuple)):
        if len(raw) != total:
            raise _json_stat_refusal(f"`value` holds {len(raw):,} values where `size` gives {total:,}")
        pairs: Iterable[tuple[int, Any]] = enumerate(raw)
    elif isinstance(raw, dict):
        located: list[tuple[int, Any]] = []
        for key, value in raw.items():
            at = int(key) if isinstance(key, str) and _INTEGER_INDEX.fullmatch(key) else key
            if type(at) is not int or not 0 <= at < total:
                raise _json_stat_refusal("a key of the `value` object is no position within `size`")
            located.append((at, value))
        pairs = located
    else:
        raise _json_stat_refusal("`value` must be an array or an object of positions")
    cells = [""] * total
    for at, value in pairs:
        if not _scalar(value):
            raise _json_stat_refusal("a value is nested; only text, numbers and null are supported")
        cells[at] = _json_cell(value, position)
    return cells


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
    text, invisible = _clean_key(raw)
    return ("" if text in MISSING_VALUES else text), invisible


def _clean_key(raw: str) -> tuple[str, bool]:
    """A pair key (`json_pairs` category) is a name: cleaned like a cell, but `NA` or `null` stays text.

    A cell of canonical CSV (`parse_dataset(canonical=True)`) is cleaned the same way: there the
    empty cell is the only missing one."""
    text, invisible, _ = _cleaned(raw)
    return text, invisible


def _cleaned(raw: str) -> tuple[str, bool, bool]:
    """The cleaned cell, whether invisible characters went, and whether surrounding whitespace went.

    A cell of nothing but whitespace is empty, not trimmed: it was blank to begin with.
    """
    text, invisible = _strip_invisible(raw)
    unstripped = text.replace("\r\n", "\n").replace("\r", "\n")
    stripped = unstripped.strip()
    return stripped, invisible, bool(stripped) and stripped != unstripped


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
       `YYYY-MM-DD[(T| )HH:MM[:SS[.fraction]][offset]]` (`_as_iso_stamps`: up to nine
       fraction digits and the offset kept as written), `DD.MM.YYYY`, or `DD/MM/YYYY` / `MM/DD/YYYY`,
       the last three with an optional ` HH:MM[:SS]` and one- or two-digit day and
       month. A slash column is day-first when a first part exceeds 12, month-first
       when a second part does, not a date when both happen, and day-first with a
       warning when neither does. Written as `YYYY-MM-DD`, or `YYYY-MM-DDTHH:MM:SS`
       for the whole column when any cell has a time.
    2. **boolean**: `true` / `false` in any letter case, written `True` / `False`.
    3. **integer**: ASCII digits with an optional sign within int64. A column with a
       leading zero (`007`) stays text, because the zeros are part of the value, and so
       does a column with a whole number past int64 (`BIG_INTEGERS`): a float64 would
       round its last digits.
    4. **number**: dot decimals with an optional exponent, written in Python's
       shortest round-trip form (the value is kept, not the spelling: `1.50` is `1.5`;
       a cell with more digits than a float64 holds is counted, `rounded_note`); then decimal commas when every cell has the
       `1.234,56` or `1234,56` shape and at least one has a comma. Dates were tried
       first, so `DD.MM.YYYY` never reads as a thousands-dot number. Then numbers whose
       thousands are grouped unambiguously by a dot, a comma, an apostrophe or a space
       (`_as_grouped_numbers`).
    5. **integer or number with a unit**: every cell is a number next to one unit
       that all cells share (`65 %`, `15,6 h`, `€ 5`, see `_split_units`), and the
       number parts pass rules 3 and 4 (so `007 kg` keeps its text). The cells keep
       the number; the unit goes into the column name, see `canonical_headers`.
    6. **text**: everything else, every column without a non-missing cell, the
       `category` column of `json_pairs`, whose cells are the keys, and every dimension
       column of `json_stat`, whose cells are category labels or codes (`text_only`).
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
        # Past int64 a whole number only fits a float64, which keeps 15 to 17 digits: an id or a count
        # of 20 digits would lose its last ones. Text keeps every digit; `set_type number` can still read it.
        column.notes.append(BIG_INTEGERS)
        return False
    if all(_FLOAT.fullmatch(cell) for cell in present):
        return _as_numbers(column, cells)
    if all(_DECIMAL_COMMA.fullmatch(cell) for cell in present) and any("," in cell for cell in present):
        if _as_numbers(column, [cell.replace(".", "").replace(",", ".") for cell in cells]):
            column.decimal_comma = True
            commas = [cell for cell in present if "," in cell]
            if all(_AMBIGUOUS_COMMA.fullmatch(cell) for cell in commas) and not any("." in cell for cell in present):
                column.notes.append(AMBIGUOUS_COMMAS)
            return True
    return _as_grouped_numbers(column, cells, present)


AMBIGUOUS_COMMAS = "commas read as decimal commas; remove them first if they separate thousands"
"""The note of a column whose commas could be decimals or thousands (`1,234`); `_commas_as_thousands` replaces it."""

BIG_INTEGERS = "whole numbers beyond the 64-bit range kept as text, so no digit is lost"
"""The note of an integer column with a value past int64, which a number column could hold only rounded."""


RESPELLED = "written in another form with the same value"
"""The heart of the one warning that counts numbers whose value stayed but whose spelling did not (`_respelled`)."""


def rounded_note(count: int) -> str:
    """The note of a number column whose cells hold more significant digits than a float64 keeps."""
    return (
        f"{_count(count, 'value')} with more significant digits than a number holds (15 to 17) "
        f"{'is' if count == 1 else 'are'} stored rounded to the nearest number"
    )


def _as_grouped_numbers(column: _Column, cells: list[str], present: list[str]) -> bool:
    """Numbers whose thousands are grouped by a mark the rules above do not read (live test of 2026-10-15).

    A semicolon file with decimal commas wrote its population as `7.184.003`, which no rule
    above takes (a dot-decimal number has one dot, a decimal-comma one a comma), so the column
    stayed text. A column reads as grouped numbers when every cell is a number whose
    thousands are separated by one mark of `GROUP_MARKS` in groups of three (or a plain
    number), at least one cell carries the mark, and the grouping is unambiguous:

    * a dot or a comma: some cell holds two or more groups (`7.184.003`, `1,234,567`), or a
      comma group stands before a dot decimal (`1,234.5`); then a one-group cell such as
      `999.123` of the same column is grouped too. One group alone (`1.234`, `1,234`) stays
      with the rules above, which read it as a decimal (and `_retype_thousands_dots` or
      `_commas_as_thousands` settles it from the file's other columns);
    * an apostrophe (Swiss `1'234'567`, also `’`) or a space (also no-break, narrow no-break
      or thin): some cell holds two or more groups or a decimal part (`1'234.5`), since a
      single group without one is as often an id, a phone number or an article number
      (`123 456`) as a number (review of 2026-10-15).

    The decimal mark is the other one of dot and comma, the same in every cell. Dates were
    tried first, so `01.02.2024` never gets here; `0.125` is no group (a group never starts
    with a zero). Without a decimal the column is integers. A cell of four dot groups each at
    most 255 (`192.168.100.200`, an IPv4 address) keeps the column text, and so does a column
    whose name says it holds ids, codes, versions or phone numbers (`_id_like`). The mark is
    recorded (`_Column.group_mark`): it is evidence for the file's other columns.
    """
    if column.id_like:
        return False
    for mark, label in GROUP_MARKS.items():
        pattern = _GROUPED[mark]
        matches = [pattern.fullmatch(cell) for cell in present]
        if not all(matches) or not any(mark in cell for cell in present):
            continue
        decimals = {match["decimal"] for match in matches if match and match["decimal"]}
        if len(decimals) > 1 or mark in decimals:
            continue
        decimal = decimals.pop() if decimals else None
        several = any(cell.count(mark) >= 2 for cell in present)
        if mark in ".," and not (several or (mark == "," and decimal == ".")):
            continue
        if mark not in ".," and not (several or decimal):
            continue
        if mark == "." and any(_IPV4.fullmatch(cell) for cell in present):
            continue
        bare = [cell.replace(mark, "").replace(",", ".") if cell else "" for cell in cells]
        if not (_as_numbers(column, bare) if decimal else _as_integers(column, bare)):
            if not decimal:  # a whole number past int64: text keeps every digit, and says why
                column.notes.append(BIG_INTEGERS)
            return False
        column.decimal_comma = decimal == ","
        column.group_mark = mark
        column.notes.append(f"{label} read as thousands separators")
        return True
    return False


def _id_like(name: str) -> bool:
    """Whether a column name says its cells are ids, codes, versions or phone numbers, never quantities."""
    words = set(_NAME_WORDS.findall(name.casefold()))
    return bool(words & ID_WORDS) or any(name.casefold().endswith(suffix) for suffix in ("_id", "-id", "id_"))


def _commas_as_thousands(columns: list[_Column]) -> None:
    """A column of `1,234` shapes reads by what the file's other columns settle, else keeps its decimal comma.

    A column whose commas could be decimals or thousands (every cell a whole number or `1,234`,
    typed as decimal commas with the `AMBIGUOUS_COMMAS` note) is settled only by strong evidence
    (review of 2026-10-15: a dot number elsewhere is none, since `12.30` may be a time and a
    rating of `4.5` says nothing about a price of `1,250`):

    * another column writes a decimal comma that is no such shape (`6,07`): the decimal comma
      stays and the note goes, so the root asks no question the file answers (live test of
      2026-10-15, `43,621` Mio. t beside `6,07` t);
    * otherwise, another column groups its thousands with commas unambiguously (`1,234,567`,
      `1,234.5`, `_as_grouped_numbers`): the column reads as whole numbers with comma
      thousands, with a note.

    Without either the decimal comma stays with its note. A column named as an id or a code
    (`_id_like`) is never retyped.
    """
    ambiguous = [column for column in columns if column.decimal_comma and AMBIGUOUS_COMMAS in column.notes]
    if not ambiguous:
        return
    if any(column.decimal_comma and column not in ambiguous and column.group_mark != "," for column in columns):
        for column in ambiguous:
            column.notes.remove(AMBIGUOUS_COMMAS)
        return
    if not any(column.group_mark == "," for column in columns):
        return
    for column in ambiguous:
        if column.id_like or not all(_COMMA_GROUP.fullmatch(cell) for cell in column.bare if cell):
            continue
        if _as_integers(column, [cell.replace(",", "") for cell in column.bare]):
            column.decimal_comma = False
            column.notes.remove(AMBIGUOUS_COMMAS)
            column.notes.append("commas read as thousands separators, as in the file's other columns")


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


def _retype_thousands_dots(column: _Column, *, decimal_comma: bool) -> None:
    """In a file with decimal commas, or with a column of unambiguous dot groups (`7.184.003`), a dot-number
    column of `1.234` shapes holds thousands separators; `decimal_comma` says the file writes decimal commas.
    A column named as an id, a code or a version (`_id_like`) is never retyped."""
    present = [cell for cell in column.bare if cell]
    if column.id_like or not (
        all(_THOUSANDS_DOT.fullmatch(cell) for cell in present) and any("." in cell for cell in present)
    ):
        return
    cells = [cell.replace(".", "") for cell in column.bare]
    if not _as_integers(column, cells):
        # Every cell is a whole number (`_THOUSANDS_DOT`), one past int64: text keeps every digit, as rule 3 does.
        column.dtype, column.cells, column.numbers, column.unit = "text", list(column.source), [], None
        column.rounded = column.respelled = 0
        column.notes.append(BIG_INTEGERS)
        return
    column.decimal_comma = decimal_comma
    column.notes.append("dots read as thousands separators, as in the file's other columns")


def _as_integers(column: _Column, cells: list[str]) -> bool:
    values = [int(cell) if cell else None for cell in cells]
    if any(value is not None and not _INT64_MIN <= value <= _INT64_MAX for value in values):
        return False
    column.dtype = "integer"
    column.cells = ["" if value is None else str(value) for value in values]
    column.integers = [value for value in values if value is not None]
    column.numbers = [float(value) for value in column.integers]
    column.rounded = 0
    column.respelled = sum(1 for cell, text in zip(cells, column.cells, strict=True) if cell != text)  # `+3`, `-0`
    return True


def _as_numbers(column: _Column, cells: list[str]) -> bool:
    """The dot-decimal `cells` as floats, written in their shortest round-trip form (`repr`).

    The value is what counts, not the spelling: `1.50`, `1.5e0` and `+1.5` are all `1.5`. A
    cell whose value a float64 does not hold (more than about 15 to 17 significant digits,
    `0.1234567890123456789`, or a whole number past 2**53 beside decimals) is counted in
    `_Column.rounded`, and `_build` warns about it (owner rule of 2026-10-15: precision is
    never lost silently). A cell that keeps its value but not its spelling (`respelled`) is
    counted too, for a note (owner decision of 2026-10-15).
    """
    values = [float(cell) if cell else None for cell in cells]
    finite = [value for value in values if value is not None]
    if not all(math.isfinite(value) for value in finite):
        return False
    column.dtype = "number"
    column.cells = [
        "" if value is None else number_text(cell, value) for cell, value in zip(cells, values, strict=True)
    ]
    column.numbers = finite
    column.integers = []
    kept = [
        (cell, text, keeps_value(cell, value))
        for cell, text, value in zip(cells, column.cells, values, strict=True)
        if value is not None
    ]
    column.rounded = sum(1 for _, _, same in kept if not same)
    column.respelled = sum(1 for cell, text, same in kept if same and _respelled(cell, text))
    return True


def number_text(written: str, value: float) -> str:
    """The canonical text of a cell of a number column: `repr`, except a whole number written without a fraction.

    `87000` beside `120500.5` stays `87000` (live test round 5 of 2026-10-15: it showed as
    `87000.0` in the preview and in `data.csv`, a representation the user never wrote); `2.0`
    stays `2.0`, and `1e3` is `1000.0` as before. A whole number a float64 holds only rounded
    (past 2**53) keeps the `repr` that shows it, which the rounding note counts.
    """
    text = repr(value)
    if _INTEGER.fullmatch(written) and text.endswith(".0") and keeps_value(written, value):
        return text[:-2]
    return text


def _respelled(written: str, canonical: str) -> bool:
    """Whether the canonical text of a number of the same value drops what the written one showed.

    Trailing zeros of a fraction (`1.50` as `1.5`, `2.00` as `2.0`), scientific notation
    (`1e3` as `1000.0`, or a long plain number as `1.2e+20`) and a plus sign (`+1.5`). What
    the canonical form only adds (`2` as `2.0`, `.5` as `0.5`, `1e-7` as `1e-07`) is no loss.
    """
    mantissa, _, exponent = written.lower().partition("e")
    canonical_mantissa, _, canonical_exponent = canonical.partition("e")
    if bool(exponent) != bool(canonical_exponent) or mantissa.startswith("+"):
        return True
    fraction = mantissa.partition(".")[2]
    return fraction.endswith("0") and len(fraction) > len(canonical_mantissa.partition(".")[2])


_FLOAT_DIGITS = 15
"""Every decimal of at most this many significant digits survives a float64 and its `repr` (`DBL_DIG`)."""


def keeps_value(text: str, value: float) -> bool:
    """Whether the finite float `value` read from the dot-decimal number `text` has exactly the value of `text`.

    `1.50` and `1.5` are the same value, so are `1e3` and `1000.0`; `0.1234567890123456789`
    (19 digits) and `9007199254740993` (2**53 + 1) are not, since a float64 keeps 15 to 17
    significant digits. A short number is decided by its digit count; a long one, or one so
    small that the float is subnormal, by comparing the decimal values exactly.
    """
    mantissa = text.lower().partition("e")[0]
    digits = mantissa.lstrip("+-").replace(".", "").lstrip("0")
    if len(digits) <= _FLOAT_DIGITS and (abs(value) >= sys.float_info.min or (value == 0 and not digits)):
        return True
    try:
        return Decimal(text) == Decimal(repr(value))
    except InvalidOperation:
        return False


def _match_all(pattern: re.Pattern[str], cells: list[str]) -> dict[str, tuple[int, ...]] | None:
    """Each distinct cell's date and time fields as integers (an absent time is 0), or None on a miss."""
    fields: dict[str, tuple[int, ...]] = {}
    for cell in cells:
        match = pattern.fullmatch(cell)
        if match is None:
            return None
        fields[cell] = tuple(int(part) if part else 0 for part in match.groups())
    return fields


def _as_iso_stamps(column: _Column, present: list[str]) -> bool | None:
    """ISO dates and timestamps with every digit and the offset as written (owner rule of 2026-10-15).

    None when a cell is no ISO date, so the other formats are tried. A fraction of up to nine
    digits stays (each cell padded to the column's longest fraction, which changes no value and
    lets `pd.read_csv(parse_dates=...)` read the column as one format), and so does an offset
    (`Z`, `+01`, `+0100`, `+01:00`, written `+01:00`; `Z` as `+00:00`). A column that mixes
    cells with and without an offset is not a date column: no time is given a zone by guess.
    A column with several offsets (summer and winter time) is written in UTC (`+00:00`) with a
    note naming the offsets, because pandas reads one offset per column; the instants stay.
    """
    matches = []
    for cell in present:
        match = _ISO_STAMP.fullmatch(cell)
        if match is None:
            return None
        matches.append((cell, match))
    offsets: dict[str, int | None] = {}
    stamps: dict[str, tuple[datetime, str]] = {}
    for cell, match in matches:
        year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
        hour, minute, second = (int(match.group(index) or 0) for index in (4, 5, 6))
        fraction, offset = match.group(7) or "", match.group(8)
        try:
            stamp = datetime(year, month, day, hour, minute, second, int((fraction + "000000")[:6]))
        except ValueError:
            return False
        minutes: int | None = None
        if offset is not None:
            digits = offset[1:].replace(":", "") if offset != "Z" else "0000"
            minutes = int(digits[:2]) * 60 + int(digits[2:4] or 0)
            if minutes >= 24 * 60:
                return False
            minutes = -minutes if offset.startswith("-") else minutes
            stamp = stamp.replace(tzinfo=timezone(timedelta(minutes=minutes)))
        offsets[cell] = minutes
        stamps[cell] = (stamp, fraction)
    zones = set(offsets.values())
    if None in zones and len(zones) > 1:
        return False
    mixed = len(zones) > 1
    if mixed:
        shown = ", ".join(_offset_text(value) for value in sorted(zone for zone in zones if zone is not None))
        column.notes.append(f"times with the UTC offsets {shown} written in UTC (+00:00); the instants are the same")
    digits = max((len(fraction) for _, fraction in stamps.values()), default=0)
    if digits > 6 and any(not _NS_RANGE[0] <= _naive_utc(stamp) <= _NS_RANGE[1] for stamp, _ in stamps.values()):
        # pandas holds a nanosecond only between 1677 and 2262: the loader's `parse_dates` would leave such a
        # column text without a word (review of #12196), so it is text here, said, with every digit.
        column.notes.append(NS_OUT_OF_RANGE)
        return False
    column.with_time = any(":" in cell for cell in present)
    texts: dict[str, str] = {}
    for cell, (stamp, fraction) in stamps.items():
        if mixed:
            stamp = stamp.astimezone(timezone.utc)
        if not column.with_time:
            texts[cell] = stamp.date().isoformat()
            continue
        text = stamp.replace(microsecond=0, tzinfo=None).isoformat(timespec="seconds")
        if digits:
            text += "." + fraction.ljust(digits, "0")
        if stamp.tzinfo is not None:
            text += _offset_text(0 if mixed else offsets[cell])
        texts[cell] = text
    column.dtype = "datetime"
    column.dates = [stamps[cell][0] for cell in column.source if cell]
    column.date_texts = [texts[cell] for cell in column.source if cell]
    column.date_rests = [int((stamps[cell][1] + "000000000")[6:9]) for cell in column.source if cell]
    column.cells = [texts[cell] if cell else "" for cell in column.source]
    return True


NS_OUT_OF_RANGE = (
    "kept as text: times with fractions below a microsecond can be read as dates only between 1677 and 2262, "
    "and this column has a date outside that range"
)
_NS_RANGE = (datetime(1677, 9, 22), datetime(2262, 4, 11))
"""The moments a pandas `datetime64[ns]` holds, a day inside each end so an offset never crosses them."""


def _naive_utc(stamp: datetime) -> datetime:
    """The moment in UTC without its zone; at the ends of the calendar (year 1 or 9999) the wall time itself."""
    if stamp.tzinfo is None:
        return stamp
    try:
        return stamp.astimezone(timezone.utc).replace(tzinfo=None)
    except OverflowError:
        return stamp.replace(tzinfo=None)


def _offset_text(minutes: int | None) -> str:
    """An offset in minutes as `+HH:MM`."""
    value = minutes or 0
    sign = "-" if value < 0 else "+"
    hours, rest = divmod(abs(value), 60)
    return f"{sign}{hours:02d}:{rest:02d}"


def _as_dates(column: _Column, present: list[str]) -> bool:
    stamped = _as_iso_stamps(column, present)
    if stamped is not None:
        return stamped
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
    *,
    canonical: bool = False,
    context: list[str] | None = None,
    missing_marks: frozenset[str] = frozenset(),
    listed: frozenset[str] = frozenset(),
) -> ParsedDataset:
    read: list[tuple[str, bool, _Column]] = []  # header, whether breaks became spaces, column
    for position, raw in enumerate(raw_headers):
        header, invisible, broken = _clean_header(raw)
        # The keys of an object of values are names, and so are JSON-stat categories (every column but
        # the last, the measure): `NA` (Namibia), `-` or `2024` stay text, untyped and never missing.
        text_only = (source_format == "json_pairs" and position == 0) or (
            source_format == "json_stat" and position < len(raw_headers) - 1
        )
        cells: list[str] = []
        na_rows: list[int] = []
        mark_rows: list[int] = []
        trimmed = 0
        tokens: Counter[str] = Counter()
        mark_tokens: Counter[str] = Counter()
        for row_index, row in enumerate(raw_rows):
            text, cell_invisible, cell_trimmed = _cleaned(row[position])
            trimmed += cell_trimmed
            if text_only or canonical:
                cell = text
            else:
                cell = "" if text in MISSING_VALUES else text
                if text and not cell:
                    tokens[text] += 1
                if text == NA_TOKEN:
                    na_rows.append(row_index)
                if missing_marks and _matches_mark(text, missing_marks):
                    mark_rows.append(row_index)
                    if text and not cell:
                        mark_tokens[text] += 1
            cells.append(cell)
            invisible = invisible or cell_invisible
        if not header and not any(cells):
            continue
        column = _Column(
            name="",
            source=cells,
            cells=[],
            invisible=invisible,
            text_only=text_only,
            na_rows=na_rows,
            mark_rows=mark_rows,
            trimmed=trimmed,
            missing_tokens=tokens,
            mark_tokens=mark_tokens,
            from_list=raw in listed,
        )
        read.append((header, broken, column))

    dropped = len(raw_headers) - len(read)
    if dropped:
        warnings.append(f"{_count(dropped, 'empty column')} without a header dropped")
    if not canonical:
        read = _without_empty_columns(read, warnings)
        if source_format in _DELIMITED:
            read = _without_row_names(read, warnings)
    headers = [header for header, _, _ in read]
    columns = [column for _, _, column in read]
    renamed_by_breaks = [index for index, (_, broken, _) in enumerate(read) if broken]
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
    marked = 0
    for index, (header, column) in enumerate(zip(headers, columns, strict=True)):
        if text_columns and plain_names[index] in text_columns:
            column.cells = list(column.source)  # kept text by request: the cells as cleaned, never typed
        else:
            column.id_like = _id_like(header)
            marked += _blank_marks(column)
            _type_column(column)
    if marked:
        warnings.append(
            f"{_count(marked, 'cell')} of number or date columns matched the missing-value mark the notes declare "
            "and are empty"
        )
    _commas_as_thousands(columns)
    decimal_comma = any(column.decimal_comma for column in columns)
    if decimal_comma or any(column.group_mark == "." for column in columns):
        for column in columns:
            if column.dtype == "number" and not column.decimal_comma:
                _retype_thousands_dots(column, decimal_comma=decimal_comma)
    for column in columns:
        _keep_na_codes(column)
        _fidelity_notes(column, layout_padding=source_format == "whitespace")

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
    respelled = [column for column in columns if column.dtype in ("integer", "number") and column.respelled]
    if respelled:
        # One line for the file, not one per column: a price list writes every `12.50` so (owner decision of 2026-10-15).
        total = sum(column.respelled for column in respelled)
        named = ", ".join(column.name for column in respelled[:MAX_NAMED_FIELDS])
        more = ", …" if len(respelled) > MAX_NAMED_FIELDS else ""
        warnings.append(
            f"{_count(total, 'number')} {RESPELLED} (trailing zeros, exponent or plus sign dropped, "
            f"such as 1.50 as 1.5 or 1e3 as 1000.0) in {named}{more}"
        )

    full = _finish(columns, source_format, warnings, text_columns)
    if canonical or source_format == "json_stat" or context is None:
        return full
    notes_before = list(context)
    kept = _constants_to_notes(columns, len(raw_rows), text_columns, warnings, context)
    if kept is columns:
        return full
    # The table with its constant columns stays at hand: when the notes are not kept, they become columns again.
    return replace(
        _finish(kept, source_format, warnings, text_columns), with_constants=replace(full, context_lines=notes_before)
    )


def _finish(
    columns: list[_Column], source_format: SourceFormat, warnings: list[str], text_columns: frozenset[str]
) -> ParsedDataset:
    """The dataset of these typed and named columns: canonical CSV, profile, preview and the loader's typing."""
    rows = [list(row) for row in zip(*(column.cells for column in columns), strict=True)]
    capped = _cap_warnings(warnings)
    listed = [column.name for column in columns if column.from_list]
    profile = DatasetProfile(
        rows=len(rows),
        columns=[_profile_column(column) for column in columns],
        sample=[[_clip(cell) for cell in row] for row in rows[:MAX_SAMPLE_ROWS]],
        source_format=source_format,
        decimal="," if any(column.decimal_comma for column in columns) else ".",
        warnings=capped,
        list_columns=listed or None,
    )
    return ParsedDataset(
        profile=profile,
        csv=_write_csv([column.name for column in columns], rows),
        preview=[[preview_cell(cell) for cell in row] for row in rows[:PREVIEW_ROWS]],
        column_dtypes={column.name: column.dtype for column in columns},
        parse_dates=[column.name for column in columns if column.dtype == "datetime"],
        warnings=capped,
        text_columns=[column.name for column in columns if column.name in text_columns],
    )


def _blank_marks(column: _Column) -> int:
    """Blank the cells that match a declared missing-value mark when the column then reads as numbers or dates.

    Owner decision of 2026-10-15: a declared mark (`Missing values: -999`, `_declared_missing`)
    blanks cells of number and date columns only; a text column keeps its cells, so a category
    `M` or `NA` (Namibia) survives a declaration of `M` or `NA`. Returns the cells blanked,
    also those (`NA`) that were missing by default already.
    """
    if not column.mark_rows:
        return 0
    marked = set(column.mark_rows)
    blanked = ["" if row in marked else cell for row, cell in enumerate(column.source)]
    trial = _Column(name="", source=blanked, cells=[], id_like=column.id_like)
    _type_column(trial)
    if trial.dtype not in ("integer", "number", "datetime"):
        return 0
    column.source = blanked
    column.na_rows = [row for row in column.na_rows if row not in marked]
    column.missing_tokens -= column.mark_tokens  # counted once, by the declared mark's warning
    return len(marked)


def _keep_na_codes(column: _Column) -> None:
    """`NA` in a text column of letter codes is a code (Namibia, North America), not a missing cell.

    A pasted `NA` is missing by default (R and many exports write it so). In a column that
    stays text and whose other cells are all two- or three-letter upper-case codes, at
    least `MIN_OTHER_CODES` distinct ones (`CH`, `DE`, `NA`; `EU`, `NA`, `SA`), it is one of
    the codes: the cells get it back and a warning says so, so the root can drop those rows
    when the user meant missing. Any other column keeps it missing.
    """
    if not column.na_rows or column.dtype != "text":
        return
    present = {cell for cell in column.cells if cell}
    if len(present) < MIN_OTHER_CODES or not all(_LETTER_CODE.fullmatch(cell) for cell in present):
        return
    for row in column.na_rows:
        column.cells[row] = NA_TOKEN
    column.missing_tokens.pop(NA_TOKEN, None)
    column.notes.append(f"{NA_TOKEN} read as a code (such as Namibia or North America), not as a missing cell")


def _fidelity_notes(column: _Column, *, layout_padding: bool) -> None:
    """The column's notes for every cell the parse changed beyond its spelling (owner rule of 2026-10-15).

    A number keeps its value and a date its moment (`5.3.2024` is written `2024-03-05`).
    What is a change gets a note with its count: a number stored rounded (`_as_numbers`);
    a number whose value stayed but whose spelling did not (`1.50` as `1.5`, `1e3` as
    `1000.0`, `+3` as `3`: owner decision of 2026-10-15, the value is enough but the
    user is told); in a text column, a cell whose surrounding whitespace was removed (not
    in a space-aligned table, whose padding is layout); and in every column a token such
    as `NA`, `None` or `-` read as missing. Until live test round 5 of 2026-10-15 only a
    text column said so, where the token could have been a category; a number column's
    `NA` went unsaid, so the user saw four missing values in `sex` and none in
    `body_mass_g`, which had as many. Whitespace is no part of a number.
    """
    if column.dtype == "number" and column.rounded:
        column.notes.append(rounded_note(column.rounded))
    if column.dtype == "text" and column.trimmed and not layout_padding:
        column.notes.append(f"spaces around the text removed in {_count(column.trimmed, 'cell')}")
    if column.missing_tokens:
        total = sum(column.missing_tokens.values())
        tokens = column.missing_tokens.most_common()
        named = ", ".join(f"'{token}'" for token, _ in tokens[:3])
        if len(tokens) > 3:
            named += f" and {_count(len(tokens) - 3, 'other token')}"
        column.notes.append(f"{_count(total, 'cell')} read as missing ({named})")


def _without_empty_columns(
    read: list[tuple[str, bool, _Column]], warnings: list[str]
) -> list[tuple[str, bool, _Column]]:
    """The pasted columns without those that hold no value in any row, with one warning naming them.

    A statistics API's export carries its whole schema (live test of 2026-10-15: an ECB CSV
    had 14 columns such as `OBS_COM` and `BREAKS` without a single value), and those columns
    say nothing, crowd the preview and the profile, and count against the column cap, which
    is checked after this. They leave the table even when only one column with values remains
    (a table too small to plot is the later checks' and the root's to name); only a table of
    nothing but empty columns keeps them, so its own error stays the same. A canonical re-parse keeps
    them (`parse_dataset(canonical=True)`): an operation or the user's code made them on purpose.
    The warning names the columns as pasted (their headers before canonicalisation).
    """
    empty = [index for index, (_, _, column) in enumerate(read) if not any(column.source)]
    if not empty or len(empty) == len(read):
        return read
    names = ", ".join(_clip(read[index][0], MAX_COLUMN_NAME_CHARS) or f"column_{index + 1}" for index in empty)
    warnings.append(f"{_count(len(empty), 'column')} without any value dropped: {names}")
    gone = set(empty)
    return [entry for index, entry in enumerate(read) if index not in gone]


ROW_NAME_HEADERS = frozenset(("", "Unnamed: 0", "...1"))
"""The headers a tool gives the row-name or index column it writes first: R's `write.csv` (an empty name),
pandas' `to_csv` of an unnamed index (empty; `Unnamed: 0` after a round trip through `read_csv`) and readr's
`read_csv` of such a file (`...1`). No person names a column so."""
_DELIMITED: frozenset[SourceFormat] = frozenset(("csv", "tsv", "semicolon", "pipe", "whitespace"))


def _without_row_names(read: list[tuple[str, bool, _Column]], warnings: list[str]) -> list[tuple[str, bool, _Column]]:
    """The pasted columns without a leading row-name column that only numbers the rows, with one warning.

    R's `write.csv` writes the row names first under an empty header (`"","species",...`,
    then `"1","Chinstrap",...`), and pandas' `to_csv` writes its index so (live test round
    5 of 2026-10-15: the column became `column_1`, typed integer, and the default x of a
    scatter plot). The first column leaves the table when its header is one of
    `ROW_NAME_HEADERS` and its cells are exactly the row positions in order, `1` to `n` or
    `0` to `n - 1`, at least two rows, and another column remains. It holds nothing but the
    row order, which the table keeps: the warning names it and counts its cells (owner rule
    of 2026-10-15, a change is said with its count). A first column under such a header that
    holds anything else (row names such as car models, positions after a filter, `3`, `7`,
    `12`) is data and stays, named `column_1`. A column named `X` (R's `read.csv` of such a
    file) or `index` stays too: a person may name an x coordinate or an index so.
    """
    if len(read) < 2:
        return read
    header, _, column = read[0]
    cells = column.source
    if header not in ROW_NAME_HEADERS or len(cells) < 2 or cells[0] not in ("0", "1"):
        return read
    first = int(cells[0])
    if any(cell != str(first + offset) for offset, cell in enumerate(cells)):
        return read
    named = f"'{header}'" if header else "without a header"
    warnings.append(
        f"left out the first column ({named}): its {_count(len(cells), 'cell')} only number the rows "
        f"{first} to {first + len(cells) - 1} in order, as R's write.csv or pandas' to_csv write row names"
    )
    return read[1:]


def _constants_to_notes(
    columns: list[_Column], rows: int, text_columns: frozenset[str], warnings: list[str], context: list[str] | None
) -> list[_Column]:
    """The columns without those that hold the same text in every row, which become notes.

    A statistics export repeats its filters as columns (`Kanton` = `Schweiz`, `Geschlecht`
    = `Geschlecht - Total`): one value, no information per row, and a trap for a series or
    color binding. Like a JSON-stat dimension of one category (`_json_stat`), such a column
    leaves the table and `<name>: <value>` joins the notes (`context`), which the route
    screens before any model reads them; one warning names the columns, never the values.
    Only text columns with no missing cell count, in a table of at least two rows; a column
    kept text by request stays. When fewer than `MIN_KEPT_COLUMNS` columns would remain,
    every column stays: the table would have too little left to plot. A column whose note
    the notes' cap (`MAX_CONTEXT_CHARS`) would cut or leave out stays a column too, so the
    value is never lost to the cap. (When the route later drops every note because the
    screening refused them, `without_context`, the constants go with them, as a JSON-stat
    dimension's do.)
    """
    if rows < 2 or context is None:
        return columns
    constant = [
        column
        for column in columns
        if column.dtype == "text"
        and not column.text_only
        and column.name not in text_columns
        and all(column.cells)
        and len(set(column.cells)) == 1
    ]
    if not constant or len(columns) - len(constant) < MIN_KEPT_COLUMNS:
        return columns
    # A column moves only with its whole note: one the notes' cap would cut or leave out stays a column.
    notes = [_WHITESPACE_RUN.sub(" ", f"{column.name}: {column.cells[0]}").strip() for column in constant]
    lines, _ = _context_lines([*([line] for line in context), *([note] for note in notes)], None)
    fitted = lines[len(context) :]
    moving: list[_Column] = []
    for column, note, line in zip(constant, notes, fitted, strict=False):
        if note != line:
            break
        moving.append(column)
    if not moving:
        return columns
    context.extend(fitted[: len(moving)])
    names = ", ".join(column.name for column in moving)
    warnings.append(f"{_count(len(moving), 'column')} with the same text in every row moved to the notes: {names}")
    moved = {id(column) for column in moving}
    return [column for column in columns if id(column) not in moved]


def _profile_column(column: _Column) -> ColumnProfile:
    present = [cell for cell in column.cells if cell]
    minimum: int | float | str | None = None
    maximum: int | float | str | None = None
    mean: float | None = None
    median: float | None = None
    top: list[str] = []
    if column.dtype == "integer" and column.integers:
        # Exact: a float64 would round an id or a count past 2**53 in the profile the root reads.
        minimum, maximum = min(column.integers), max(column.integers)
        mean, median = _statistics(column.numbers)
    elif column.dtype in ("integer", "number") and column.numbers:
        minimum, maximum = min(column.numbers), max(column.numbers)
        mean, median = _statistics(column.numbers)
    elif column.dtype == "datetime" and column.dates and column.date_texts:
        order = sorted(range(len(column.dates)), key=lambda index: (column.dates[index], column.date_rests[index]))
        minimum, maximum = column.date_texts[order[0]], column.date_texts[order[-1]]
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
        months=named_months(column.cells) if column.dtype == "text" else None,
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
        or _grouped_like(name)
    )


def _grouped_like(cell: str) -> bool:
    """A cell that reads as a number with thousands groups (`1'234`, `7.184.003`, `1 234`), for finding the table.

    Looser than `_as_grouped_numbers`, which types a column: one apostrophe or space group counts
    here, since a table's value columns are what `table_block` looks for, not their type.
    """
    for mark in GROUP_MARKS:
        match = _GROUPED[mark].fullmatch(cell)
        if not match or mark not in cell or match["decimal"] == mark:
            continue
        if mark not in ".,":
            return True
        if cell.count(mark) >= 2 or match["decimal"] == ".":
            return not (mark == "." and _IPV4.fullmatch(cell))
    return False


def _clip(text: str, limit: int = MAX_CELL_CHARS) -> str:
    """A display copy for the preview, the sample and top values: one line, at most `limit` characters."""
    text = _WHITESPACE_RUN.sub(" ", text)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def preview_cell(cell: str) -> str:
    """The copy of a cell the page's preview shows: at most `MAX_CELL_CHARS`, its whitespace as it is.

    Line breaks and runs of spaces stay (owner decision of 2026-10-15): the page draws them
    visibly (`↵`, `·`), so the preview never shows `a  b` or a two-line cell as something
    the data does not hold. A cut is marked with `…`.
    """
    return cell if len(cell) <= MAX_CELL_CHARS else cell[: MAX_CELL_CHARS - 1] + "…"


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
