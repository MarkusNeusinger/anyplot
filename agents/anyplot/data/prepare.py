"""The `prepare_data` operations: a fixed set the model chooses from, applied with pandas on the server.

The design is docs/concepts/agent-network.md, "Two steps: data first, then the plot".
The model never writes data rows: it picks operations from the set below, each a
Pydantic model with every string bounded, and `apply_operations` applies them in order
to the canonical `data.csv` of a `ParsedDataset`. The result is canonical CSV text
again (comma, dot decimal, ISO dates, header first, missing as an empty cell) plus one
English change line per operation with its counts, so the user sees what changed
before confirming. The caller re-parses the text with `parse_dataset`, which applies
the caps, canonical headers and column typing again; this module never profiles.
No ADK import.

The operations:

* `rename` a column; `drop_columns` (1 to 10); `drop_rows` where 1 to 3 conditions on
  single columns all hold; `sort` by one column. A text column whose every cell names a
  month (`months.named_months`: `Jan`, `März`, `févr.`) sorts in calendar order, never
  alphabetically (`April` before `Januar` would be silently wrong; live test of
  2026-10-15), and the change line says so.
* `set_type` of one column to `number`, `datetime` or `text`. To number: one unit token
  at either end (`12,5 %`, `€ 12`, `1.200 EUR`) is removed, then the cell is read with
  `decimal` as the parser reads a number: the other mark is a thousands separator in
  three-digit groups only (`1,234.5` with a dot decimal), spaces and apostrophes
  separate thousands too, and a mark anywhere else makes the cell unreadable with that
  decimal (`12,5` is no dot-decimal number, never 125). When cells fail with `decimal`
  and fewer fail with the other mark, the whole column is read with the other mark and
  the change line says so ("read as numbers (decimal comma)"); the unit must be the
  same wherever it occurs. Whole numbers are read exactly (`Int64`, never through a
  float64), and the change line counts the cells a float64 holds only rounded (more
  than 15 to 17 significant digits). To datetime: with `date_format` the cells are read in
  exactly that format, with an optional time (`HH:MM[:SS]`) after it (a format without
  a day, such as `YYYY-MM` or `YYYY`, reads the first day of the month or the year;
  `YYYY` on a number column says "read as years", since a measure of 1450 to 2100 reads
  the same way; the compact `YYYYMMDD`, `YYYYMM` and `YYYY` take exactly their 8, 6 or
  4 digits, so `2024115` is refused, never guessed; `MM.YYYY` reads a column the parser
  read as numbers, `03.2020` as 3.202, through four decimals, only when every cell then
  is a month 1 to 12 of a year 1000 to 2200, at most 300 years apart, else the column of
  ordinary decimals is a `type_mismatch`). The cells are read with Python's own parser
  and stored at microseconds, so any year from 1 to 9999 fits (a datetime64[ns] holds
  only 1677 to 2262; a date pandas still cannot hold is an `invalid_operation`, never a
  crash). Without `date_format`
  pandas infers the format per cell, day before month when ambiguous, as the parser
  reads a slash date, except for a cell that starts with a year (`2024-06-01T13:00:00Z`
  is 1 June; the order is chosen per cell); a fraction of a second and a UTC offset are
  kept (`_cell_text`), different offsets in one column are read in UTC with the offsets
  named in the change line (owner decision of 2026-10-15, as the parser writes such a
  column), and times with and without an offset are a `type_mismatch`. Either way a cell that cannot be read becomes missing and the
  change line counts it; when more than 10 % of the non-missing cells fail, the
  operation is a `type_mismatch` instead. To text: every cell becomes its canonical
  text and the column is kept text through the re-parse (`Prepared.text_columns`,
  `parse_dataset(text_columns=...)`), so a column of years or ids stays a category in
  every later version. A column that already is a number or a datetime column is left
  as it is ("already numbers, nothing changed"), with one exception: a date column
  whose day and month order is open (every day at most 12: the parser's slash guess,
  its `AMBIGUOUS_DATE_ORDER` warning, or a `set_type` read of such cells) swaps day and
  month when the format asks for the other order, `MM/DD/YYYY` on a column read day
  first and `DD/MM/YYYY` or `DD.MM.YYYY` on one read month first, so a wrong choice can
  be taken back; the order travels to the next version as a warning
  (`Prepared.date_notes`, `with_date_notes`). A column whose order is settled (ISO, or
  a day over 12) stays as it is (see `_reread_dates`).
* `aggregate`: group by one or two key columns and reduce one value column with `sum`,
  `mean`, `count`, `min` or `max`. A `period` turns every datetime key into `YYYY-MM`,
  `YYYY-Qn` or `YYYY` text before grouping, or, since live test round 5 of 2026-10-15
  ("Tagesmittel pro Sensor" on readings every 13 minutes), into the first moment of its
  `hour`, `day` or ISO `week` (its Monday), which stays a datetime, so the result keeps
  a time axis: a day and a week are written as dates, an hour with its time and offset.
  The buckets follow the column's clock as stored: a column with one UTC offset is cut
  at its own midnight, one the parser wrote in UTC (several offsets) at UTC midnight,
  and the change line names that offset. The result holds the key columns and one
  value column named like the source, or `count`; every other column is dropped, rows
  with a missing key form their own group, and the rows are sorted by the keys.
* `pivot_longer`: 2 to 20 columns become a `names_to`/`values_to` pair (long format,
  one row per source row and column, missing values kept; columns of unlike kinds melt
  into their canonical texts, a datetime with its time). `pivot_wider`: the distinct
  values of `names_from` become new columns (at most 50, and at most 50 columns in all,
  else `too_wide`) holding `values_from`, one row per distinct index; duplicate index
  and name pairs are refused rather than aggregated.
* `classify`: a new text column `name`, appended last, whose cells are labels: each row
  gets the label of the first of 1 to 10 rules whose conditions (1 to 3, as in
  `drop_rows`) all hold, else `otherwise`, or a missing cell when that is left out. A
  label is at most a cell's length, never a token the parser reads as missing (`NA`,
  `-`), and is new text the model writes from the user's message, as a rename's name
  is (so ToolSafety exempts it from the link rule, as it exempts a name). The column stays text through the re-parse, so
  labels such as `1` and `2` remain categories. This is how a category is derived from
  the cells that are there ("positive y is class 1, the rest class 2"); a rule that
  matches no row is reported with its count of 0, and a column that would hold no
  label at all is an `invalid_operation`.
* `derive`: a new number column `name`, appended last, computed row by row from number
  columns by one of a closed set of formulas (`DeriveHow`; never a free expression):
  `ratio` (`a / b`) and `difference` (`a - b`) of exactly two columns, `sum` of 2 to 10
  columns in the same row (missing cells count as 0, a row with none present stays
  missing), `share` of one column in the total of its group (`within` 0 to 2 key
  columns, none for the whole column), and three ordered formulas of one column within
  its group in the order of `order`: `percent_change` from the previous row (a group's
  first row is missing), `cumsum`, the running total (missing cells add nothing), and
  `index`, the value relative to the group's first row with a value, which is 100
  (owner decision of 2026-10-14). The order column must hold numbers or dates: a text
  column sorts alphabetically (`April` before `Januar`, `10` before `9`), which would be
  silently wrong, so it is a `type_mismatch` with a hint to `set_type` it first. Two
  rows with the same group and order are an `invalid_operation`, since "previous" would
  be a guess (aggregate first); a row without an order value gets an empty cell and
  takes no place in the order. `percent` multiplies a `ratio` or a `share` by 100;
  a percent change is always in percent. A difference, a sum or a `cumsum` of
  whole-number columns is computed in Python integers and stays whole (a float64 holds
  integers only up to 2**53), as does an `aggregate` `sum` (pandas' `Int64` sum wraps
  around past 2**63); a result past int64 makes the column float64, and the change line
  counts the values it rounds (`whole_rounded`). A division by zero or a missing input gives a
  missing cell, and the change line counts them. A question such as "which year has the
  largest share of X" takes the same operations through `query_data` (`query.py`), on a
  copy that is never stored (live tests of 2026-10-14 and 2026-10-15).
* `make_date`: a new date column `name`, appended last, built row by row from the parts
  of a date held in whole-number columns: a `year`, then a `month` and optionally a
  `day`, or a `quarter`, or an ISO `week`; a part left out is its first (January, the
  first day of the month or the quarter, the Monday of the ISO week, so week 1 can start
  in late December of the year before, as the change line says). A day needs a month,
  and a quarter or a week takes no other part. A part column holds whole numbers within
  its range (a year of four digits, 1000 to 9999, so a two-digit `24` is refused rather
  than read as the year 24; a month 1 to 12, a day
  1 to 31, a quarter 1 to 4, a week 1 to 53), else the operation is refused, as it is
  when a row's parts are no calendar date (31 April, week 53 of a 52-week year): a
  date is never moved to the next valid one. A text `month` column may hold month names
  and abbreviations in the eleven languages of the fixed refusals (`months.MONTH_NAMES`: en,
  de, fr, es, it, pt, nl, pl, zh, vi, ru; `Jan`, `März`, `févr.`, `Май`, `3月`,
  `tháng 3`), compared without case and diacritics; one unknown name refuses it (owner
  decision of 2026-10-15). Any other text part column is a `type_mismatch` with a
  hint to `set_type` it to number first. A row with a missing part gets an empty cell,
  which the change line counts. It came from the live test of 2026-10-15: a MeteoSwiss
  table of `Year` and `Month` had no date column for a time series, and the root could
  only ask the user to add one by hand.

Values in conditions are never evaluated: a condition compares text with text for a
text column, numbers for a numeric column (the value is a dot-decimal number, which
the model may also pass as a JSON number), moments for a datetime column (the value is
an ISO date or date-time), `true`/`false` for a boolean column. A missing cell matches
only `is_missing`. `contains` searches the cell's canonical text, case-sensitively.

What the canonical CSV does not say about its columns travels with the frame as
`_Carried`: the columns the parser read by guess, the columns kept text, whether a
datetime column is written with its time (the parser's choice, read from the profile),
and the form of each whole number in a float column (`87000` or `2.0`, as the paste
wrote it; live test round 5 of 2026-10-15, where `87000` came back as `87000.0` after a
wide-to-long), so a column no operation touched is written back exactly as it was
stored and a value an operation moves keeps its form. A whole number an operation
computes (a sum, a mean, a ratio) is written without `.0` unless its column writes
every whole number with it; past 2**53 it keeps the `.0` that shows it is a float.

Errors raise `PrepareError(code, message)`: `unknown_column`, `type_mismatch`,
`empty_result` (no rows or no columns would remain), `too_wide` and
`invalid_operation` (an operation that is well-formed but cannot apply, such as a
condition without its value, a `period` without a datetime key, or a long format that
would exceed the 2 MiB cap of computed data, `parse.MAX_COMPUTED_BYTES`). Messages name columns, never cells.
Change lines name column names bare, condition values quoted and clipped to 40
characters, and are at most `MAX_NOTE_CHARS` long. `validation_lines` formats a
Pydantic error of the operation models for the model (`tools/session.py` and
`plugins/tool_safety.py` share it), one line per error with its location.
"""

import csv
import io
import math
import re
import unicodedata
import warnings
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, tzinfo
from decimal import ROUND_FLOOR, InvalidOperation
from decimal import Decimal as ExactDecimal
from typing import Annotated, Any, Literal

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_datetime64_any_dtype, is_integer_dtype, is_numeric_dtype
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, ValidationError

from ..schemas import MAX_CELL_CHARS, MAX_COLUMNS, MAX_NOTE_CHARS, MAX_ROWS, MAX_WARNINGS, ColumnName
from .months import month_number, named_months
from .parse import (
    AMBIGUOUS_DATE_ORDER,
    MAX_COMPUTED_BYTES,
    MISSING_VALUES,
    ParsedDataset,
    canonical_names,
    keeps_value,
    pandas_dtypes,
    rounded_note,
)


MAX_OPERATIONS = 5  # per `prepare_data` call, the design's "at most five operations"
MAX_VALUE_CHARS = 200  # a condition value, as long as a parsed cell can be
MAX_DROP_COLUMNS = 10
MAX_CONDITIONS = 3
MAX_RULES = 10  # of one `classify`
MAX_KEYS = 2
MAX_DERIVE_COLUMNS = 10  # of one `derive sum`
MAX_LONGER_COLUMNS = 20
MAX_WIDER_COLUMNS = 50
MAX_FAILED_SHARE = 0.10  # of the non-missing cells; more than this is `type_mismatch`
MAX_VALIDATION_LINES = 10  # of a refused operation list, for the model
_INT64_MIN, _INT64_MAX = -(2**63), 2**63 - 1

Test = Literal["eq", "ne", "contains", "is_missing", "gt", "lt"]
TargetType = Literal["number", "datetime", "text"]
DateFormat = Literal[
    "DD.MM.YYYY",
    "MM/DD/YYYY",
    "YYYY-MM-DD",
    "DD/MM/YYYY",
    "YYYYMMDD",
    "YYYYMM",
    "YYYY-MM",
    "MM/YYYY",
    "MM.YYYY",
    "YYYY",
]
Decimal = Literal[".", ","]
How = Literal["sum", "mean", "count", "min", "max"]
Period = Literal["hour", "day", "week", "month", "quarter", "year"]
DATE_PERIODS = frozenset(("hour", "day", "week"))
"""The periods whose bucket stays a datetime, its first moment (`_period_starts`); the others become text labels."""
Kind = Literal["number", "datetime", "boolean", "text"]
DeriveHow = Literal["ratio", "difference", "sum", "share", "percent_change", "cumsum", "index"]
ORDERED: frozenset[str] = frozenset(("percent_change", "cumsum", "index"))
"""The formulas that walk each group in the order of `order`."""
_DERIVE_ARITY: dict[str, tuple[int, int]] = {
    "ratio": (2, 2),
    "difference": (2, 2),
    "sum": (2, MAX_DERIVE_COLUMNS),
    "share": (1, 1),
    "percent_change": (1, 1),
    "cumsum": (1, 1),
    "index": (1, 1),
}
"""How many value columns each formula takes, as (at least, at most)."""
PrepareErrorCode = Literal["unknown_column", "type_mismatch", "empty_result", "too_wide", "invalid_operation"]

STRPTIME: dict[str, str] = {
    "DD.MM.YYYY": "%d.%m.%Y",
    "MM/DD/YYYY": "%m/%d/%Y",
    "YYYY-MM-DD": "%Y-%m-%d",
    "DD/MM/YYYY": "%d/%m/%Y",
    "YYYYMMDD": "%Y%m%d",
    "YYYYMM": "%Y%m",
    "YYYY-MM": "%Y-%m",
    "MM/YYYY": "%m/%Y",
    "MM.YYYY": "%m.%Y",
    "YYYY": "%Y",
}
COMPACT_DIGITS: dict[str, int] = {"YYYYMMDD": 8, "YYYYMM": 6, "YYYY": 4}
"""The digits a compact date format takes exactly, without a time."""
MONTH_YEAR_RANGE = (1000, 2200)
MONTH_YEAR_SPAN = 300
"""The years an `MM.YYYY` column the parser read as numbers may hold, and their widest spread."""
DatePart = Literal["year", "month", "day", "quarter", "week"]
DATE_PART_RANGES: dict[str, tuple[int, int]] = {
    "year": (1000, 9999),  # four digits: a two-digit year (`24`) is refused, never read as the year 24
    "month": (1, 12),
    "day": (1, 31),
    "quarter": (1, 4),
    "week": (1, 53),
}
"""The values a `make_date` part column may hold, inclusive."""
_TIME_SUFFIXES = ("", " %H:%M", " %H:%M:%S", "T%H:%M", "T%H:%M:%S")
_VERBS: dict[str, str] = {
    "sum": "summed",
    "mean": "averaged",
    "count": "counted",
    "min": "took the minimum of",
    "max": "took the maximum of",
}
_TEST_SIGNS: dict[str, str] = {"eq": "=", "ne": "≠", "gt": ">", "lt": "<"}

# The parser's number shape: a dot decimal with an optional exponent, ASCII digits only.
_NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")
# The parser's thousands-grouped shapes, per decimal mark: the other mark between three-digit
# groups, never starting with a zero group, then an optional fraction (`1,234.5` and `1.234,5`).
_GROUPED: dict[str, re.Pattern[str]] = {
    ".": re.compile(r"[+-]?[1-9][0-9]{0,2}(?:,[0-9]{3})+(?:\.[0-9]+)?"),
    ",": re.compile(r"[+-]?[1-9][0-9]{0,2}(?:\.[0-9]{3})+(?:,[0-9]+)?"),
}
# A number body for the unit split: a sign, then digits with separators, ending in a digit.
_BODY = r"[+-]?[0-9](?:[0-9.,'\s]*[0-9])?"
_TRAILING_UNIT = re.compile(rf"^(?P<body>{_BODY})\s*(?P<unit>[^0-9\s][^0-9]*)$")
_LEADING_UNIT = re.compile(rf"^(?P<unit>[^0-9\s+-][^0-9]*?)\s*(?P<body>{_BODY})$")
_SPACES = re.compile(r"\s+")
_HEADER_BREAKS = re.compile(r"[\t\r\n]")
AMBIGUOUS_MONTH_FIRST = "day and month order is ambiguous; read as MM/DD/YYYY"
"""The note of a date column whose every day is at most 12, read month first (`set_type` with `MM/DD/YYYY`)."""
_ORDER_NOTES: dict[str, str] = {"day": AMBIGUOUS_DATE_ORDER, "month": AMBIGUOUS_MONTH_FIRST}
_AMBIGUOUS_WARNING = re.compile(
    rf"column '(?P<name>.+)': (?P<note>{re.escape(AMBIGUOUS_DATE_ORDER)}|{re.escape(AMBIGUOUS_MONTH_FIRST)})"
)
_YEAR_FIRST = re.compile(r"\s*[0-9]{4}[-/.]")
_DAY_FIRST_FORMATS = frozenset(("DD.MM.YYYY", "DD/MM/YYYY"))
"""The formats that read a day before a month; `MM/DD/YYYY` is the one that reads the month first."""


class PrepareError(Exception):
    """An operation that cannot be applied; `code` is fixed, `message` names columns at most."""

    def __init__(self, code: PrepareErrorCode, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code: PrepareErrorCode = code
        self.message = message


@dataclass(frozen=True)
class Prepared:
    """The result of `apply_operations`: canonical CSV text and one change line per operation."""

    csv: str
    changes: list[str]
    text_columns: list[str] = field(default_factory=list)
    """The columns kept text (`set_type text` and `classify`): the caller passes them to `parse_dataset(text_columns=...)`."""
    date_notes: list[str] = field(default_factory=list)
    """`column '<name>': <order note>` per date column whose day and month order is still a guess: the caller adds
    them to the re-parsed version's warnings (`with_date_notes`), so a later call can still switch the order."""


def with_date_notes(parsed: ParsedDataset, prepared: Prepared) -> ParsedDataset:
    """The re-parsed version with `prepared.date_notes` among its warnings, the profile's included.

    The canonical CSV writes ISO dates, so its re-parse no longer knows that the order of
    a column's day and month was a guess; the note keeps that knowledge with the version.
    """
    if not prepared.date_notes:
        return parsed
    notes = [*parsed.warnings, *prepared.date_notes][:MAX_WARNINGS]
    return replace(parsed, warnings=notes, profile=parsed.profile.model_copy(update={"warnings": notes}))


@dataclass
class _Carried:
    """What the canonical CSV does not say about its columns, carried through the operations.

    The parse's notes name columns, and an operation renames, drops or creates them,
    so the notes follow the frame: `date_order` holds the date columns whose every day
    is at most 12, so day and month could be read either way, with the order they
    were read in (`day` for the parser's slash guess, its `AMBIGUOUS_DATE_ORDER`
    warning, and for a `set_type` that read a day first; `month` for `MM/DD/YYYY`;
    `Prepared.date_notes` carries it into the next version), `text_columns` the
    columns kept text through the re-parse, and `with_time` whether a datetime column
    is written with its time (the parser's choice, read from the profile's `min`; a
    column no operation touched is therefore written back exactly as stored,
    `T00:00:00` included). `forms` holds, per number column, the form each whole
    number was written in (True for `2.0`, False for `87000`, which the parser keeps
    so, `parse.number_text`; live test round 5 of 2026-10-15), and `dotted` the
    columns whose whole numbers are all written with `.0` (as pandas writes a float
    column), the form of a whole number the column did not hold (a mean, a sum). Any
    other float column writes a new whole number without `.0`. So a whole number keeps
    the form the user saw through every operation that moves it (`_cell_text`).
    """

    decimal: str
    date_order: dict[str, str] = field(default_factory=dict)
    text_columns: set[str] = field(default_factory=set)
    with_time: dict[str, bool] = field(default_factory=dict)
    dotted: set[str] = field(default_factory=set)
    forms: dict[str, dict[float, bool]] = field(default_factory=dict)
    mixed: dict[str, int] = field(default_factory=dict)
    """Per column, the cells of a whole number it wrote both ways, which the write puts in the column's form."""

    @classmethod
    def of(cls, parsed: ParsedDataset) -> "_Carried":
        matches = (_AMBIGUOUS_WARNING.fullmatch(warning) for warning in parsed.warnings)
        order = {
            match.group("name"): "day" if match.group("note") == AMBIGUOUS_DATE_ORDER else "month"
            for match in matches
            if match
        }
        with_time = {
            column.name: isinstance(column.min, str) and "T" in column.min
            for column in parsed.profile.columns
            if column.dtype == "datetime"
        }
        forms, dotted, mixed = _whole_forms(parsed)
        return cls(parsed.profile.decimal, order, set(parsed.text_columns), with_time, dotted, forms, mixed)

    def rename(self, old: str, new: str) -> None:
        if old in self.text_columns:
            self.text_columns.remove(old)
            self.text_columns.add(new)
        if old in self.date_order:
            self.date_order[new] = self.date_order.pop(old)
        if old in self.with_time:
            self.with_time[new] = self.with_time.pop(old)
        if old in self.dotted:
            self.dotted.remove(old)
            self.dotted.add(new)
        if old in self.forms:
            self.forms[new] = self.forms.pop(old)
        if old in self.mixed:
            self.mixed[new] = self.mixed.pop(old)

    def forget(self, names: Iterable[str]) -> None:
        for name in names:
            self.date_order.pop(name, None)
            self.text_columns.discard(name)
            self.with_time.pop(name, None)
            self.dotted.discard(name)
            self.forms.pop(name, None)
            self.mixed.pop(name, None)

    def keep_only(self, names: Iterable[str]) -> None:
        kept = set(names)
        known = {*self.date_order, *self.text_columns, *self.with_time, *self.dotted, *self.forms, *self.mixed}
        self.forget(known - kept)

    def form(self, name: object) -> tuple[bool, Mapping[float, bool]]:
        """The column's form of a whole number it did not hold, and the forms of those it held (`_cell_text`)."""
        return str(name) in self.dotted, self.forms.get(str(name), {})


def _whole_forms(parsed: ParsedDataset) -> tuple[dict[str, dict[float, bool]], set[str], dict[str, int]]:
    """Per number column of the canonical CSV, each whole number's form (True for `2.0`, False for `2`), the
    columns whose form is `.0` (`_Carried.dotted`), and per column the cells whose form the next write changes.

    A value written both ways in one column (`2.0` in one row, `2` in another) has no form of its own and takes
    the column's: the cells written the other way are counted, and the change lines say so (`_Carried.mixed`,
    Copilot review of #12200), because one cell can carry no form through an operation that moves it.
    """
    numbers = [name for name, dtype in parsed.column_dtypes.items() if dtype == "number"]
    if not numbers:
        return {}, set(), {}
    reader = csv.reader(io.StringIO(parsed.csv))
    header = next(reader, [])
    positions = {name: header.index(name) for name in numbers if name in header}
    seen: dict[str, Counter[tuple[float, bool]]] = {name: Counter() for name in positions}
    for row in reader:
        for name, position in positions.items():
            cell = row[position] if position < len(row) else ""
            if cell and "e" not in cell and float(cell).is_integer():
                seen[name][(float(cell), cell.endswith(".0"))] += 1
    forms: dict[str, dict[float, bool]] = {}
    dotted: set[str] = set()
    mixed: dict[str, int] = {}
    for name, counts in seen.items():
        clashing = {value for value, form in counts if (value, not form) in counts}
        forms[name] = {value: form for value, form in counts if value not in clashing}
        if forms[name] and all(forms[name].values()):
            dotted.add(name)
        changed = sum(
            count for (value, form), count in counts.items() if value in clashing and form != (name in dotted)
        )
        if changed:
            mixed[name] = changed
    return forms, dotted, mixed


# --- Operation models -----------------------------------------------------------------------


def _clean_name(name: str) -> str:
    """A new column name as the parser would keep it: no surrounding whitespace, breaks or invisible characters."""
    if name != name.strip() or _HEADER_BREAKS.search(name):
        raise ValueError("a column name has no surrounding whitespace, tabs or line breaks")
    if any(unicodedata.category(char) == "Cf" for char in name):
        raise ValueError("a column name has no invisible formatting characters")
    return name


def _clean_label(label: str) -> str:
    """A `classify` label that the re-parse keeps exactly as written.

    No surrounding whitespace, breaks, control, invisible or line and paragraph
    separator characters (the parser drops or turns them into spaces), and no token
    the parser reads as a missing cell (`NA`, `null`, `-`, ...), which would store an
    empty cell where the change line reported a label.
    """
    if label != label.strip() or _HEADER_BREAKS.search(label):
        raise ValueError("a label has no surrounding whitespace, tabs or line breaks")
    if any(unicodedata.category(char) in ("Cc", "Cf", "Zl", "Zp") for char in label):
        raise ValueError("a label has no control, invisible or separator characters")
    if label in MISSING_VALUES:
        raise ValueError("a label is not a token the data reads as missing, such as NA, null or -")
    return label


NewName = Annotated[ColumnName, AfterValidator(_clean_name)]
Value = Annotated[str, Field(max_length=MAX_VALUE_CHARS)]
Label = Annotated[str, Field(min_length=1, max_length=MAX_CELL_CHARS), AfterValidator(_clean_label)]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Condition(_Strict):
    """One test on one column; `value` is required for every test but `is_missing`.

    A JSON number as the value (`{"test": "gt", "value": 100}`) is read as its text,
    so a numeric comparison needs no quoting.
    """

    model_config = ConfigDict(extra="forbid", coerce_numbers_to_str=True)

    column: ColumnName
    test: Test
    value: Value | None = None


class Rename(_Strict):
    op: Literal["rename"]
    column: ColumnName
    name: NewName


class DropColumns(_Strict):
    op: Literal["drop_columns"]
    columns: list[ColumnName] = Field(min_length=1, max_length=MAX_DROP_COLUMNS)


class DropRows(_Strict):
    """Drop every row for which all conditions hold."""

    op: Literal["drop_rows"]
    where: list[Condition] = Field(min_length=1, max_length=MAX_CONDITIONS)


class SetType(_Strict):
    """`decimal` defaults to the dataset's own; `date_format` left out lets pandas infer the format."""

    op: Literal["set_type"]
    column: ColumnName
    type: TargetType
    date_format: DateFormat | None = None
    decimal: Decimal | None = None


class Aggregate(_Strict):
    op: Literal["aggregate"]
    by: list[ColumnName] = Field(min_length=1, max_length=MAX_KEYS)
    column: ColumnName
    how: How
    period: Period | None = None


class Sort(_Strict):
    op: Literal["sort"]
    column: ColumnName
    descending: bool = False


class PivotLonger(_Strict):
    op: Literal["pivot_longer"]
    columns: list[ColumnName] = Field(min_length=2, max_length=MAX_LONGER_COLUMNS)
    names_to: NewName = "series"
    values_to: NewName = "value"


class PivotWider(_Strict):
    op: Literal["pivot_wider"]
    names_from: ColumnName
    values_from: ColumnName
    index: list[ColumnName] = Field(min_length=1, max_length=MAX_KEYS)


class Rule(_Strict):
    """The rows for which all conditions hold get `label`, unless an earlier rule labelled them."""

    where: list[Condition] = Field(min_length=1, max_length=MAX_CONDITIONS)
    label: Label


class Classify(_Strict):
    """A new text column of labels: the first rule that holds names a row, else `otherwise` (missing when left out)."""

    op: Literal["classify"]
    name: NewName
    rules: list[Rule] = Field(min_length=1, max_length=MAX_RULES)
    otherwise: Label | None = None


class Derive(_Strict):
    """A new number column computed row by row from number columns by one formula of a closed set.

    `columns` are the inputs (two for `ratio` and `difference`, in the order `a / b` and
    `a - b`; 2 to 10 for `sum`; one for `share` and the ordered formulas `percent_change`,
    `cumsum` and `index`). `within` groups the rows for `share` and the ordered formulas;
    `order`, a number or datetime column, sorts each group for the ordered formulas.
    """

    op: Literal["derive"]
    name: NewName
    how: DeriveHow
    columns: list[ColumnName] = Field(min_length=1, max_length=MAX_DERIVE_COLUMNS)
    within: list[ColumnName] = Field(default_factory=list, max_length=MAX_KEYS)
    order: ColumnName | None = None
    percent: bool = False


class MakeDate(_Strict):
    """A new date column from whole-number part columns: a `year`, then a `month` and a `day`, or a `quarter`, or a `week`.

    A part left out is its first: January, the first day of the month or the quarter,
    the Monday of the ISO week. A day needs a month; a quarter or a week takes no other
    part than the year.
    """

    op: Literal["make_date"]
    name: NewName
    year: ColumnName
    month: ColumnName | None = None
    day: ColumnName | None = None
    quarter: ColumnName | None = None
    week: ColumnName | None = None


Operation = Annotated[
    Rename
    | DropColumns
    | DropRows
    | SetType
    | Aggregate
    | Sort
    | PivotLonger
    | PivotWider
    | Classify
    | Derive
    | MakeDate,
    Field(discriminator="op"),
]


# --- Applying ---------------------------------------------------------------------------------


def apply_operations(parsed: ParsedDataset, operations: list[Operation]) -> Prepared:
    """Apply `operations` in order to the canonical CSV of `parsed`; raises `PrepareError`."""
    if not operations:
        raise PrepareError("invalid_operation", "there is no operation to apply")
    if len(operations) > MAX_OPERATIONS:
        raise PrepareError("invalid_operation", f"at most {MAX_OPERATIONS} operations can be applied at once")
    carried = _Carried.of(parsed)
    frame = _read(parsed)
    changes: list[str] = []
    for operation in operations:
        try:
            frame, change = _apply(frame, operation, carried)
        except (pd.errors.OutOfBoundsDatetime, OverflowError):
            # A date pandas cannot hold is a refusal, never a crash of the tool (review of 2026-10-15).
            raise PrepareError("invalid_operation", "a date would lie outside the years the data can hold") from None
        if not frame.shape[1]:
            raise PrepareError("empty_result", "no column would remain")
        if not len(frame):
            raise PrepareError("empty_result", "no row would remain")
        changes.append(_clip(change, MAX_NOTE_CHARS))
    mixed = [name for name in carried.mixed if name in frame.columns]
    if mixed:
        # A whole number one column wrote both ways is written in one form now: said, with its count.
        where = _listed(mixed) if len(mixed) <= 3 else _count(len(mixed), "column")
        total = sum(carried.mixed[name] for name in mixed)
        changes[-1] = _with_notice(
            changes[-1],
            f"{where} wrote the same whole number both with and without '.0' ({_count(total, 'cell')} in the "
            "other form), now written in one form",
        )
    csv_text = _write(frame, carried)
    if len(csv_text.encode("utf-8")) > MAX_COMPUTED_BYTES:
        # Only the long format grows the data; the re-parse would refuse it, so the model hears it from here.
        raise PrepareError(
            "invalid_operation",
            f"the result would be larger than {MAX_COMPUTED_BYTES // 1024:,} KB; "
            "drop columns or aggregate before pivoting to the long format",
        )
    # Named as the re-parse will name them: a pivot's value or a long new name may be shortened or
    # suffixed by `canonical_headers`, and the hint must match the header the CSV gets.
    names = [str(name) for name in frame.columns]
    canonical = canonical_names(names)
    text_columns = [canon for name, canon in zip(names, canonical, strict=True) if name in carried.text_columns]
    date_notes = [
        f"column '{canon}': {_ORDER_NOTES[carried.date_order[name]]}"
        for name, canon in zip(names, canonical, strict=True)
        if name in carried.date_order and _kind(frame[name]) == "datetime"
    ]
    return Prepared(csv=csv_text, changes=changes, text_columns=text_columns, date_notes=date_notes)


def _apply(frame: pd.DataFrame, operation: Operation, carried: _Carried) -> tuple[pd.DataFrame, str]:
    match operation:
        case Rename():
            return _rename(frame, operation, carried)
        case DropColumns():
            return _drop_columns(frame, operation, carried)
        case DropRows():
            return _drop_rows(frame, operation, carried)
        case SetType():
            return _set_type(frame, operation, carried)
        case Aggregate():
            return _aggregate(frame, operation, carried)
        case Sort():
            return _sort(frame, operation)
        case PivotLonger():
            return _pivot_longer(frame, operation, carried)
        case PivotWider():
            return _pivot_wider(frame, operation, carried)
        case Classify():
            return _classify(frame, operation, carried)
        case Derive():
            return _derive(frame, operation, carried)
        case MakeDate():
            return _make_date(frame, operation, carried)


def _read(parsed: ParsedDataset) -> pd.DataFrame:
    """The canonical CSV as the loader reads it; `round_trip` keeps every number's shortest form stable.

    Only an empty cell is missing (`keep_default_na=False`, as the run form's loader reads
    it): a text category `NA` (Namibia, North America) that the parse kept is a category here too.
    """
    return pd.read_csv(
        io.StringIO(parsed.csv),
        dtype=pandas_dtypes(parsed.column_dtypes),
        parse_dates=list(parsed.parse_dates),
        date_format="ISO8601",  # `data.csv` writes ISO dates only: no per-column guess, no "Could not infer" warning
        float_precision="round_trip",
        keep_default_na=False,
        na_values=[""],
    )


def _write(frame: pd.DataFrame, carried: _Carried) -> str:
    """Canonical CSV text: every column written through its canonical cell texts."""
    out = pd.DataFrame(
        {str(name): _texts(frame[name], _with_time(frame[name], carried), carried.form(name)) for name in frame.columns}
    )
    return out.to_csv(index=False, lineterminator="\n")


def _rename(frame: pd.DataFrame, op: Rename, carried: _Carried) -> tuple[pd.DataFrame, str]:
    _require(frame, op.column)
    if op.name in frame.columns:
        raise PrepareError("invalid_operation", f"a column named '{op.name}' already exists")
    carried.rename(op.column, op.name)
    return frame.rename(columns={op.column: op.name}), f"renamed '{op.column}' to '{op.name}'"


def _drop_columns(frame: pd.DataFrame, op: DropColumns, carried: _Carried) -> tuple[pd.DataFrame, str]:
    columns = _distinct(op.columns)
    for name in columns:
        _require(frame, name)
    if len(columns) >= frame.shape[1]:
        raise PrepareError("empty_result", "dropping these columns would leave no column")
    carried.forget(columns)
    if len(columns) == 1:
        return frame.drop(columns=columns), f"dropped column {columns[0]}"
    return frame.drop(columns=columns), f"dropped {len(columns)} columns: {', '.join(columns)}"


def _drop_rows(frame: pd.DataFrame, op: DropRows, carried: _Carried) -> tuple[pd.DataFrame, str]:
    mask = pd.Series(True, index=frame.index)
    clauses: list[str] = []
    for condition in op.where:
        _require(frame, condition.column)
        series = frame[condition.column]
        mask &= _matches(series, condition, _with_time(series, carried), carried.form(condition.column))
        clauses.append(_describe(condition, _kind(series)))
    dropped = int(mask.sum())
    if dropped == len(frame):
        raise PrepareError("empty_result", "every row matches the conditions; no row would remain")
    kept = frame[~mask].reset_index(drop=True)
    return kept, f"dropped {_count(dropped, 'row')} where {' and '.join(clauses)}"


def _set_type(frame: pd.DataFrame, op: SetType, carried: _Carried) -> tuple[pd.DataFrame, str]:
    _require(frame, op.column)
    series = frame[op.column]
    present = int(series.notna().sum())
    kind = _kind(series)
    result = frame.copy()
    zone_notice = ""  # different UTC offsets converted to UTC by a read as dates
    if op.type == "text":
        # Kept text through the re-parse either way: a text column stays one when a later change makes its cells typeable.
        carried.text_columns.add(op.column)
        if kind == "text":
            return frame, f"{op.column}: already text, nothing changed"
        result[op.column] = _texts(series, _with_time(series, carried), carried.form(op.column))
        carried.with_time.pop(op.column, None)
        carried.date_order.pop(op.column, None)
        carried.dotted.discard(op.column)
        carried.forms.pop(op.column, None)
        return result, f"{op.column}: {_count(present, 'cell')} now text"
    if op.type == "number":
        if kind == "number":
            # The canonical text of a number is a dot decimal; re-reading it under a decimal comma would be wrong.
            return frame, f"{op.column}: already numbers, nothing changed"
        requested = op.decimal or carried.decimal
        converted, unit, failed, used, rounded = _to_numbers(series, requested)
        _check_failed(op.column, failed, present, "numbers")
        result[op.column] = converted
        carried.with_time.pop(op.column, None)
        carried.date_order.pop(op.column, None)
        change = f"{op.column}: {_count(present - failed, 'cell')} read as numbers"
        if used != requested:
            change += " (decimal comma)" if used == "," else " (decimal point)"
        if unit:
            change += f", unit '{_clip(unit, MAX_CELL_CHARS)}' removed"
        if rounded:
            change = _with_notice(change, rounded_note(rounded))
    else:
        if kind == "datetime":
            return _reread_dates(frame, op, present, carried)
        converted, failed, with_time, zone_notice = _to_dates(series, op.date_format)
        _check_failed(op.column, failed, present, "dates")
        result[op.column] = converted
        carried.with_time[op.column] = with_time
        carried.date_order.pop(op.column, None)
        year_first = op.date_format is None and any(
            isinstance(text, str) and _YEAR_FIRST.match(text) for text in _texts(series)
        )
        if op.date_format in (None, "MM/DD/YYYY", *_DAY_FIRST_FORMATS) and not year_first and _order_open(converted):
            # Every day is at most 12: the cells read the other way too, so a later request may still swap them.
            carried.date_order[op.column] = "month" if op.date_format == "MM/DD/YYYY" else "day"
        if op.date_format == "YYYY":
            # A number column of 1450, 1890 and 2100 reads as years too: the change line says so, the user checks it.
            change = f"{op.column}: {_count(present - failed, 'cell')} read as years (YYYY, each as 1 January)"
        else:
            # The cells that were read decide the wording; an unreadable one is counted below.
            read = converted.notna()
            texts = [text for text, ok in zip(_texts(series), read, strict=True) if ok and isinstance(text, str)]
            year_cells = sum(1 for text in texts if _YEAR_FIRST.match(text))
            how: str
            if op.date_format:
                how = op.date_format
            elif year_cells == len(texts):
                how = "format inferred, year first"  # `2024-06-01` is 1 June, no day-before-month guess
            elif year_cells:
                how = "format inferred, year first where a cell starts with one, else day before month"
            else:
                how = "format inferred, day before month"
            change = f"{op.column}: {_count(present - failed, 'cell')} read as dates ({how})"
    carried.text_columns.discard(op.column)
    if failed:
        verb = "is" if failed == 1 else "are"
        change += f", {_count(failed, 'cell')} could not be read and {verb} now missing"
    return result, _with_notice(change, zone_notice)


def _reread_dates(frame: pd.DataFrame, op: SetType, present: int, carried: _Carried) -> tuple[pd.DataFrame, str]:
    """A datetime column asked for a date format: nothing to read, except the order of day and month when it is a guess.

    A column whose order is open (`_Carried.date_order`: the parser's slash guess, its
    `AMBIGUOUS_DATE_ORDER` warning, or a `set_type` read whose every day is at most 12,
    kept from version to version through `Prepared.date_notes`) is read in the other
    order when the format asks for it: `MM/DD/YYYY` on a column read day first, and
    `DD/MM/YYYY` or `DD.MM.YYYY` on one read month first, so a wrong choice can be taken
    back (review of 2026-10-15). Day and month swap in every cell. A column whose order
    is settled (ISO, or a day over 12) is left as it is.
    """
    order = carried.date_order.get(op.column)
    wanted = "month" if op.date_format == "MM/DD/YYYY" else "day" if op.date_format in _DAY_FIRST_FORMATS else None
    if order is None or wanted is None or wanted == order or not present:
        return frame, f"{op.column}: already dates, nothing changed"
    series = frame[op.column]
    swapped = [
        value.replace(month=value.day, day=value.month) if isinstance(value, pd.Timestamp) else None for value in series
    ]
    result = frame.copy()
    result[op.column] = pd.Series(swapped, index=series.index, dtype=series.dtype)
    carried.date_order[op.column] = wanted
    return result, (
        f"{op.column}: {_count(present, 'cell')} re-read as dates ({op.date_format}, day and month swapped)"
    )


def _order_open(dates: pd.Series) -> bool:
    """Whether every date's day is at most 12 and some day differs from its month: the cells read the other way too."""
    present = [value for value in dates if isinstance(value, pd.Timestamp)]
    return bool(present) and all(value.day <= 12 for value in present) and any(v.day != v.month for v in present)


def _aggregate(frame: pd.DataFrame, op: Aggregate, carried: _Carried) -> tuple[pd.DataFrame, str]:
    keys = _distinct(op.by)
    for name in [*keys, op.column]:
        _require(frame, name)
    if op.column in keys:
        raise PrepareError("invalid_operation", f"column '{op.column}' cannot be both a key and the value")
    date_keys = [name for name in keys if _kind(frame[name]) == "datetime"]
    if op.period and not date_keys:
        raise PrepareError("invalid_operation", "a period needs a datetime column among the keys")
    value_kind = _kind(frame[op.column])
    if op.how in ("sum", "mean") and value_kind not in ("number", "boolean"):
        raise PrepareError("type_mismatch", f"column '{op.column}' is {value_kind}; {op.how} needs a number column")
    value_name = "count" if op.how == "count" else op.column
    if value_name in keys:
        raise PrepareError("invalid_operation", f"a key column is already named '{value_name}'")

    work = frame[[*keys, op.column]].copy()
    if op.period in DATE_PERIODS:
        for name in date_keys:
            work[name] = _period_starts(work[name], op.period)
    elif op.period:
        for name in date_keys:
            work[name] = _period_labels(work[name], op.period)
    if value_kind == "boolean" and op.how in ("sum", "mean"):
        work[op.column] = work[op.column].astype("Int64")
    grouped = work.groupby(keys, dropna=False, sort=True)[op.column]
    rounded = cast = 0
    match op.how:
        case "sum" if is_integer_dtype(work[op.column].dtype):
            # In Python integers: pandas' Int64 sum wraps around silently past 2**63 (review of 2026-10-15).
            # Summed outside pandas, which would infer a dtype for the totals; the groups come in the order of `size`.
            totals = [sum(int(value) for value in values.dropna()) for _, values in grouped]
            aggregated, rounded = _whole_numbers(totals, grouped.size().index)
        case "sum":
            aggregated = grouped.sum()
        case "mean":
            aggregated = grouped.mean()
            if is_integer_dtype(work[op.column].dtype):  # a mean is a float: inputs past 2**53 are counted
                cast = _past_exact(work[op.column])
        case "count":
            aggregated = grouped.count()
        case "min":
            aggregated = grouped.min()
        case "max":
            aggregated = grouped.max()
    result = aggregated.reset_index()
    result.columns = pd.Index([*keys, value_name])
    carried.keep_only([*keys, value_name])
    carried.mixed.pop(value_name, None)  # the cells are new values now, not the ones written both ways
    if op.period in DATE_PERIODS:
        # Each key is the bucket's first moment: a date for a day or an ISO week (its Monday), a time for an hour.
        carried.forget(date_keys)
        carried.with_time.update(dict.fromkeys(date_keys, op.period == "hour"))
    elif op.period:
        carried.forget(date_keys)  # period labels are text now

    period = _PERIOD_WORDS.get(op.period, op.period) if op.period else ""
    zones = sorted({str(frame[name].dt.tz) for name in date_keys if frame[name].dt.tz is not None})
    if op.period in DATE_PERIODS and zones:
        period += f", by the clock of {', '.join(zones)}"  # the column's own offset decides where a day ends
    by = " and ".join(keys) + (f" ({period})" if period else "")
    change = f"{_VERBS[op.how]} {op.column} by {by}: {_count(len(result), 'row')}"
    other = frame.shape[1] - len(keys) - 1
    if other:
        change += f", {_count(other, 'other column')} dropped"
    if cast:
        return result, _with_notice(change, cast_note(cast, f"in {op.column}"))
    return result, _with_notice(change, whole_rounded(rounded) if rounded else "")


def _sort(frame: pd.DataFrame, op: Sort) -> tuple[pd.DataFrame, str]:
    _require(frame, op.column)
    series = frame[op.column]
    order = "descending" if op.descending else "ascending"
    if _kind(series) == "text" and named_months([value for value in series if isinstance(value, str)]):
        ordered = frame.sort_values(
            op.column,
            ascending=not op.descending,
            kind="stable",
            na_position="last",
            key=lambda column: column.map(lambda value: month_number(value) if isinstance(value, str) else None),
        )
        return ordered.reset_index(drop=True), f"sorted by {op.column}, {order}, in calendar order of the months"
    try:
        ordered = frame.sort_values(op.column, ascending=not op.descending, kind="stable", na_position="last")
    except TypeError:
        raise PrepareError(
            "type_mismatch", f"column '{op.column}' mixes kinds of values and cannot be sorted"
        ) from None
    return ordered.reset_index(drop=True), f"sorted by {op.column}, {order}"


def _pivot_longer(frame: pd.DataFrame, op: PivotLonger, carried: _Carried) -> tuple[pd.DataFrame, str]:
    columns = _distinct(op.columns)
    for name in columns:
        _require(frame, name)
    if len(columns) < 2:
        raise PrepareError("invalid_operation", "pivot_longer needs at least two different columns")
    if op.names_to == op.values_to:
        raise PrepareError("invalid_operation", "names_to and values_to must differ")
    rest = [str(name) for name in frame.columns if name not in columns]
    for name in (op.names_to, op.values_to):
        if name in rest:
            raise PrepareError("invalid_operation", f"a column named '{name}' already exists; choose another name")
    rows = len(frame) * len(columns)
    if rows > MAX_ROWS:
        raise PrepareError(
            "invalid_operation", f"pivoting {len(columns)} columns would give {rows:,} rows; at most {MAX_ROWS:,} fit"
        )
    kinds = {_kind(frame[name]) for name in columns}
    times = [_with_time(frame[name], carried) for name in columns]
    work = frame
    rounded = 0
    dotted = all(name in carried.dotted for name in columns)
    forms, respelled = _melted_forms(frame, columns, carried, dotted)
    respelled += sum(carried.mixed.get(name, 0) for name in columns)  # a source column's own two forms
    if len(kinds) > 1:
        # Unlike kinds melt into one text column: each column's canonical texts, a datetime with its time.
        work = frame.assign(
            **{name: _texts(frame[name], time, carried.form(name)) for name, time in zip(columns, times, strict=True)}
        )
    elif kinds == {"number"} and len({is_integer_dtype(frame[name].dtype) for name in columns}) > 1:
        # Whole numbers beside decimals share one float64 column, which rounds a whole number past 2**53: counted.
        whole = [name for name in columns if is_integer_dtype(frame[name].dtype)]
        rounded = sum(_past_exact(frame[name]) for name in whole)
        work = frame.assign(**{name: frame[name].astype("float64") for name in whole})
    melted = work.melt(id_vars=rest, value_vars=columns, var_name=op.names_to, value_name=op.values_to)
    # The melted column stays text through the re-parse when a source was kept text by request
    # (ids that look like numbers) or unlike kinds were written as text: by content it could type again.
    explicit_text = any(name in carried.text_columns for name in columns)
    carried.forget(columns)
    if explicit_text or len(kinds) > 1:
        carried.text_columns.add(op.values_to)
    if kinds == {"datetime"}:
        carried.with_time[op.values_to] = any(bool(time) for time in times)
    if kinds == {"number"}:
        # Each whole number keeps the form its column wrote it in; the melted column's own form is `.0` only when
        # every source column's was.
        carried.forms[op.values_to] = forms
        if dotted:
            carried.dotted.add(op.values_to)
    change = f"pivoted {len(columns)} columns into {op.names_to}/{op.values_to}: {_count(rows, 'row')}"
    notices = []
    if rounded:
        notices.append(cast_note(rounded, f"beside the decimals of {op.values_to}"))
    if kinds == {"number"} and respelled:
        notices.append(
            f"{_count(respelled, 'whole number')} that the columns wrote both with and without '.0' "
            f"written {'with' if dotted else 'without'} it"
        )
    return melted, _with_notice(change, ", ".join(notices))


def _melted_forms(
    frame: pd.DataFrame, columns: list[str], carried: _Carried, dotted: bool
) -> tuple[dict[float, bool], int]:
    """The forms of the whole numbers of `columns` melted into one column, and the cells whose form changes.

    A whole number keeps the form its column wrote it in (`_Carried.form`; a whole-number column writes `7`). A
    number that one column wrote `2.0` and another `2` can have one form only, the melted column's (`dotted`): the
    cells written the other way are counted for the change line (owner rule of 2026-10-15).
    """
    sources: list[tuple[str, bool, Mapping[float, bool]]] = []
    merged: dict[float, bool] = {}
    clashing: set[float] = set()
    for name in columns:
        if _kind(frame[name]) != "number":
            continue
        own, held = carried.form(name)
        if is_integer_dtype(frame[name].dtype):
            own, held = False, {}
        sources.append((name, own, held))
        for value in frame[name].dropna():
            number = float(value)
            if number.is_integer() and abs(number) < _FLOAT_EXACT:
                form = held.get(number, own)
                if merged.setdefault(number, form) != form:
                    clashing.add(number)
    respelled = 0
    for name, own, held in sources:
        for value in frame[name].dropna():
            number = float(value)
            if number in clashing and held.get(number, own) != dotted:
                respelled += 1
    return {number: form for number, form in merged.items() if number not in clashing}, respelled


def _pivot_wider(frame: pd.DataFrame, op: PivotWider, carried: _Carried) -> tuple[pd.DataFrame, str]:
    index = _distinct(op.index)
    for name in [*index, op.names_from, op.values_from]:
        _require(frame, name)
    if op.names_from == op.values_from or op.names_from in index or op.values_from in index:
        raise PrepareError("invalid_operation", "names_from, values_from and the index must be different columns")
    work = frame[[*index, op.names_from, op.values_from]]
    without_name = work[op.names_from].isna()
    left_out = int(without_name.sum())
    work = work[~without_name]
    if not len(work):
        raise PrepareError("empty_result", f"every cell of column '{op.names_from}' is missing")
    names = _texts(work[op.names_from], _with_time(work[op.names_from], carried), carried.form(op.names_from))
    values_time = _with_time(work[op.values_from], carried)
    distinct = [str(name) for name in names.unique()]
    if len(distinct) > MAX_WIDER_COLUMNS:
        raise PrepareError(
            "too_wide",
            f"column '{op.names_from}' has {len(distinct)} distinct values; at most {MAX_WIDER_COLUMNS} new columns fit",
        )
    if len(index) + len(distinct) > MAX_COLUMNS:
        raise PrepareError(
            "too_wide", f"the result would have {len(index) + len(distinct)} columns; at most {MAX_COLUMNS} fit"
        )
    if any(name in index for name in distinct):
        raise PrepareError("invalid_operation", f"a value of column '{op.names_from}' is named like an index column")
    work = work.assign(**{op.names_from: names})
    try:
        wide = work.pivot(index=index, columns=op.names_from, values=op.values_from)
    except ValueError:
        raise PrepareError(
            "invalid_operation",
            f"the pairs of {' and '.join(index)} and {op.names_from} are not unique; aggregate first",
        ) from None
    wide = wide.reset_index()
    wide.columns = pd.Index([str(name) for name in wide.columns])
    values_text = op.values_from in carried.text_columns  # the new columns hold its cells: they stay text too
    values_dotted, values_forms = carried.form(op.values_from)  # and write its whole numbers as it did
    carried.keep_only(index)
    if values_text:
        carried.text_columns.update(distinct)
    if values_dotted:
        carried.dotted.update(distinct)
    if values_forms:
        carried.forms.update({name: dict(values_forms) for name in distinct})
    if values_time is not None:
        carried.with_time.update(dict.fromkeys(distinct, values_time))
    change = f"pivoted {op.names_from} into {_count(len(distinct), 'column')} with values from {op.values_from}: "
    change += _count(len(wide), "row")
    if left_out:
        change += f", {_count(left_out, 'row')} without a {op.names_from} left out"
    other = frame.shape[1] - len(index) - 2
    if other:
        change += f", {_count(other, 'other column')} dropped"
    return wide, change


def _classify(frame: pd.DataFrame, op: Classify, carried: _Carried) -> tuple[pd.DataFrame, str]:
    if op.name in frame.columns:
        raise PrepareError("invalid_operation", f"a column named '{op.name}' already exists")
    if frame.shape[1] >= MAX_COLUMNS:
        raise PrepareError("too_wide", f"the data already has {frame.shape[1]} columns; at most {MAX_COLUMNS} fit")
    labels = pd.Series(None, index=frame.index, dtype="object")
    open_rows = pd.Series(True, index=frame.index)
    parts: list[str] = []
    for rule in op.rules:
        mask = pd.Series(True, index=frame.index)
        clauses: list[str] = []
        for condition in rule.where:
            _require(frame, condition.column)
            series = frame[condition.column]
            mask &= _matches(series, condition, _with_time(series, carried), carried.form(condition.column))
            clauses.append(_describe(condition, _kind(series)))
        hit = mask & open_rows  # the first rule that holds names a row
        labels[hit] = rule.label
        open_rows &= ~hit
        parts.append(f"'{rule.label}' for {_count(int(hit.sum()), 'row')} where {' and '.join(clauses)}")
    rest = int(open_rows.sum())
    if rest and op.otherwise is not None:
        labels[open_rows] = op.otherwise
        parts.append(f"'{op.otherwise}' for the other {_count(rest, 'row')}")
    elif rest:
        parts.append(f"{_count(rest, 'row')} without a label")
    if not labels.notna().any():
        raise PrepareError("invalid_operation", f"no row matches a rule, so column '{op.name}' would hold no label")
    # Kept text through the re-parse: labels such as `1` and `2` are categories, not numbers.
    carried.text_columns.add(op.name)
    return frame.assign(**{op.name: labels}), f"added column {op.name}: {', '.join(parts)}"


def _derive(frame: pd.DataFrame, op: Derive, carried: _Carried) -> tuple[pd.DataFrame, str]:
    if op.name in frame.columns:
        raise PrepareError("invalid_operation", f"a column named '{op.name}' already exists")
    if frame.shape[1] >= MAX_COLUMNS:
        raise PrepareError("too_wide", f"the data already has {frame.shape[1]} columns; at most {MAX_COLUMNS} fit")
    columns, keys = list(op.columns), _distinct(op.within)
    low, high = _DERIVE_ARITY[op.how]
    if not low <= len(columns) <= high:
        wanted = str(low) if low == high else f"{low} to {high}"
        raise PrepareError("invalid_operation", f"derive {op.how} takes {wanted} columns, not {len(columns)}")
    if len(set(columns)) != len(columns):
        raise PrepareError("invalid_operation", f"derive {op.how} needs different columns")
    for name in [*columns, *keys, *([op.order] if op.order else [])]:
        _require(frame, name)
    grouped = op.how == "share" or op.how in ORDERED
    if not grouped and (keys or op.order):
        raise PrepareError("invalid_operation", f"derive {op.how} works within one row; it takes no within or order")
    if op.how == "share" and op.order:
        raise PrepareError("invalid_operation", "derive share takes no order")
    if op.how in ORDERED and not op.order:
        raise PrepareError("invalid_operation", f"derive {op.how} needs an order column, such as a date or year")
    if op.percent and op.how not in ("ratio", "share"):
        raise PrepareError(
            "invalid_operation",
            f"percent applies to a ratio or a share, not to a {op.how} (a percent change is in percent)",
        )
    if set(columns) & {*keys, *([op.order] if op.order else [])}:
        raise PrepareError("invalid_operation", "a value column cannot also be a within or order column")
    for name in columns:
        kind = _kind(frame[name])
        if kind != "number":
            raise PrepareError("type_mismatch", f"column '{name}' is {kind}; derive {op.how} needs number columns")
    if op.how in ("difference", "sum") and all(is_integer_dtype(frame[name].dtype) for name in columns):
        # Whole numbers stay exact: a float64 holds integers only up to 2**53.
        result, rounded = _integer_result(frame, columns, op.how)
        what = f"{columns[0]} - {columns[1]}" if op.how == "difference" else f"sum of {', '.join(columns)}"
        return _derived(frame, op, result, what, "", carried, notice=whole_rounded(rounded) if rounded else "")
    values = [frame[name].astype("float64") for name in columns]
    # A float result reads its whole-number inputs as float64: past 2**53 that is counted, never silent (review of #12196).
    cast = sum(_past_exact(frame[name]) for name in columns if is_integer_dtype(frame[name].dtype))
    note = ""
    match op.how:
        case "ratio":
            result = values[0] / values[1].where(values[1] != 0)
            what = f"{columns[0]} / {columns[1]}"
        case "difference":
            result = values[0] - values[1]
            what = f"{columns[0]} - {columns[1]}"
        case "sum":
            result = pd.concat(values, axis=1).sum(axis=1, min_count=1)
            what = f"sum of {', '.join(columns)}"
        case "share":
            if keys:
                total = values[0].groupby([frame[key] for key in keys], dropna=False).transform("sum")
            else:
                total = pd.Series(values[0].sum(), index=frame.index)
            # A total that overflowed to infinity would give finite shares of 0: no share for its group instead.
            result = values[0] / total.where((total != 0) & np.isfinite(total))
            what = f"share of {columns[0]} in the total" + (f" of each {' and '.join(keys)}" if keys else "")
        case "percent_change" | "cumsum" | "index":
            result, what, notice = _ordered(frame, values[0], columns[0], keys, str(op.order), op.how)
            if frame[str(op.order)].isna().any():
                note = f"a row without a {op.order}, "
            if op.how == "percent_change":
                note = "the first row of each group, " + note
            if is_integer_dtype(result.dtype) or notice:  # an exact running total of whole numbers (`_integer_cumsum`)
                return _derived(frame, op, result, what, note, carried, notice=notice)
    if op.percent:
        result = result * 100
        what += ", in percent"
    result = result.where(np.isfinite(result)).astype("float64")
    return _derived(frame, op, result, what, note, carried, notice=cast_note(cast, "in the inputs") if cast else "")


def _derived(
    frame: pd.DataFrame, op: Derive, result: pd.Series, what: str, note: str, carried: _Carried, notice: str = ""
) -> tuple[pd.DataFrame, str]:
    """The frame with the derived column appended, and its change line counting the empty cells.

    `notice` is a loss the line must always show (values stored rounded): it is kept whole and
    the rest of the line is shortened instead (`_with_notice`).
    """
    present = int(result.notna().sum())
    if not present:
        raise PrepareError("invalid_operation", f"no row has a value for column '{op.name}'; check the input columns")
    change = f"added column {op.name}: {what}"
    empty = len(result) - present
    if empty:
        verb = "is" if empty == 1 else "are"
        change += f", {_count(empty, 'cell')} {verb} empty ({note}a missing input or a division by zero)"
    carried.forget([op.name])
    return frame.assign(**{op.name: result}), _with_notice(change, notice)


def _with_notice(change: str, notice: str) -> str:
    """`change` with `notice` appended, the notice never cut: `apply_operations` clips every line to
    `MAX_NOTE_CHARS`, and a rounding count lost to the clip would be a silent loss again (review of #12196)."""
    if not notice:
        return change
    return f"{_clip(change, MAX_NOTE_CHARS - len(notice) - 2)}, {notice}"


def _integer_result(frame: pd.DataFrame, columns: list[str], how: str) -> tuple[pd.Series, int]:
    """A difference or a row sum of whole-number columns in Python integers, see `_whole_numbers`."""
    rows = zip(*([None if pd.isna(value) else int(value) for value in frame[name]] for name in columns), strict=True)
    results: list[int | None] = []
    for row in rows:
        present = [value for value in row if value is not None]
        if how == "difference":
            results.append(None if len(present) < 2 else present[0] - present[1])
        else:
            results.append(sum(present) if present else None)
    return _whole_numbers(results, frame.index)


def _whole_numbers(results: Sequence[int | None], index: pd.Index) -> tuple[pd.Series, int]:
    """Exact whole-number results as `Int64`; past its range float64, with the count of values it rounds.

    A float64 holds whole numbers exactly only up to 2**53, so once one result leaves the
    int64 range the column is float64 and every result past 2**53 is written as a float:
    rounded, or exact but in another form (2**63 as `9.223372036854776e+18`, review of
    #12196). The count of those goes into the change line (`whole_rounded`), never
    silently (owner rule of 2026-10-15).
    """
    if all(value is None or _INT64_MIN <= value <= _INT64_MAX for value in results):
        return pd.Series(pd.array(results, dtype="Int64"), index=index), 0
    floats = [np.nan if value is None else float(value) for value in results]
    return pd.Series(floats, index=index, dtype="float64"), _past_exact(results)


def _past_exact(values: Iterable[Any]) -> int:
    """How many whole numbers are past 2**53, which a float64 holds rounded or only in another form."""
    count = 0
    for value in values:
        if value is not None and not pd.isna(value) and abs(int(value)) > _FLOAT_EXACT:
            count += 1
    return count


_FLOAT_EXACT = 2**53


def cast_note(count: int, where: str) -> str:
    """The change-line clause of whole numbers past 2**53 that a float computation or column takes as decimals."""
    return (
        f"{_count(count, 'whole number')} past 2^53 {where} {_be(count)} read as decimal numbers "
        "(15 to 17 significant digits; a digit past them is rounded)"
    )


def whole_rounded(count: int) -> str:
    """The change-line clause of whole numbers past 2**53 written as floats once a column left the int64 range."""
    return (
        f"{_count(count, 'whole number')} past 2^53 {_be(count)} stored as decimal numbers, since a result left "
        "the 64-bit whole-number range (15 to 17 significant digits; a digit past them is rounded)"
    )


def _integer_cumsum(frame: pd.DataFrame, column: str, keys: list[str], ordered: pd.Index) -> tuple[pd.Series, int]:
    """The running total of a whole-number column in Python integers, in the order `ordered`, within each group.

    A missing cell adds nothing and keeps an empty cell, as pandas' `cumsum` does; a row
    outside `ordered` (no order value) stays empty.
    """
    wholes = {row: None if pd.isna(value) else int(value) for row, value in frame[column].items()}
    totals: dict[tuple[object, ...], int] = {}
    running: dict[object, int | None] = {}
    for row in ordered:
        whole = wholes[row]
        if whole is None:
            running[row] = None
            continue
        # Native key values group as pandas does (`-0.0` with `0.0`); every missing kind is one group (`dropna=False`).
        group = tuple(None if pd.isna(value := frame.at[row, key]) else value for key in keys)
        totals[group] = totals.get(group, 0) + whole
        running[row] = totals[group]
    return _whole_numbers([running.get(row) for row in frame.index], frame.index)


def _ordered(
    frame: pd.DataFrame, values: pd.Series, column: str, keys: list[str], order: str, how: str
) -> tuple[pd.Series, str, str]:
    """`percent_change`, `cumsum` or `index` of `values` within each group, in the order of `order`, what it
    computed, and the notice of values stored rounded (an integer running total past int64), else "".

    The order column holds numbers or dates: a text column would sort alphabetically
    (`April` before `Januar`, `10` before `9`) and give a silently wrong result. A row
    without an order value has no place in the order: its cell stays empty and it is
    skipped by its group's other rows. Two rows of a group with the same order value
    make "previous" a guess and are refused.
    """
    kind = _kind(frame[order])
    if kind not in ("number", "datetime"):
        raise PrepareError(
            "type_mismatch",
            f"column '{order}' is {kind} and would sort alphabetically; derive {how} needs a number or datetime "
            "order column: set_type it to number or datetime first",
        )
    placed = frame[frame[order].notna()]
    within = f" within each {' and '.join(keys)}" if keys else ""
    if placed.duplicated(subset=[*keys, order]).any():
        raise PrepareError(
            "invalid_operation",
            f"column '{order}' repeats a value{within}, so the order of the rows is unclear; aggregate first",
        )
    ordered = placed.sort_values(order, kind="stable").index
    current = values.loc[ordered]
    groups = [frame[key].loc[ordered] for key in keys]
    if how == "percent_change":
        previous = current.groupby(groups, dropna=False).shift(1) if keys else current.shift(1)
        result = (current - previous) / previous.where(previous != 0) * 100
        what = f"percent change of {column} from the previous {order}{within}"
    elif how == "cumsum":
        what = f"running total of {column} in the order of {order}{within}"
        if is_integer_dtype(frame[column].dtype):
            # Whole numbers add up exactly: a float64 running total rounds past 2**53.
            exact, rounded = _integer_cumsum(frame, column, keys, ordered)
            return exact, what, whole_rounded(rounded) if rounded else ""
        result = current.groupby(groups, dropna=False).cumsum() if keys else current.cumsum()
    else:
        if keys:  # `first` takes the group's first value that is there
            base = current.groupby(groups, dropna=False).transform("first")
        else:
            present = current.dropna()
            base = pd.Series(present.iloc[0] if len(present) else np.nan, index=current.index)
        result = current / base.where(base != 0) * 100
        what = f"index of {column}, the first {order}{within} = 100"
    return result.reindex(frame.index), what, ""


def _make_date(frame: pd.DataFrame, op: MakeDate, carried: _Carried) -> tuple[pd.DataFrame, str]:
    """A date column from whole-number part columns; refused on a value out of range or a row that is no calendar date."""
    if op.name in frame.columns:
        raise PrepareError("invalid_operation", f"a column named '{op.name}' already exists")
    if frame.shape[1] >= MAX_COLUMNS:
        raise PrepareError("too_wide", f"the data already has {frame.shape[1]} columns; at most {MAX_COLUMNS} fit")
    if op.day and not op.month:
        raise PrepareError("invalid_operation", "make_date with a day needs a month column too")
    if op.quarter and (op.month or op.day or op.week):
        raise PrepareError("invalid_operation", "make_date with a quarter takes only a year besides it")
    if op.week and (op.month or op.day):
        raise PrepareError("invalid_operation", "make_date with a week takes only a year besides it")
    optional: tuple[tuple[DatePart, str | None], ...] = (
        ("month", op.month),
        ("day", op.day),
        ("quarter", op.quarter),
        ("week", op.week),
    )
    parts: dict[DatePart, str] = {"year": op.year}
    for part, column in optional:
        if column:
            parts[part] = column
    if len(set(parts.values())) != len(parts):
        raise PrepareError("invalid_operation", "make_date needs a different column for each part")
    values = {part: _date_parts(frame, column, part) for part, column in parts.items()}
    dates: list[datetime | None] = []
    impossible = 0
    for row in zip(*values.values(), strict=True):
        named = dict(zip(parts, row, strict=True))
        if any(value is None for value in row):
            dates.append(None)
            continue
        year = int(named["year"] or 0)
        try:
            if "week" in named:
                moment = datetime.fromisocalendar(year, int(named["week"] or 0), 1)
            elif "quarter" in named:
                moment = datetime(year, 3 * (int(named["quarter"] or 0) - 1) + 1, 1)
            else:
                moment = datetime(year, int(named.get("month") or 1), int(named.get("day") or 1))
        except ValueError:
            impossible += 1
            dates.append(None)
            continue
        dates.append(moment)
    if impossible:
        raise PrepareError(
            "invalid_operation",
            f"{_count(impossible, 'row')} of {_listed(list(parts.values()))} "
            f"{'is' if impossible == 1 else 'are'} no calendar date, such as 31 April or week 53 of a year with 52 weeks",
        )
    result = pd.Series(dates, index=frame.index, dtype="datetime64[us]")
    empty = int(result.isna().sum())
    if empty == len(result):
        raise PrepareError("invalid_operation", f"no row has every part, so column '{op.name}' would hold no date")
    carried.forget([op.name])
    carried.with_time[op.name] = False
    first = {
        # ISO 8601: week 1 holds the year's first Thursday, so it can start in late December (2025-W01 is 2024-12-30).
        "week": "the Monday of each ISO week; week 1 can start in late December of the year before",
        "quarter": "the first day of each quarter",
        "month": "the first day of each month",
        "year": "1 January of each year",
    }
    change = f"added column {op.name}: dates from {_listed(list(parts.values()))}"
    if "day" not in parts:
        change += f" ({next(text for part, text in first.items() if part in parts)})"
    if empty:
        verb = "is" if empty == 1 else "are"
        change += f", {_count(empty, 'cell')} {verb} empty (a missing part)"
    return frame.assign(**{op.name: result}), change


def _date_parts(frame: pd.DataFrame, column: str, part: DatePart) -> list[int | None]:
    """The cells of `column` as whole numbers within the range of `part`; raises when a value is no whole number or out of range."""
    _require(frame, column)
    series = frame[column]
    kind = _kind(series)
    if kind == "text" and part == "month":
        return _month_names(series, column)
    if kind != "number":
        raise PrepareError(
            "type_mismatch",
            f"column '{column}' is {kind}; make_date needs whole numbers as the {part}: set_type it to number first",
        )
    low, high = DATE_PART_RANGES[part]
    values: list[int | None] = []
    fractional = outside = 0
    for value in series:
        if pd.isna(value):
            values.append(None)
            continue
        number = float(value)
        if not number.is_integer():
            fractional += 1
        elif not low <= number <= high:
            outside += 1
        values.append(int(number) if number.is_integer() else None)
    if fractional:
        raise PrepareError(
            "type_mismatch",
            f"column '{column}' holds {_count(fractional, 'value')} that {_be(fractional)} no whole number",
        )
    if outside:
        what = "a year of four digits" if part == "year" else f"a {part}"
        raise PrepareError(
            "invalid_operation",
            f"column '{column}' holds {_count(outside, 'value')} outside {low} to {high}, so it is not {what}",
        )
    return values


def _month_names(series: pd.Series, column: str) -> list[int | None]:
    """A text column of months as numbers: a name or abbreviation (`MONTH_NAMES`), `3月`, `tháng 3`, or digits 1 to 12.

    Compared without case and diacritics, and without a trailing dot (`Jan.`, `März`, `févr.`);
    one cell that is no month refuses the operation: an unknown name is never guessed.
    """
    values: list[int | None] = []
    unknown = 0
    for value in series:
        if not isinstance(value, str):
            values.append(None)
            continue
        month = month_number(value)
        if month is None:
            unknown += 1
        values.append(month)
    if unknown:
        raise PrepareError(
            "type_mismatch",
            f"column '{column}' holds {_count(unknown, 'value')} that {_be(unknown)} no month name or number from 1 to 12",
        )
    return values


# --- Conditions ------------------------------------------------------------------------------


def _matches(
    series: pd.Series,
    condition: Condition,
    with_time: bool | None,
    form: tuple[bool, Mapping[float, bool]] = (False, {}),
) -> pd.Series:
    """The rows of `series` that satisfy `condition`, as booleans; a missing cell matches only `is_missing`.

    `contains` searches each cell's canonical text as `_write` writes it, a whole number in its `form`."""
    column, test, value = condition.column, condition.test, condition.value
    if test == "is_missing":
        if value is not None:
            raise PrepareError("invalid_operation", f"the condition is_missing on column '{column}' takes no value")
        return series.isna()
    if value is None:
        raise PrepareError("invalid_operation", f"the condition {test} on column '{column}' needs a value")
    if not value:
        raise PrepareError(
            "invalid_operation",
            f"the condition {test} on column '{column}' needs a value; is_missing finds empty cells",
        )
    if test == "contains":
        return _bools(_texts(series, with_time, form).str.contains(value, regex=False))
    kind = _kind(series)
    target: object
    if kind == "number" and is_integer_dtype(series.dtype):
        return _whole_matches(series, test, value, column)
    if kind == "number":
        target = _number(value, column)
    elif kind == "datetime":
        target = _moment(value, column, series.dt.tz)
    elif kind == "boolean":
        if value.casefold() not in ("true", "false"):
            raise PrepareError("invalid_operation", f"the value for column '{column}' must be true or false")
        if test in ("gt", "lt"):
            raise PrepareError("invalid_operation", f"column '{column}' is boolean; {test} does not apply")
        target = value.casefold() == "true"
    else:
        target = value
    if test == "eq":
        return _bools(series == target)
    if test == "ne":
        return _bools(series != target) & series.notna()
    if test == "gt":
        return _bools(series > target)
    return _bools(series < target)


def _describe(condition: Condition, kind: Kind) -> str:
    if condition.test == "is_missing":
        return f"{condition.column} is missing"
    shown = _clip(condition.value or "", MAX_CELL_CHARS)
    if condition.test == "contains":
        return f"{condition.column} contains '{shown}'"
    if kind == "text":
        shown = f"'{shown}'"
    return f"{condition.column} {_TEST_SIGNS[condition.test]} {shown}"


def _number(value: str, column: str) -> float:
    text = value.strip()
    if not _NUMBER.fullmatch(text) or not math.isfinite(float(text)):
        raise PrepareError("invalid_operation", f"the value for column '{column}' is not a number (use a dot decimal)")
    return float(text)


def _whole_matches(series: pd.Series, test: str, value: str, column: str) -> pd.Series:
    """A condition on a whole-number column, compared exactly: a float64 value would make `9007199254740993`
    equal `9007199254740992` (review of #12196).

    The value is read as an exact decimal. A whole value compares as a Python integer; a
    value with a fraction is never equal to a cell, and `gt` / `lt` compare with the
    whole number below or above it (`gt 2.5` is `gt 2`, `lt 2.5` is `lt 3`).
    """
    _number(value, column)  # the same refusal as any number column for a value that is no number
    exact = ExactDecimal(value.strip())
    present = series.notna()
    if exact == exact.to_integral_value():
        whole = int(exact)
        if not _INT64_MIN <= whole <= _INT64_MAX:  # past every cell: equal to none, above or below all
            above = whole > _INT64_MAX
            hit = test == "ne" or (test == "lt" and above) or (test == "gt" and not above)
            return present.astype(bool) if hit else pd.Series(False, index=series.index)
        if test == "eq":
            return _bools(series == whole)
        if test == "ne":
            return _bools(series != whole) & present
        return _bools(series > whole) if test == "gt" else _bools(series < whole)
    if test == "eq":
        return pd.Series(False, index=series.index)
    if test == "ne":
        return present.astype(bool)
    floor = int(exact.to_integral_value(rounding=ROUND_FLOOR))
    return _bools(series > floor) if test == "gt" else _bools(series < floor + 1)


def _moment(value: str, column: str, zone: tzinfo | None = None) -> pd.Timestamp:
    """The ISO date or date-time of a condition, comparable with the column's cells.

    A column with a UTC offset (`2024-01-01T10:00:00+01:00`, or `Z`) compares moments: a
    value with an offset is converted to the column's offset, a value without one is
    refused, since which zone it means would be a guess. A column without an offset takes
    a value without one; a value with an offset there is refused the same way. Comparing
    the two kinds raised a `TypeError` that crashed the tool (review of #12196).
    """
    try:
        moment = datetime.fromisoformat(value.strip())
    except ValueError:
        raise PrepareError(
            "invalid_operation",
            f"the value for column '{column}' is not an ISO date (YYYY-MM-DD, with an optional time)",
        ) from None
    stamp = pd.Timestamp(moment)
    if zone is None and stamp.tzinfo is not None:
        raise PrepareError(
            "invalid_operation",
            f"column '{column}' holds times without a UTC offset; give the value without one, such as 2024-01-01T10:00",
        )
    if zone is not None and stamp.tzinfo is None:
        raise PrepareError(
            "invalid_operation",
            f"column '{column}' holds times with a UTC offset; give the value with one, such as "
            "2024-01-01T10:00:00+00:00",
        )
    return stamp if zone is None else stamp.tz_convert(zone)


def _bools(mask: pd.Series) -> pd.Series:
    """A comparison result as plain booleans: a missing comparison (a nullable dtype's NA) is False."""
    return mask.fillna(False).astype(bool)


# --- Conversions -----------------------------------------------------------------------------


def _to_numbers(series: pd.Series, decimal: str) -> tuple[pd.Series, str | None, int, str, int]:
    """The cells as numbers (`Int64` when every value is whole, else `float64`), the unit removed, the failures, the decimal used,
    and the cells a float64 holds only rounded (more significant digits than it keeps, see `parse.keeps_value`).

    The cells are read with `decimal` first. When some fail and fewer fail with the
    other mark, the column is written that way (a `12,5 %` column in a dot-decimal
    file, `12.5 %` in a decimal-comma file) and every cell is read with the other mark:
    one decimal per column, never a mix.
    """
    if _kind(series) == "boolean":
        return series.astype("Int64"), None, 0, decimal, 0
    texts = [text if isinstance(text, str) else None for text in _texts(series)]
    numbers, units, failed = _read_numbers(texts, decimal)
    if failed:
        other = "," if decimal == "." else "."
        alternative = _read_numbers(texts, other)
        if alternative[2] < failed:
            (numbers, units, failed), decimal = alternative, other
    if len(units) > 1:
        raise PrepareError("type_mismatch", f"column '{series.name}' mixes {len(units)} different units")
    unit = next(iter(units)) if units else None
    # Whole numbers are read exactly, never through a float64, which rounds past 2**53 (`9007199254740993`).
    exact = [None if number is None else _exact(number) for number in numbers]
    integers = [None if value is None or value != value.to_integral_value() else int(value) for value in exact]
    if all(
        number is None or (integer is not None and _INT64_MIN <= integer <= _INT64_MAX)
        for number, integer in zip(numbers, integers, strict=True)
    ):
        return pd.Series(pd.array(integers, dtype="Int64"), index=series.index), unit, failed, decimal, 0
    values = [None if number is None else float(number) for number in numbers]
    rounded = sum(not keeps_value(number, float(number)) for number in numbers if number is not None)
    return pd.Series(values, index=series.index, dtype="float64"), unit, failed, decimal, rounded


def _exact(number: str) -> ExactDecimal | None:
    """The dot-decimal `number` as an exact decimal; None for an exponent past the decimal module's range
    (`1e-9999999999999999999`, whose float is a finite 0.0): such a cell takes the float path and its count."""
    try:
        return ExactDecimal(number)
    except InvalidOperation:
        return None


def _read_numbers(texts: list[str | None], decimal: str) -> tuple[list[str | None], set[str], int]:
    """Every cell read with `decimal`: the dot-decimal numbers (None for missing and failed cells), the units seen,
    the failures."""
    numbers: list[str | None] = []
    units: set[str] = set()
    failed = 0
    for text in texts:
        if text is None:
            numbers.append(None)
            continue
        number, unit = _read_number(text, decimal)
        if number is None:
            failed += 1
        elif unit:
            units.add(unit)
        numbers.append(number)
    return numbers, units, failed


def _read_number(text: str, decimal: str) -> tuple[str | None, str | None]:
    """One cell as a finite dot-decimal number and the unit token taken off it; `(None, None)` when it cannot be read."""
    body, unit = text.strip(), None
    if _plain_number(body, decimal) is None:
        match = _TRAILING_UNIT.match(body) or _LEADING_UNIT.match(body)
        if match is None:
            return None, None
        body, unit = match.group("body"), match.group("unit").strip()
    number = _plain_number(body, decimal)
    return number, (unit if number is not None else None)


def _plain_number(body: str, decimal: str) -> str | None:
    """`body` read with `decimal` as the parser reads a number, as dot-decimal text without groups; None when it is
    no finite number that way.

    Spaces and apostrophes separate thousands. The other mark does so only between
    three-digit groups (`_GROUPED`); anywhere else it makes the cell unreadable with
    this decimal (`12,5` is no dot-decimal number), so a decimal mark is never dropped.
    The text, not a float, goes back: the caller reads whole numbers exactly.
    """
    thousands = "." if decimal == "," else ","
    cleaned = _SPACES.sub("", body).replace("'", "")
    if _GROUPED[decimal].fullmatch(cleaned):
        cleaned = cleaned.replace(thousands, "")
    elif thousands in cleaned:
        return None
    if decimal == ",":
        cleaned = cleaned.replace(",", ".")
    if not _NUMBER.fullmatch(cleaned):
        return None
    return cleaned if math.isfinite(float(cleaned)) else None


def _to_dates(series: pd.Series, date_format: str | None) -> tuple[pd.Series, int, bool, str]:
    """The cells as datetimes (NaT where a cell cannot be read), how many non-missing cells failed, whether
    the column is written with a time (the parser's rule: any source cell holds a colon), and the notice of
    different UTC offsets converted to UTC, else ""."""
    texts = _texts(series)
    notice = ""
    if date_format == "MM.YYYY" and _kind(series) == "number":
        texts = _month_year_texts(series, texts)
    if date_format:
        # Python's own reader, one cell at a time: any year from 1 to 9999, stored at the parser's microseconds
        # (a datetime64[ns] holds only 1677 to 2262, review of 2026-10-15).
        values = [_read_date(text, date_format) if isinstance(text, str) else None for text in texts]
        result = pd.Series(values, index=series.index, dtype="datetime64[us]")
    else:
        # A year-first cell (`2024-06-01T13:00:00Z`) reads year, month, day: with `dayfirst` pandas would read it as
        # 6 January (review of 2026-10-15). Day before month is for the other shapes only, decided per cell, so one
        # cell of another shape never turns the year-first ones around (review of #12196).
        year_first = texts.map(lambda text: isinstance(text, str) and bool(_YEAR_FIRST.match(text))).astype(bool)
        (first, utc_first), (rest, utc_rest) = (
            _inferred_dates(texts.where(year_first), False, series.name),
            _inferred_dates(texts.where(~year_first), True, series.name),
        )
        converted = utc_first or utc_rest
        read = [part for part in (first, rest) if part.notna().any()]  # an all-unreadable part has no zone
        if len({str(part.dtype) for part in read}) > 1:
            # Two parts in different zones: one column holds one zone, so both are written in UTC.
            if any(part.dt.tz is None for part in read):
                raise _naive_and_zoned(series.name)
            first, rest = (part.dt.tz_convert("UTC") if part.notna().any() else part for part in (first, rest))
            converted = True
        # Each part is NaT outside its own cells: one alone is the result, two of one dtype merge.
        if not rest.notna().any():
            result = first
        elif not first.notna().any():
            result = rest
        else:
            result = first.where(year_first, rest)
        if converted:
            notice = f"times with the UTC offsets {', '.join(_offsets(texts))} converted to UTC (+00:00); "
            notice += "the instants are the same"
    failed = int((result.isna() & texts.notna()).sum())
    with_time = any(":" in text for text in texts if isinstance(text, str))
    return result, failed, with_time, notice


def _inferred_dates(texts: pd.Series, day_first: bool, column: object) -> tuple[pd.Series, bool]:
    """pandas' per-cell format inference over `texts` (missing stays NaT), and whether it converted to UTC.

    Different UTC offsets (summer and winter time) cannot share a column, so they are read in UTC,
    as the parser writes such a column (owner decision of 2026-10-15), and the change line names
    them. Times with and without an offset are refused: no time gets a zone by guess.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            return pd.to_datetime(texts, errors="coerce", format="mixed", dayfirst=day_first), False
        except ValueError:
            pass
        offsets = [_offset_of(text, day_first) for text in texts if isinstance(text, str)]
        if any(offset is None for offset in offsets if offset is not pd.NaT):
            raise _naive_and_zoned(column) from None
        return pd.to_datetime(texts, errors="coerce", format="mixed", dayfirst=day_first, utc=True), True


def _offset_of(text: str, day_first: bool) -> object:
    """One cell's UTC offset as a timedelta, None for a time without one, NaT for a cell that is no date."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        stamp = pd.to_datetime(text, errors="coerce", dayfirst=day_first)
    return stamp.utcoffset() if isinstance(stamp, pd.Timestamp) else pd.NaT


def _offsets(texts: pd.Series) -> list[str]:
    """The distinct UTC offsets of the cells, as `+HH:MM`, in order."""
    found: set[int] = set()
    for text in texts:
        if isinstance(text, str):
            offset = _offset_of(text, not _YEAR_FIRST.match(text))
            if isinstance(offset, timedelta):
                found.add(int(offset.total_seconds() // 60))
    shown = []
    for minutes in sorted(found):
        hours, rest = divmod(abs(minutes), 60)
        shown.append(f"{'-' if minutes < 0 else '+'}{hours:02d}:{rest:02d}")
    return shown


def _naive_and_zoned(column: object) -> PrepareError:
    return PrepareError(
        "type_mismatch",
        f"column '{column}' holds times with a UTC offset and times without one; no time is given a zone by guess, "
        "so the column stays as it is",
    )


def _read_date(text: str, date_format: str) -> datetime | None:
    """One cell in exactly `date_format`, with an optional time after it; None when it is not.

    A compact format takes exactly its digits (`YYYYMMDD` 8, `YYYYMM` 6, `YYYY` 4) and no
    time: `2024115` is no `YYYYMMDD` date, never guessed as 5 November (review of 2026-10-15).
    """
    text = text.strip()
    digits = COMPACT_DIGITS.get(date_format)
    if digits is not None and not (text.isascii() and text.isdigit() and len(text) == digits):
        return None
    for suffix in ("",) if digits is not None else _TIME_SUFFIXES:
        try:
            return datetime.strptime(text, STRPTIME[date_format] + suffix)
        except ValueError:
            continue
    return None


def _month_year_texts(series: pd.Series, texts: pd.Series) -> pd.Series:
    """`MM.YYYY` cells the parser read as numbers (`03.2020` as 3.202), as `m.yyyy` text again; or a refusal.

    Four decimals give the year back, trailing zeros included, but only where they keep the
    value (`03.20249` stays as it is and fails, never rounded into March 2025). An ordinary
    decimal reads the same way (`2.2` as February 2000, `3.5` as March 5000), so the column
    must look like month and year throughout: every month 1 to 12, every year within 1000 to
    2200 and all of them at most 300 years apart (`2.2`, `2.3`, `2.1` give 2000, 3000 and
    1000); otherwise it is a `type_mismatch` (review of 2026-10-15). A single year of monthly
    cells (`01.2020` to `12.2020`, all read without their zeros) passes.
    """
    padded: list[str | None] = []
    parts: list[tuple[int, int]] = []
    for text in texts:
        if not isinstance(text, str):
            padded.append(None)
            continue
        candidate = f"{float(text):.4f}"
        if float(candidate) != float(text):
            padded.append(text)  # more than four decimals: no month.year, it fails as it is
            continue
        padded.append(candidate)
        month, year = candidate.split(".")
        parts.append((int(month), int(year)))
    low, high = MONTH_YEAR_RANGE
    years = [year for _, year in parts]
    plausible = (
        bool(parts)
        and all(1 <= month <= 12 and low <= year <= high for month, year in parts)
        and max(years) - min(years) <= MONTH_YEAR_SPAN
    )
    if not plausible:
        raise PrepareError(
            "type_mismatch",
            f"column '{series.name}' holds numbers that do not read as month.year (MM.YYYY, such as 03.2024)",
        )
    return pd.Series(padded, index=series.index, dtype="str")


def _check_failed(column: str, failed: int, present: int, what: str) -> None:
    if present and failed / present > MAX_FAILED_SHARE:
        raise PrepareError("type_mismatch", f"column '{column}': {failed} of {present} cells cannot be read as {what}")


_PERIOD_WORDS = {"week": "ISO week, each as its Monday", "hour": "hour", "day": "day"}


def _period_starts(series: pd.Series, period: str) -> pd.Series:
    """Every moment as the first moment of its hour, day or ISO week (Monday 00:00), still a datetime.

    The bucket follows the wall clock of the column as stored: a column with one UTC offset
    (`+01:00`) is cut at its own midnight, a column the parser converted to UTC (mixed offsets)
    at UTC midnight, a naive column as written. The offset stays on the value, so an hour
    keeps it in `data.csv`; a day and a week are written as dates (`_cell_text`).
    """
    if period == "hour":
        return pd.Series(series.dt.floor("h"), index=series.index)
    days = pd.Series(series.dt.normalize(), index=series.index)
    if period == "day":
        return days
    return pd.Series(days - pd.to_timedelta(days.dt.weekday, unit="D"), index=series.index)


def _period_labels(series: pd.Series, period: str) -> pd.Series:
    labels: list[str | None] = []
    for value in series:
        if not isinstance(value, pd.Timestamp):
            labels.append(None)
        elif period == "month":
            labels.append(f"{value.year:04d}-{value.month:02d}")
        elif period == "quarter":
            labels.append(f"{value.year:04d}-Q{(value.month - 1) // 3 + 1}")
        else:
            labels.append(f"{value.year:04d}")
    return pd.Series(labels, index=series.index, dtype="str")


# --- Cells and helpers ------------------------------------------------------------------------


def _kind(series: pd.Series) -> Kind:
    if is_datetime64_any_dtype(series.dtype):
        return "datetime"
    if is_bool_dtype(series.dtype):
        return "boolean"
    if is_numeric_dtype(series.dtype):
        return "number"
    return "text"


def _texts(
    series: pd.Series, with_time: bool | None = None, form: tuple[bool, Mapping[float, bool]] = (False, {})
) -> pd.Series:
    """Every cell as its canonical text (`str` dtype, missing stays missing), as `data.csv` writes it.

    `with_time` is the datetime column's carried flag; None derives it from the values
    (a column an operation made, or a mixed object column after a melt). `form` is the
    column's form of whole floats (`_Carried.form`).
    """
    if with_time is None and _kind(series) == "datetime":
        with_time = _has_time(series)
    return pd.Series([_cell_text(value, bool(with_time), form) for value in series], index=series.index, dtype="str")


def _has_time(series: pd.Series) -> bool:
    return bool(((series.dt.normalize() != series) & series.notna()).any())


def _with_time(series: pd.Series, carried: _Carried) -> bool | None:
    """A datetime column's carried time flag, derived from its values when none is carried; None for other kinds."""
    if _kind(series) != "datetime":
        return None
    flag = carried.with_time.get(str(series.name))
    return _has_time(series) if flag is None else flag


def _cell_text(value: object, with_time: bool, form: tuple[bool, Mapping[float, bool]] = (False, {})) -> str | None:
    """One cell's canonical text; the missing scalars of every dtype (None, NA, NaT, NaN) are None.

    A whole float below 2**53 is written in the form the column held it in (`87000` or `2.0`, `_Carried.form`),
    else in the column's form, and without `.0` in a column that has none.
    """
    if isinstance(value, str):
        return value
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, bool | np.bool_):
        return "True" if value else "False"
    if isinstance(value, int | np.integer):
        return str(int(value))
    if isinstance(value, float | np.floating):
        number = float(value)
        if math.isnan(number):
            return None
        text = repr(number)
        dotted, held = form
        # Past 2**53 the `.0` stays: there a float may hold a whole number only rounded, which its form shows.
        if text.endswith(".0") and abs(number) < _FLOAT_EXACT and not held.get(number, dotted):
            return text[:-2]
        return text
    if isinstance(value, pd.Timestamp):
        # Every digit and the offset as the value holds them (owner rule of 2026-10-15): a fraction is written
        # only when there is one, an offset only for a zone-aware value.
        return value.isoformat() if with_time else value.date().isoformat()
    return str(value)


def _require(frame: pd.DataFrame, name: str) -> None:
    if name not in frame.columns:
        raise PrepareError("unknown_column", f"there is no column '{name}'")


def _distinct(names: list[str]) -> list[str]:
    return list(dict.fromkeys(names))


def _be(number: int) -> str:
    return "is" if number == 1 else "are"


def _listed(names: list[str]) -> str:
    """`a`, `a and b`, `a, b and c`."""
    return names[0] if len(names) == 1 else f"{', '.join(names[:-1])} and {names[-1]}"


def _count(number: int, noun: str) -> str:
    return f"{number} {noun}" if number == 1 else f"{number} {noun}s"


def _clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def validation_lines(exc: ValidationError, *, prefix: str = "") -> list[str]:
    """At most `MAX_VALIDATION_LINES` Pydantic errors as `operations[2].where[0].value: <message>` lines.

    `prefix` names the validated value when the error locations start below it (a
    `TypeAdapter` of the list starts at the index). The model's input is never echoed
    back, only the location and Pydantic's message; an error of the whole model (such
    as `generate.Generate`'s distinct names) has no location and is the message alone.
    """
    lines: list[str] = []
    for error in exc.errors()[:MAX_VALIDATION_LINES]:
        location = "".join(f"[{part}]" if isinstance(part, int) else f".{part}" for part in error.get("loc", ()))
        where = (prefix + location).lstrip(".")
        message = error.get("msg", "invalid")
        lines.append(f"{where}: {message}" if where else message)
    return lines
