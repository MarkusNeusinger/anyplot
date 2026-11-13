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
  a month name with a four-digit year (`Nov 2026`, `Okt. 2026`, `2026 Nov`, in the eleven
  languages of `months.py`) is its month's first day, as the parser reads it, and pandas
  infers the format of every other cell, day before month when ambiguous, as the parser
  reads a slash date, except for a cell that starts with a year (`2024-06-01T13:00:00Z`
  is 1 June; the order is chosen per cell); a cell pandas would only fill in (no digit, as
  `May` or `now`; a time alone, which it puts on today; no year, which it makes the year
  1) is a failure, never a made-up date (since 2026-11-01); a fraction of a second and a UTC offset are
  kept (`_cell_text`), different offsets in one column are read in UTC with the offsets
  named in the change line (owner decision of 2026-10-15, as the parser writes such a
  column), and times with and without an offset are a `type_mismatch`. Either way a cell that cannot be read becomes missing and the
  change line counts it; when more than 10 % of the non-missing cells fail, the
  operation is a `type_mismatch` instead. To number, a minus written as the minus sign
  `−` before the number is a sign, as the parser reads it, and the change line counts
  those cells; an en dash is none (`10–20`). With `name`, a conversion to number or datetime
  writes a new column of that name, appended last, and keeps the source column as it
  is: the conversion an open required role asks for (`conversions.py`), which the
  service then binds to that role (`Prepared.converted`). Without `name`, a column read
  from another type is recorded there too, as its own source, so the user's request to
  read it fills the open role the same way. To text: every cell becomes its canonical
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
* `aggregate`: group by one or two key columns and reduce one value column (`column`), or
  each of 2 to 10 (`columns`, one `how` for all, never `count`), with `sum`, `mean`,
  `count`, `min`, `max`, `first` or `last` (since 2026-11-07: the last meter reading of
  each month). `first` and `last` take a group's first and last value that is there, in
  the order of the rows, or, with a `period`, of the datetime keys' moments, so the
  last reading of a month is its latest one. A `period` turns every datetime key into `YYYY-MM`,
  `YYYY-Qn` or `YYYY` text before grouping, or, since live test round 5 of 2026-10-15
  ("Tagesmittel pro Sensor" on readings every 13 minutes), into the first moment of its
  `hour`, `day` or ISO `week` (its Monday), which stays a datetime, so the result keeps
  a time axis: a day and a week are written as dates, an hour with its time and offset.
  The buckets follow the column's clock as stored: a column with one UTC offset is cut
  at its own midnight, one the parser wrote in UTC (several offsets) at UTC midnight,
  and the change line names that offset. The result holds the key columns and the
  value columns named like their sources, or `count`; every other column is dropped, rows
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
  label at all is an `invalid_operation`. A rule takes several values into one label
  with an "any of" condition (`values`, see below: `Miete` or `Strom` is `Wohnen`). The
  change line counts the rows no rule named, under `otherwise` or without a label, and
  names their three largest groups by the text column the rules test most often, so a
  fallback that took a category of its own is seen (persona tests of 2026-11-06).
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
* `row_number`: a new whole-number column `name` (`index` when left out), inserted as the
  first column, that numbers the rows 1 to n in their current order. A column of that name
  that already numbers the rows (`1` to `n` or `0` to `n - 1`, each once) is reused, nothing
  added, and moved to the first column when it stands elsewhere, which the change line says
  (owner decision of 2026-11-02: the row numbers label the rows, as the data view shows them). The
  service binds it to the role it was made for (`Prepared.row_numbers`,
  `bindings.carry_bindings`). It came from the owner's live test of 2026-11-02: a pasted
  list `1,3,5,4,6,2` on a line plot had no x, and the root stopped to ask. It is an
  operation of its own so that the data panel's role dropdowns can offer it later.
* `date_number`: a new number column, appended last, computed from a datetime column, which
  stays as it is: its calendar `year`; its `decimal_year`, the year plus the part of it gone
  by at that moment (1 April 2021 is about 2021.25; a leap year has 366 days); its whole
  `days` since the column's earliest date, which is 0 (calendar dates count, never the time
  of day); or its Unix `timestamp`, the seconds since 1970-01-01 in UTC: a moment with a UTC
  offset is converted, a date without a time counts from its midnight UTC and a time without
  an offset is read as UTC, which the change line says, and a fraction of a second is kept
  as decimals (whole seconds stay whole numbers). The year, the decimal year and the days
  follow the column's clock as stored, as the `aggregate` buckets do. A missing date stays
  missing; the change line counts the dates converted and the cells left empty. Without
  `name` the column is named after its source and the unit in the session language
  (`DATE_UNIT_WORDS`: `Subscription Date (days)`, `Abodatum (Tage)`), as `conversions.py`
  names a converted column. Any other column is a `type_mismatch` with a hint to `set_type`
  it to datetime first. The new column fills an open required role that takes numbers
  (`Prepared.converted`), as a `set_type` with `name` does. Nothing converts by itself: the
  unit is the user's choice. It came from the owner's live test of 2026-11-04: a customers
  table on `scatter-basic` had no number for `y` but its subscription dates, and "convert
  subscription date to integer" had no operation (`set_type` to number reads text cells,
  `derive` takes number columns, `make_date` goes the other way).
* The text operations, a closed set with literal texts only (never a pattern), each reading
  the source column's canonical cell texts and writing new columns, appended last, while the
  source stays as it is: `split` cuts each cell at a literal `separator` into the 2 to 10
  columns `names` (a separator of spaces cuts at every run of whitespace; a `-` or `−` that
  starts a part right before a digit is that part's minus sign, never a cut, so `-5-10` is -5
  and 10; a cell without the separator stays whole in the first part, and the last part keeps
  the rest of a cell with more separators than parts, both counted in the change line);
  `extract` keeps only the number of each cell (`#12345` is 12345, `CHF 1'200` is 1200; a cell
  with no number or with two, such as `10–20`, has none, and more than 10 % of such cells are a
  `type_mismatch`, as for `set_type`), only its digits (`+41 79` is `4179`) or only its letters
  and the spaces between them (`12 kg` is `kg`); `strip` takes a literal `prefix` off the start
  of each cell and a `suffix` off its end where they stand; `replace` writes `new` (empty
  removes) in place of every `old`. Each part and each new column gets its type as `set_type`
  reads one (`_typed`): numbers with the dataset's decimal mark, its thousands rules, the unit
  token and the 10 % share of cells that may fail (they become missing and are counted), else
  dates, else text, which stays text through the re-parse. A number counts only in a cell the
  parser reads as one (`10 kg`, `CHF 1'200`; `Q1` stays a label), leading zeros keep a column
  text (`007`, as the parser keeps it), and a month name with a year (`Nov 2026`) is a date. The
  operations chain: `strip` a `#`, `split` the new column at `-`, `extract` the digits of a
  part, in one call. Without them a column of ranges such as `10–25` could only be fixed in a
  spreadsheet, and the root sent the user there. A text column whose every cell
  is two numbers around one dash, the first never above the second (`range_run`), is what a
  lower and upper bound pair left open asks for (`conversions.py`).
* The operations of 2026-11-07, from the persona tests of 2026-11-06, where five of ten
  personas got no plot because a column could not be derived and the root sent them to a
  spreadsheet:
  * `compute`: a new number column, appended last, from an `expression` over number
    columns, which `inputs` maps to short names (`{"l": "Länge l in m"}`). The expression
    language is `generate_data`'s, checked by its AST whitelist (`generate.parse_expression`)
    before a cell is read, so one language serves both tools: numbers, the inputs (an input
    named like a constant, such as `e` for an export column, stands for its column), `pi`,
    `e` and `tau`, `+ - * / ** % //` (`//` and `%` for whole-number buckets such as a
    decade), and the functions `log log10 log2 exp sqrt abs` (logs, growth, roots), `sin
    cos tan asin acos atan atan2` (angles and directions, such as wind components), `sinh
    cosh tanh`, `floor ceil round` (a whole part or a rounding the user asks for, written
    into the new column while the source stays), `sign` (the direction of a change) and
    `min max` (an elementwise cap). No comparison, condition or other call parses. Where
    every input is a whole-number column and every step keeps whole numbers whole, the
    rows are computed in Python integers, exactly; plain arithmetic (`+ - * /` over the
    inputs and number literals) in exact decimals with one rounding to a float at the end,
    as `diff` and `rolling` compute, so `19.99 * 3` is 59.97; anything else in float64, as
    `derive` computes, never rounded to fewer digits (`generate`'s `SIGNIFICANT_DIGITS` is a
    formula's, not the user's data). A cell is empty where an input is missing, a step
    divides by zero, or a step leaves a function's domain or the number range, and the
    change line quotes the checked expression and counts the empty cells by reason.
  * `diff`: each row's value minus the one `lag` rows before it (1 by default) within its
    group, in the order of `order`, as the ordered `derive` formulas walk (`_order_rows`);
    the first `lag` rows of each group are empty and counted. `rolling`: the `mean` or the
    `sum` over `window` rows, a row and the ones before it; the first `window - 1` rows of
    each group, and a row whose window holds a missing value, are empty and counted. Both
    work in exact decimals, so whole numbers stay whole and `12.3 - 10.1` is `2.2`. An
    order column may also hold the period labels an `aggregate` writes (`2024-03`), whose
    text sorts in time order, so the last reading per month and its change from the month
    before chain in one call. A window over a span of time (seven days of irregular
    readings) is no option: an `aggregate` by `day` first makes it one of rows.
  * `blank`: the cells of 1 to 10 columns emptied in place where 1 to 3 conditions hold,
    as in `drop_rows` (missing codes such as `-0.99`); the rows stay, each column counts
    its emptied cells, and a column that would lose every value is refused. It empties
    and never fills: `prepare_data` still never invents or fills in a value.
  * `keep_rows`: the first `n` rows in their current order, the rest dropped and counted
    ("kept the first 10 of 487 rows, 477 dropped"); after a `sort`, the top N (owner decision
    of 2026-11-07). A table of `n` rows or fewer keeps every row, and the line says so. The
    cut stays at `n`, and when it falls among rows of one value in the column the call's
    last `sort` ranked the rows by, the line counts and names the tied rows on each side
    (`_tie_note`). With `where` in place of `n` it keeps the rows for which 1 to 3 conditions
    all hold, a selection said positively ("only Miete and Strom", "only January"): its line
    counts both sides and the dropped rows that had no value to test (`_unvalued_note`).
  * `unsupported`: names a change no operation can make by a closed `family` (fill in
    values, edit single cells, add rows, combine tables, a text pattern, a window over
    time, other). It changes nothing: `apply_operations` refuses it as
    `unsupported_operation` before any operation runs, and `prepare_data` answers with a
    fixed sentence in the session language instead of the root telling the user to fix
    the file.

Values in conditions are never evaluated: a condition compares text with text for a
text column, numbers for a numeric column (the value is a dot-decimal number, which
the model may also pass as a JSON number), moments for a datetime column (the value is
an ISO date or date-time), `true`/`false` for a boolean column. The order tests are `gt`,
`lt`, `ge` (at least) and `le` (at most). A date without a time is the whole day for `le`
and `gt`: "until the 31st" takes in that day's rows whatever their time and "after the
31st" none of them, where midnight alone would cut the day's rows in two. A missing cell
matches only `is_missing`, and `not_missing` holds for every other cell, so "the rows
where X is missing" can be dropped or kept. `contains` searches the cell's canonical text,
case-sensitively.
`values` in place of `value` is an "any of" list (1 to 20) for `eq` and `contains`: the
condition holds when the cell equals one of them or contains one, and each value is read
as `value` is.

What the canonical CSV does not say about its columns travels with the frame as
`_Carried`: the columns the parser read by guess, the columns kept text, and whether a
datetime column is written with its time (the parser's choice, read from the profile),
so a column no operation touched is written back exactly as it was stored. A number is
written in its canonical form, as the parser writes it (`parse.number_text`): a whole
number below 2**53 without `.0` (`87000`, `2`; owner decision of 2026-10-15, live test
round 5: `30` and `30.0` are the same number), any other value in its shortest exact
form, and a whole number past 2**53 with the `.0` that shows a float holds it.

Errors raise `PrepareError(code, message)`: `unknown_column`, `type_mismatch`,
`empty_result` (no rows or no columns would remain), `too_wide`,
`invalid_operation` (an operation that is well-formed but cannot apply, such as a
condition without its value, a `period` without a datetime key, an expression outside
the whitelist, or a long format that would exceed the 2 MiB cap of computed data,
`parse.MAX_COMPUTED_BYTES`) and `unsupported_operation` (an `unsupported` operation).
Messages name columns, never cells.
Change lines name column names bare, condition values quoted and clipped to 40
characters (an "any of" list shows its first three and how many more), the cells of a
`classify` fallback's largest groups quoted and clipped to 24, and are at most
`MAX_NOTE_CHARS` long; the counts a line must never lose (empty cells, values stored
rounded, a fallback) are kept whole and the rest is shortened (`_with_notice`). `validation_lines` formats a
Pydantic error of the operation models for the model (`tools/session.py` and
`plugins/tool_safety.py` share it), one line per error with its location.
"""

import ast
import calendar
import io
import keyword
import math
import re
import sys
import unicodedata
import warnings
from collections import Counter
from collections.abc import Callable, Collection, Hashable, Iterable, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime, timedelta, tzinfo
from decimal import ROUND_FLOOR, InvalidOperation, localcontext
from decimal import Decimal as ExactDecimal
from typing import Annotated, Any, Literal, Self

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_datetime64_any_dtype, is_integer_dtype, is_numeric_dtype
from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    ValidationInfo,
    field_validator,
    model_validator,
)

from ..language import DEFAULT_LANGUAGE, canonical
from ..schemas import (
    MAX_CELL_CHARS,
    MAX_COLUMN_NAME_CHARS,
    MAX_COLUMNS,
    MAX_NOTE_CHARS,
    MAX_ROWS,
    MAX_WARNINGS,
    ColumnName,
    FromVersion,
    NewName,
)
from .generate import FUNCTIONS, IDENTIFIER, Expr, GenerateError, evaluate, parse_expression, source_text
from .months import month_number, month_year, named_months
from .parse import (
    AMBIGUOUS_DATE_ORDER,
    MAX_COMPUTED_BYTES,
    MAX_INPUT_CELL_CHARS,
    MISSING_VALUES,
    YEAR_MONTH,
    ParsedDataset,
    ascii_minus,
    canonical_names,
    keeps_value,
    minus_note,
    pandas_dtypes,
    parse_dataset,
    rounded_note,
    value_like,
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
MAX_SPLIT_PARTS = 10  # the new columns of one `split`
MAX_LITERAL_CHARS = (
    MAX_CELL_CHARS  # a separator, prefix, suffix or replaced text, at most what the profile shows of a cell
)
MAX_INPUTS = 10  # the input columns of one `compute`
MAX_AGGREGATE_COLUMNS = 10  # the value columns of one `aggregate`
MAX_ANY_VALUES = 20  # the values of one condition's "any of" list (`Condition.values`)
SHOWN_ANY_VALUES = 3  # of an "any of" list, the values a change line quotes before "and N more"
FALLBACK_GROUPS = 3  # the largest groups of a `classify` fallback that its change line names
_INT64_MIN, _INT64_MAX = -(2**63), 2**63 - 1

Test = Literal["eq", "ne", "contains", "is_missing", "not_missing", "gt", "lt", "ge", "le"]
ANY_OF_TESTS: frozenset[str] = frozenset(("eq", "contains"))
"""The tests an "any of" list (`Condition.values`) takes: a cell equal to one of the values, or one that contains one."""
ORDER_TESTS: frozenset[str] = frozenset(("gt", "lt", "ge", "le"))
"""The tests that compare by order, which a boolean column has none of."""
VALUE_FREE_TESTS: frozenset[str] = frozenset(("is_missing", "not_missing"))
"""The tests that ask whether a cell is there, and take no value."""
SHOWN_TIED_ROWS = 3  # of the rows of a tie on each side of a top N's cut, the ones its change line names
TIED_NAME_CHARS = 20  # of one such row's name in that line, which names up to twice `SHOWN_TIED_ROWS` of them
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
How = Literal["sum", "mean", "count", "min", "max", "first", "last"]
RollingHow = Literal["mean", "sum"]
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
PrepareErrorCode = Literal[
    "unknown_column", "type_mismatch", "empty_result", "too_wide", "invalid_operation", "unsupported_operation"
]
UnsupportedFamily = Literal[
    "fill_values", "edit_cells", "add_rows", "combine_tables", "text_pattern", "time_window", "other"
]
"""What kind of data change no operation can make (`Unsupported`): a closed set, so the reply is a fixed sentence and
the telemetry counts the gap by kind (`capability_gap`) without a word of the request."""
UNSUPPORTED_WORDS: dict[str, str] = {
    "fill_values": "fill in, interpolate or invent values",
    "edit_cells": "change single cells by hand",
    "add_rows": "add rows",
    "combine_tables": "combine the table with another one",
    "text_pattern": "match text by a pattern or a wildcard",
    "time_window": "compute over a span of time instead of a number of rows",
    "other": "make this change",
}
"""The English message of an `unsupported_operation` refusal, after "no operation can"."""

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
ROW_NUMBER_NAME = "index"
"""The name of the column a `row_number` makes, unless the operation names another."""
DateUnit = Literal["year", "decimal_year", "days", "timestamp"]
"""What a `date_number` makes of each date: its calendar year, its year with the part gone by as decimals, its whole
days since the column's earliest date (which is 0), or its Unix time in seconds (UTC)."""
DATE_UNIT_WORDS: dict[str, dict[str, str]] = {
    "en": {"year": "year", "decimal_year": "decimal year", "days": "days", "timestamp": "Unix time"},
    "de": {"year": "Jahr", "decimal_year": "Dezimaljahr", "days": "Tage", "timestamp": "Unix-Zeit"},
    "fr": {"year": "année", "decimal_year": "année décimale", "days": "jours", "timestamp": "temps Unix"},
    "es": {"year": "año", "decimal_year": "año decimal", "days": "días", "timestamp": "tiempo Unix"},
    "it": {"year": "anno", "decimal_year": "anno decimale", "days": "giorni", "timestamp": "tempo Unix"},
    "pt": {"year": "ano", "decimal_year": "ano decimal", "days": "dias", "timestamp": "tempo Unix"},
    "nl": {"year": "jaar", "decimal_year": "decimaal jaar", "days": "dagen", "timestamp": "Unix-tijd"},
    "pl": {"year": "rok", "decimal_year": "rok dziesiętny", "days": "dni", "timestamp": "czas uniksowy"},
}
"""The unit's word in the name a `date_number` gives its column when the operation names none (`<column> (<word>)`),
by session language, as `conversions.TYPE_WORDS` names a converted column; English for any other language."""
_EPOCH = datetime(1970, 1, 1)
_MICROSECONDS = 1_000_000
_DAY_MICROSECONDS = 86_400 * _MICROSECONDS
Keep = Literal["number", "digits", "letters"]
"""What an `extract` keeps of each cell."""
RANGE_SEPARATORS = ("–", "—", "-")
"""The dashes a range such as `10–25` stands around (`range_run`): en dash, em dash, hyphen."""
LEADING_ZEROS = "that leading zeros are no part of the value"
"""The guess of a number reading whose cells have leading zeros (`_number_guess`): such a part stays text."""
TEXT_READING = "kept as text"
"""The change-line words of a new column of a text operation that reads as neither numbers nor dates."""
DECIMAL_MARK = "the decimal mark"
"""The guess of a number reading whose cells read as numbers with either decimal mark, to other values
(`_number_guess`: `1.234` is 1.234 or 1234)."""
OPEN_MARK_READING = (
    'kept as text, since its cells read as numbers with either decimal mark: set_type to number with "decimal" '
    "reads them"
)
"""The change-line words of a text operation's new column whose number reading would be a guess of the decimal mark
(`_typed`). Typed by that guess, `38.790` would be stored as 38.79, and no later operation could read the thousands
back: the zero is gone from the canonical text."""
_SIGNS = ("-", "\N{MINUS SIGN}")
"""The separators that may also be a minus sign: one that starts a part right before a digit is its sign."""
_TIME_SUFFIXES = ("", " %H:%M", " %H:%M:%S", "T%H:%M", "T%H:%M:%S")
_VERBS: dict[str, str] = {
    "sum": "summed",
    "mean": "averaged",
    "count": "counted",
    "min": "took the minimum of",
    "max": "took the maximum of",
    "first": "took the first value of",
    "last": "took the last value of",
}
_PERIOD_LABEL_SHAPES = (YEAR_MONTH, re.compile(r"[0-9]{4}-Q[1-4]"), re.compile(r"[0-9]{4}"))
"""The labels an `aggregate` with a `period` writes (`2024-03`, `2024-Q1`, `2024`): text whose order is the time's."""
_DIVISIONS = (ast.Div, ast.FloorDiv, ast.Mod)
_WHOLE_OPERATORS = (ast.Add, ast.Sub, ast.Mult, ast.FloorDiv, ast.Mod)
_WHOLE_FUNCTIONS = frozenset(("abs", "sign", "min", "max"))
"""The steps of a `compute` that keep whole numbers whole, besides a power with a whole exponent of 0 or more."""
_WHOLE_BITS = 1023
"""A power whose result has more bits than this, by its base's bits times its exponent, is past the float64 range
before it is computed: refused at once, so a huge one never takes the time it would (`_whole_value`)."""
_FLOAT_MAX_WHOLE = int(sys.float_info.max)
"""The largest whole number a float64 holds (just under 2**1024): a whole result beyond it is empty and counted;
2**1023 and every other whole number up to it is kept, written as the float holds it (`_whole_value`)."""
_DECIMAL_DIGITS = 100
"""The digits a `rolling` window adds its decimal cells with: exact for cells within some 80 orders of magnitude."""
_TEST_SIGNS: dict[str, str] = {"eq": "=", "ne": "≠", "gt": ">", "lt": "<", "ge": "≥", "le": "≤"}

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
    converted: dict[str, str] = field(default_factory=dict)
    """The new columns a `set_type` with `name`, a text operation or a `date_number` made, each with its source column,
    and the columns a `set_type` without `name` read from another type, each as its own source: the caller binds each
    to the open required role that takes it (`bindings.carry_bindings`), as the conversion for that role was made."""
    row_numbers: list[str] = field(default_factory=list)
    """The columns a `row_number` made or reused: the caller binds one to the axis or label role that stayed open
    (`bindings.carry_bindings`), as the fallback for that role was made."""
    splits: list[list[str]] = field(default_factory=list)
    """The new columns of each `split`, in the order of its parts: two neighbouring parts may fill a lower and upper
    bound pair left open (`bindings.carry_bindings`), and no other two columns of one source may."""


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
    `T00:00:00` included). `language` is the session language, in which a `date_number`
    without `name` names its column (`DATE_UNIT_WORDS`).
    """

    decimal: str
    date_order: dict[str, str] = field(default_factory=dict)
    text_columns: set[str] = field(default_factory=set)
    with_time: dict[str, bool] = field(default_factory=dict)
    converted: dict[str, str] = field(default_factory=dict)  # columns a conversion made or re-typed, and their sources
    row_numbers: set[str] = field(default_factory=set)  # the columns of a `row_number`
    splits: list[list[str]] = field(default_factory=list)  # the new columns of each `split`, in the parts' order
    language: str = DEFAULT_LANGUAGE
    pasted_cells: dict[str, list[str]] = field(default_factory=dict)  # `ParsedDataset.pasted_cells`, renamed along
    rows_changed: bool = False  # an operation of this call dropped, grouped, sorted or reshaped the rows
    # The column this call's last `sort` ordered the rows by, while only row filters followed it: what a top N
    # ranks by, so its cut can be checked for a tie. None after any other operation.
    sorted_by: str | None = None

    @classmethod
    def of(cls, parsed: ParsedDataset, language: str = DEFAULT_LANGUAGE) -> "_Carried":
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
        carried = cls(parsed.profile.decimal, order, set(parsed.text_columns), with_time, language=language)
        carried.pasted_cells = {name: list(cells) for name, cells in parsed.pasted_cells.items()}
        return carried

    def rename(self, old: str, new: str) -> None:
        if old in self.pasted_cells:
            self.pasted_cells[new] = self.pasted_cells.pop(old)
        if old in self.text_columns:
            self.text_columns.remove(old)
            self.text_columns.add(new)
        if old in self.date_order:
            self.date_order[new] = self.date_order.pop(old)
        if old in self.with_time:
            self.with_time[new] = self.with_time.pop(old)
        self.converted = {
            (new if name == old else name): (new if source == old else source)
            for name, source in self.converted.items()
        }
        if old in self.row_numbers:
            self.row_numbers.remove(old)
            self.row_numbers.add(new)
        self.splits = [[new if name == old else name for name in parts] for parts in self.splits]

    def forget(self, names: Iterable[str]) -> None:
        gone = set(names)
        for name in gone:
            self.date_order.pop(name, None)
            self.text_columns.discard(name)
            self.with_time.pop(name, None)
            self.converted.pop(name, None)
            self.row_numbers.discard(name)
            # A later column of the same name (a rename, a derived one) is no column as pasted.
            self.pasted_cells.pop(name, None)
        # A dropped part leaves a gap: the parts on either side of it are no neighbours any more.
        self.splits = [[name if name not in gone else "" for name in parts] for parts in self.splits]

    def keep_only(self, names: Iterable[str]) -> None:
        kept = set(names)
        split = {name for parts in self.splits for name in parts if name}
        tracked = {
            *self.date_order,
            *self.text_columns,
            *self.with_time,
            *self.converted,
            *self.row_numbers,
            *split,
            *self.pasted_cells,
        }
        self.forget(tracked - kept)


# --- Operation models -----------------------------------------------------------------------


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


def _clean_text(text: str) -> str:
    """A literal a text operation compares with the cells or writes into them: nothing the parser drops or
    turns into a space (tabs, line breaks, control, invisible or separator characters)."""
    if _HEADER_BREAKS.search(text) or any(unicodedata.category(char) in ("Cc", "Cf", "Zl", "Zp") for char in text):
        raise ValueError("the text has no tabs, line breaks, control or invisible characters")
    return text


def _clean_affix(text: str) -> str:
    """A `strip` prefix or suffix, compared with the trimmed cell: its own surrounding spaces count for nothing."""
    if not text.strip():
        raise ValueError("a prefix or suffix holds more than spaces")
    return _clean_text(text).strip()


Value = Annotated[str, Field(max_length=MAX_VALUE_CHARS)]
Label = Annotated[str, Field(min_length=1, max_length=MAX_CELL_CHARS), AfterValidator(_clean_label)]
Literal_ = Annotated[str, Field(min_length=1, max_length=MAX_LITERAL_CHARS), AfterValidator(_clean_text)]
Affix = Annotated[str, Field(min_length=1, max_length=MAX_LITERAL_CHARS), AfterValidator(_clean_affix)]
NewText = Annotated[str, Field(max_length=MAX_LITERAL_CHARS), AfterValidator(_clean_text)]


def _input_name(name: str) -> str:
    """A `compute` input is named in its expression, so it is no function name or keyword. A constant's name may be
    one: `e` for an export column stands for that column, not for Euler's number, as the change line shows (the
    prep eval of 2026-11-07: the root named `Einspeisung` `e` despite the prompt, and its call was refused)."""
    if name in FUNCTIONS or keyword.iskeyword(name):
        raise ValueError("an input is named like a function or a keyword; choose another name")
    return name


InputName = Annotated[str, Field(min_length=1, max_length=64, pattern=IDENTIFIER), AfterValidator(_input_name)]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Condition(_Strict):
    """One test on one column; `value` is required for every test but `is_missing` and `not_missing`.

    A JSON number as the value (`{"test": "gt", "value": 100}`) is read as its text,
    so a numeric comparison needs no quoting. `values` in place of `value` is an "any
    of" list for `eq` and `contains`: the condition holds when the cell equals one of
    them, or contains one (`Miete` or `Strom` into one category, the missing codes
    `-0.99` and `-1` in one `blank`).
    """

    model_config = ConfigDict(extra="forbid", coerce_numbers_to_str=True)

    column: ColumnName
    test: Test
    value: Value | None = None
    values: list[Value] | None = Field(default=None, min_length=1, max_length=MAX_ANY_VALUES)


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
    """`decimal` defaults to the dataset's own; `date_format` left out lets pandas infer the format.

    `name` writes the converted cells into a new column of that name, appended last, and keeps
    `column` as it is (to number or datetime only): the conversion a role left open asks for
    (`conversions.py`), which `.undo()` takes back like any other.
    """

    op: Literal["set_type"]
    column: ColumnName
    type: TargetType
    date_format: DateFormat | None = None
    decimal: Decimal | None = None
    name: NewName | None = None


class Aggregate(_Strict):
    """Group by one or two key columns and reduce the value `column`, or each of 2 to 10 `columns`, with `how`.

    One `how` for every value column; `count` takes one. `first` and `last` take a group's first and last value
    that is there, in the order of the rows, or, with a `period`, of the moments of the datetime keys.
    """

    op: Literal["aggregate"]
    by: list[ColumnName] = Field(min_length=1, max_length=MAX_KEYS)
    column: ColumnName | None = None
    columns: list[ColumnName] | None = Field(default=None, min_length=1, max_length=MAX_AGGREGATE_COLUMNS)
    how: How
    period: Period | None = None

    @model_validator(mode="after")
    def _one_or_several(self) -> Self:
        if (self.column is None) == (self.columns is None):
            raise ValueError("aggregate takes column (one value column) or columns (several), not both and not neither")
        if self.columns is not None and len(set(self.columns)) != len(self.columns):
            raise ValueError("aggregate columns names each value column once")
        if self.columns is not None and len(self.columns) == 1:
            self.column, self.columns = self.columns[0], None  # one column in a list is the one value column
        return self

    @property
    def value_columns(self) -> list[str]:
        """The value columns, in the order given."""
        return [self.column] if self.column is not None else list(self.columns or [])


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


class RowNumber(_Strict):
    """A new whole-number column `name`, the rows numbered 1 to n in their current order.

    A column of that name that already numbers the rows (`1` to `n` or `0` to `n - 1`, each once) is reused.
    """

    op: Literal["row_number"]
    name: NewName = ROW_NUMBER_NAME


class DateNumber(_Strict):
    """A new number column `name`, appended last, from the datetime column `column`, which stays as it is.

    `unit`: the calendar `year`, the `decimal_year` (the year plus the part of it gone by), the whole `days` since the
    column's earliest date (0), or the Unix `timestamp` in seconds (UTC). `name` left out is the column's name with the
    unit in the session language (`DATE_UNIT_WORDS`). Nothing converts by itself: the unit is the user's choice.
    """

    op: Literal["date_number"]
    column: ColumnName
    unit: DateUnit
    name: NewName | None = None


class Split(_Strict):
    """Each cell of `column` cut at the literal `separator` into the new columns `names`, appended last, in order.

    A cell without the separator stays whole in the first new column; the last one keeps the rest of a cell
    with more separators than `names` has room for.
    """

    op: Literal["split"]
    column: ColumnName
    separator: Literal_
    names: list[NewName] = Field(min_length=2, max_length=MAX_SPLIT_PARTS)


class Extract(_Strict):
    """A new column `name` with only the number, the digits or the letters of each cell of `column`."""

    op: Literal["extract"]
    column: ColumnName
    keep: Keep
    name: NewName


class Strip(_Strict):
    """A new column `name` with the literal `prefix` taken off the start and `suffix` off the end of each cell."""

    op: Literal["strip"]
    column: ColumnName
    prefix: Affix | None = None
    suffix: Affix | None = None
    name: NewName


class Replace(_Strict):
    """A new column `name` with every literal `old` of each cell of `column` replaced by `new` (empty removes it)."""

    op: Literal["replace"]
    column: ColumnName
    old: Literal_
    new: NewText = ""
    name: NewName


class Compute(_Strict):
    """A new number column `name`, appended last, computed row by row from `expression` over number columns.

    `inputs` maps each short name the expression uses to its column, since a column name such as `Länge l in m`
    is no name an expression can hold (`{"l": "Länge l in m", "T": "Periode T in s"}`). The expression language
    is `generate_data`'s (`generate.parse_expression`): numbers, the inputs, the constants, `+ - * / ** % //`,
    parentheses and its functions; no comparison and no other call. An input named like a constant (`e`) stands for
    its column (`InputName`).
    """

    op: Literal["compute"]
    name: NewName
    expression: Expr
    inputs: dict[InputName, ColumnName] = Field(min_length=1, max_length=MAX_INPUTS)


class Diff(_Strict):
    """A new number column `name`: each row's `column` minus the one `lag` rows before it, within each group of
    `within`, in the order of `order`; the first `lag` rows of each group are empty."""

    op: Literal["diff"]
    name: NewName
    column: ColumnName
    order: ColumnName
    within: list[ColumnName] = Field(default_factory=list, max_length=MAX_KEYS)
    lag: int = Field(default=1, ge=1, le=MAX_ROWS)


class Rolling(_Strict):
    """A new number column `name`: the `mean` or the `sum` of `column` over `window` rows, each row and the
    `window - 1` before it, within each group of `within`, in the order of `order`; the first `window - 1` rows of
    each group are empty."""

    op: Literal["rolling"]
    name: NewName
    column: ColumnName
    how: RollingHow
    window: int = Field(ge=2, le=MAX_ROWS)
    order: ColumnName
    within: list[ColumnName] = Field(default_factory=list, max_length=MAX_KEYS)


class Blank(_Strict):
    """The cells of `columns` emptied in every row for which all conditions hold; the rows stay, nothing is filled."""

    op: Literal["blank"]
    columns: list[ColumnName] = Field(min_length=1, max_length=MAX_DROP_COLUMNS)
    where: list[Condition] = Field(min_length=1, max_length=MAX_CONDITIONS)


class KeepRows(_Strict):
    """The rows to keep, said positively; the rest are dropped. Either the first `n` rows in their current order
    (after a `sort`, the top N), or every row for which all conditions of `where` hold ("only Miete and Strom",
    "only this month"), which `drop_rows` could only say as the negation of each condition."""

    op: Literal["keep_rows"]
    n: int | None = Field(default=None, ge=1, le=MAX_ROWS)
    where: list[Condition] | None = Field(default=None, min_length=1, max_length=MAX_CONDITIONS)

    @model_validator(mode="after")
    def _one_way(self) -> Self:
        if (self.n is None) == (self.where is None):
            raise ValueError("keep_rows takes n (the first n rows) or where (the rows that match), one of the two")
        return self


class Unsupported(_Strict):
    """A data change no operation can make, named by its `family`: refused as `unsupported_operation`, nothing changes.

    The root reports it instead of telling the user to change the file: `prepare_data` answers with a fixed sentence in
    the session language (`refusals.yaml`, `unsupported_<family>`) and the telemetry counts the gap.
    """

    op: Literal["unsupported"]
    family: UnsupportedFamily


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
    | MakeDate
    | RowNumber
    | DateNumber
    | Split
    | Extract
    | Strip
    | Replace
    | Compute
    | Diff
    | Rolling
    | Blank
    | KeepRows
    | Unsupported,
    Field(discriminator="op"),
]


class PrepareArgs(BaseModel):
    """The arguments of `prepare_data`, validated by ToolSafety and the tool alike: up to `MAX_OPERATIONS` operations
    applied to the version `from_version` names (`dataset_versions.resolve_version`). None only for an earlier version
    taken as it was ("go back to the original"): from the current one they would change nothing."""

    model_config = ConfigDict(extra="forbid")
    # Declared before `operations`, whose check reads it, so an empty list is refused under its own field's name.
    from_version: FromVersion = "current"
    operations: list[Operation] = Field(max_length=MAX_OPERATIONS)

    @field_validator("operations")
    @classmethod
    def _changes_something(cls, operations: list[Operation], info: ValidationInfo) -> list[Operation]:
        if not operations and info.data.get("from_version", "current") == "current":
            raise ValueError(
                f"operations holds 1 to {MAX_OPERATIONS} operations; it is empty only with a from_version that names "
                "an earlier version"
            )
        return operations


_ROW_CHANGING = (DropRows, Aggregate, Sort, PivotLonger, PivotWider, KeepRows)
"""The operations after which a row of the frame is no longer the pasted row of the same place."""
_ROW_FILTERS = (DropRows, KeepRows)
"""The operations that only take rows out: the rows left keep their order and their cells, so a `sort` before them
still says what the rows are ranked by."""


# --- Applying ---------------------------------------------------------------------------------


def apply_operations(parsed: ParsedDataset, operations: list[Operation], language: str = DEFAULT_LANGUAGE) -> Prepared:
    """Apply `operations` in order to the canonical CSV of `parsed`; raises `PrepareError`.

    `language` is the session language, which names the column of a `date_number` that names none.
    """
    if not operations:
        raise PrepareError("invalid_operation", "there is no operation to apply")
    if len(operations) > MAX_OPERATIONS:
        raise PrepareError("invalid_operation", f"at most {MAX_OPERATIONS} operations can be applied at once")
    gap = next((operation for operation in operations if isinstance(operation, Unsupported)), None)
    if gap is not None:
        # Reported before anything is applied: a call that names a gap changes nothing.
        raise PrepareError("unsupported_operation", f"no operation can {UNSUPPORTED_WORDS[gap.family]}")
    carried = _Carried.of(parsed, language)
    frame = _read(parsed)
    changes: list[str] = []
    for operation in operations:
        try:
            frame, change = _apply(frame, operation, carried)
        except pd.errors.OutOfBoundsDatetime, OverflowError:
            # A date pandas cannot hold is a refusal, never a crash of the tool (review of 2026-10-15).
            raise PrepareError("invalid_operation", "a date would lie outside the years the data can hold") from None
        if not frame.shape[1]:
            raise PrepareError("empty_result", "no column would remain")
        if not len(frame):
            raise PrepareError("empty_result", "no row would remain")
        if isinstance(operation, _ROW_CHANGING):
            # The pasted cells sit one per pasted row: after this, a row of the frame is no longer theirs.
            carried.rows_changed = True
        if isinstance(operation, Sort):
            carried.sorted_by = operation.column
        elif not isinstance(operation, _ROW_FILTERS):
            carried.sorted_by = None
        changes.append(_clip(change, MAX_NOTE_CHARS))
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
    renamed = dict(zip(names, canonical, strict=True))
    converted = {renamed[name]: renamed.get(source, source) for name, source in carried.converted.items()}
    row_numbers = [canon for name, canon in zip(names, canonical, strict=True) if name in carried.row_numbers]
    # A part no longer in the data stays a gap (""), so the parts beside it are never taken for neighbours.
    splits = [[renamed.get(name, "") for name in parts] for parts in carried.splits]
    return Prepared(
        csv=csv_text,
        changes=changes,
        text_columns=text_columns,
        date_notes=date_notes,
        converted=converted,
        row_numbers=row_numbers,
        splits=[parts for parts in splits if any(parts)],
    )


def apply_and_parse(
    parsed: ParsedDataset, operations: list[Operation], language: str = DEFAULT_LANGUAGE
) -> tuple[Prepared, ParsedDataset]:
    """`apply_operations`, then its CSV parsed again as the next dataset version stores it; raises `PrepareError`,
    and `ParseError` only for a bug, since the operations keep every parser cap.

    The one path from operations to a version, shared by the root's `prepare_data` and the conversions the server
    makes on a paste (`paste_conversions.py`), so both store the same data for the same operations.
    """
    prepared = apply_operations(parsed, operations, language=language)
    # The columns `set_type text` made text stay text: the re-parse would type them by content again.
    # The CSV is the service's own: every row stays, also a `Total` category a sort moved to the end.
    again = parse_dataset(
        prepared.csv, text_columns=prepared.text_columns, find_table=False, max_bytes=MAX_COMPUTED_BYTES, canonical=True
    )
    # A date column whose day and month order is still a guess keeps its note, so a later call can switch it.
    return prepared, with_date_notes(again, prepared)


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
        case RowNumber():
            return _row_number(frame, operation, carried)
        case DateNumber():
            return _date_number(frame, operation, carried)
        case Split():
            return _split(frame, operation, carried)
        case Extract():
            return _extract(frame, operation, carried)
        case Strip():
            return _strip(frame, operation, carried)
        case Replace():
            return _replace(frame, operation, carried)
        case Compute():
            return _compute(frame, operation, carried)
        case Diff():
            return _diff(frame, operation, carried)
        case Rolling():
            return _rolling(frame, operation, carried)
        case Blank():
            return _blank(frame, operation, carried)
        case KeepRows():
            return _keep_rows(frame, operation, carried)
        case Unsupported():  # `apply_operations` refuses it before any operation runs
            raise PrepareError("unsupported_operation", f"no operation can {UNSUPPORTED_WORDS[operation.family]}")


def _read(parsed: ParsedDataset) -> pd.DataFrame:
    """The canonical CSV as the loader reads it; pandas' reader keeps every number's shortest form stable.

    Only an empty cell is missing (`keep_default_na=False`, as the run form's loader reads
    it): a text category `NA` (Namibia, North America) that the parse kept is a category here too.
    """
    return pd.read_csv(
        io.StringIO(parsed.csv),
        dtype=pandas_dtypes(parsed.column_dtypes),
        parse_dates=list(parsed.parse_dates),
        date_format="ISO8601",  # `data.csv` writes ISO dates only: no per-column guess, no "Could not infer" warning
        keep_default_na=False,
        na_values=[""],
    )


def _write(frame: pd.DataFrame, carried: _Carried) -> str:
    """Canonical CSV text: every column written through its canonical cell texts."""
    out = pd.DataFrame({str(name): _texts(frame[name], _with_time(frame[name], carried)) for name in frame.columns})
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


def _rows_where(frame: pd.DataFrame, conditions: Sequence[Condition], carried: _Carried) -> tuple[pd.Series, list[str]]:
    """The rows for which every condition holds, and each condition in the change line's words."""
    mask = pd.Series(True, index=frame.index)
    clauses: list[str] = []
    for condition in conditions:
        _require(frame, condition.column)
        series = frame[condition.column]
        mask &= _matches(series, condition, _with_time(series, carried))
        clauses.append(_describe(condition, _kind(series)))
    return mask, clauses


def _drop_rows(frame: pd.DataFrame, op: DropRows, carried: _Carried) -> tuple[pd.DataFrame, str]:
    mask, clauses = _rows_where(frame, op.where, carried)
    dropped = int(mask.sum())
    if dropped == len(frame):
        raise PrepareError("empty_result", "every row matches the conditions; no row would remain")
    kept = frame[~mask].reset_index(drop=True)
    line = f"dropped {_count(dropped, 'row')} where {' and '.join(clauses)}"
    return kept, line + _offsets_note(frame[mask], kept)


MAX_OFFSET_COLUMNS = 2
"""How many columns the note of `_offsets_note` names."""


def _adds_up_below_zero(cells: pd.Series) -> bool:
    """Whether a number column's cells add up to less than 0. Whole numbers are summed as Python integers: pandas'
    Int64 sum wraps around silently past 2**63, which would turn a large negative total into a positive one."""
    if is_integer_dtype(cells.dtype):
        return sum(int(value) for value in cells.dropna()) < 0
    return float(cells.sum()) < 0


def _offsets_note(dropped: pd.DataFrame, kept: pd.DataFrame) -> str:
    """What a `drop_rows` line adds when a number column is below 0 only in the rows it dropped, while rows that stay
    are above 0, and the dropped rows together are below 0 there: those rows took amounts off (returns,
    cancellations, credits), so the column's total over the rows kept went up, which a count of dropped rows does
    not say. Dropped rows that add up to 0 or more took nothing off on balance, and get no note.

    In the persona round of 2026-11-11 the user had the cancelled invoices taken off. Their quantities were negative,
    so the total rose from the net to the gross figure, and the root called the higher one right when the user
    doubted it. The note states the sign, which holds for every such table, where a sum of each column would be a
    figure for every drop.
    """
    names = [
        str(column)
        for column in kept.columns
        if _kind(kept[column]) == "number"
        and bool(dropped[column].lt(0).fillna(False).any())
        and _adds_up_below_zero(dropped[column])
        and not bool(kept[column].lt(0).fillna(False).any())
        and bool(kept[column].gt(0).fillna(False).any())
    ][:MAX_OFFSET_COLUMNS]
    if not names:
        return ""
    one = len(names) == 1
    return (
        f"; {' and '.join(names)} {'is' if one else 'are'} below 0 only in rows that were dropped, so "
        f"{'its total' if one else 'their totals'} over the rows kept {'is' if one else 'are'} higher than before"
    )


def _set_type(frame: pd.DataFrame, op: SetType, carried: _Carried) -> tuple[pd.DataFrame, str]:
    _require(frame, op.column)
    series = frame[op.column]
    present = int(series.notna().sum())
    kind = _kind(series)
    if op.name is not None:
        _check_new_column(frame, op, kind)
    result = frame.copy()
    if op.type == "text":
        # Kept text through the re-parse either way: a text column stays one when a later change makes its cells typeable.
        carried.text_columns.add(op.column)
        if kind == "text":
            return frame, f"{op.column}: already text, nothing changed"
        # A pasted number column whose dots are open becomes its cells as pasted (`7.000`, not the stored `7`), so
        # a `set_type` back to numbers with a decimal comma later in the call still reads the thousands.
        result[op.column] = _source_texts(frame, op.column, carried)
        carried.with_time.pop(op.column, None)
        carried.date_order.pop(op.column, None)
        return result, f"{op.column}: {_count(present, 'cell')} now text"
    if op.type == "number":
        if kind == "number":
            pasted = carried.pasted_cells.get(op.column)
            if op.decimal != "," or pasted is None:
                # The canonical text of a number is a dot decimal (`7.000` is stored as `7`); re-reading it under a
                # decimal comma would be wrong. Only the cells as pasted can be read again.
                if op.decimal == "," and carried.decimal != ",":
                    # Refused, never a line of a call that goes on: the operations after it would compute with the
                    # decimal reading, and the call would store that as the next version.
                    raise PrepareError(
                        "type_mismatch",
                        f"column '{op.column}' already holds numbers read with a decimal point, stored without the "
                        "trailing zeros they were written with (`7.000` is `7`); a decimal comma can read them again "
                        "only from the pasted data, before any other operation changes the column: undo to the "
                        "pasted data first, or read the text column these numbers came from",
                    )
                return frame, f"{op.column}: already numbers, nothing changed"
            if carried.rows_changed or len(pasted) != len(frame):
                raise PrepareError(
                    "type_mismatch",
                    f"column '{op.column}' can be read with a decimal comma only from the rows as pasted: "
                    "change the reading first, in its own call, or undo to the pasted data first",
                )
            # The pasted cells, read again: `1.234` is 1234 and `7.000` is 7000 now. An empty one (a missing cell, or
            # a declared mark the parse blanked) stays missing, as it is in the column.
            series = pd.Series([cell or None for cell in pasted], index=frame.index, name=op.column, dtype="object")
            present = int(series.notna().sum())
        # A text column read here holds the cells it holds. A pasted number column that a `set_type` to text in the
        # same call turned into text holds its cells as pasted (`7.000`), so a decimal comma reads 7000 here too; one
        # whose rows changed first holds its canonical dot decimals, and `7` (pasted `7.000`) stays 7.
        conversion = _number_conversion(series, op.decimal or carried.decimal)
    else:
        if kind == "datetime":
            return _reread_dates(frame, op, present, carried)
        conversion = _date_conversion(series, op.date_format)
    _check_failed(op.column, conversion.failed, present, "numbers" if op.type == "number" else "dates")
    # A conversion into a new column keeps the source as it is: what the cells said stays beside what was read.
    target = op.name or op.column
    result[target] = conversion.values
    carried.with_time.pop(target, None)
    carried.date_order.pop(target, None)
    if op.type == "datetime":
        carried.with_time[target] = conversion.with_time
        if conversion.order is not None:
            # Every day is at most 12: the cells read the other way too, so a later request may still swap them.
            carried.date_order[target] = conversion.order
    carried.text_columns.discard(target)
    if op.name is not None:
        carried.converted[op.name] = op.column
    elif kind != op.type:
        # Read in place from another type, the column fills an open required role that takes it, as a named
        # conversion's new column does (`carry_bindings`): a user who asks for it means the role that waits for it.
        carried.converted[op.column] = op.column
    read = present - conversion.failed
    if op.name is None:
        change = f"{op.column}: {_count(read, 'cell')} {conversion.reading}"
    else:
        change = f"new column {op.name}: {_count(read, 'cell')} of {op.column} {conversion.reading}"
    if conversion.failed:
        change += f", {_count(conversion.failed, 'cell')} could not be read and {_be(conversion.failed)} now missing"
    if op.name is not None:
        change += f"; {op.column} stays as it is"
    notice = conversion.notice
    if op.type == "number" and op.decimal is None and _mark_open(_texts(series), conversion):
        # The reading took the dataset's mark for cells the other mark reads too: said here, where the root can
        # still act on it, as the parser says it of a pasted column (`parse.AMBIGUOUS_DOTS`).
        notice = "; ".join(part for part in (notice, _open_mark_note(conversion.used)) if part)
    return result, _with_notice(change, notice)


def _check_new_column(frame: pd.DataFrame, op: SetType, kind: Kind) -> None:
    """A `set_type` with `name` makes a new column of numbers or dates, from a column not of that type yet."""
    if op.type == "text":
        raise PrepareError("invalid_operation", "set_type to text changes the column itself: leave name out")
    if op.name in frame.columns:
        raise PrepareError("invalid_operation", f"a column named '{op.name}' already exists")
    if frame.shape[1] >= MAX_COLUMNS:
        raise PrepareError("too_wide", f"the data already has {frame.shape[1]} columns; at most {MAX_COLUMNS} fit")
    if kind == "number" and op.type == "number":
        raise PrepareError("invalid_operation", f"column '{op.column}' already holds numbers: bind it as it is")
    if kind == "datetime" and op.type == "datetime":
        raise PrepareError("invalid_operation", f"column '{op.column}' already holds dates: bind it as it is")


@dataclass(frozen=True)
class Conversion:
    """A `set_type` of one column to numbers or dates before it is stored: the cells, the failures and the words.

    `reading` is the change line after the count (`read as dates (format inferred, year
    first)`); `notice` follows the failures and is never cut (a rounding count, the UTC
    offsets, the typographic minus). `order` is the day and month order a date reading
    chose by guess (`day` or `month`, every day at most 12, `_order_open`). `guess` names
    what the reading guessed, for the dry run of an open role (`dry_run`): the day and
    month order, a two-digit year, the decimal mark, spaces or apostrophes as thousands
    separators; None when the cells say how they read.
    """

    values: pd.Series
    failed: int
    reading: str
    notice: str = ""
    with_time: bool = False
    order: str | None = None
    guess: str | None = None
    unit: str | None = None
    used: str | None = None
    """The decimal mark a number reading used: the requested one, or the other when the cells read better with it."""


def _number_conversion(series: pd.Series, requested: str) -> Conversion:
    """The cells of a column that is no number column yet as numbers, read with `requested` first (`_to_numbers`)."""
    converted, unit, failed, used, rounded, minus = _to_numbers(series, requested)
    reading = "read as numbers"
    if used != requested:
        reading += " (decimal comma)" if used == "," else " (decimal point)"
    if unit:
        reading += f", unit '{_clip(unit, MAX_CELL_CHARS)}' removed"
    notices = [note for note in (minus_note(minus) if minus else "", rounded_note(rounded) if rounded else "") if note]
    guess = _number_guess(series, used)
    if rounded and guess is None:
        # Digits past what a number holds (an account number of 20 digits) would be lost: the parser kept it text.
        guess = "that values with more digits than a number holds may be rounded"
    return Conversion(converted, failed, reading, "; ".join(notices), guess=guess, unit=unit, used=used)


def _mark_open(texts: Iterable[Any], conversion: Conversion) -> bool:
    """Whether a number reading took for its decimal mark a mark that could as well separate thousands in every cell:
    `38.790` read with a decimal point is 38.79, and with a decimal comma 38790.

    The other way round is no such guess: a mark the reading took for a thousands separator between three-digit
    groups (`1.200` in a file of decimal commas, `1,234` in one of decimal points) is how that file writes numbers.
    """
    used = conversion.used
    return (
        conversion.guess == DECIMAL_MARK
        and used is not None
        and any(isinstance(text, str) and used in text for text in texts)
    )


def _open_mark_note(used: str | None) -> str:
    """What a `set_type` to numbers without `decimal` says of cells whose decimal mark could separate thousands
    (`_mark_open`): the reading it took and how to get the other, since the text is gone once the column holds
    numbers."""
    marks, other = ("dots", ",") if used == "." else ("commas", ".")
    return f'{marks} read as the decimal mark; if they separate thousands, undo this and set "decimal": "{other}"'


def _number_guess(series: pd.Series, used: str) -> str | None:
    """What a read as numbers guessed: that leading zeros are no part of the value (`007`, a code the parser kept
    text), thousands separators of spaces or apostrophes (`123 456` may be an id), or the decimal mark, when the
    other mark reads the same cells too, to other values (`1,234` is 1.234 or 1234). Flash pre-check of 2026-11-01:
    without the first, a postal code column read as certain numbers for an open role."""
    texts = [ascii_minus([text])[0][0] for text in _texts(series) if isinstance(text, str)]
    if any(_LEADING_ZERO.search(text.strip()) for text in texts):
        return LEADING_ZEROS
    if any(_GROUP_INSIDE.search(text.strip()) for text in texts):
        return "that spaces or apostrophes separate thousands"
    other = "," if used == "." else "."
    first, _, _ = _read_numbers(list(texts), used)
    second, _, _ = _read_numbers(list(texts), other)
    # A cell neither mark reads says nothing about the mark; one that only a single mark reads settles it (`1.5`
    # is no thousands group), so the guess needs both readings to fail on the same cells.
    if [number is None for number in first] == [number is None for number in second] and first != second:
        return DECIMAL_MARK
    return None


_GROUP_INSIDE = re.compile(r"[0-9][\s'’]+[0-9]")
"""A space or an apostrophe between digits: `set_type` reads it as a thousands separator, the parser only by rule."""
_LEADING_ZERO = re.compile(r"(?<![0-9.,'’\s])0[0-9]")
"""A zero that leads a run of digits (`007`, `$012`), never one after a decimal mark or a group (`1.05`, `1 005`)."""


def _date_conversion(series: pd.Series, date_format: str | None) -> Conversion:
    """The cells of a column that is no date column yet as dates (`_to_dates`), with the words of the change line."""
    converted, failed, with_time, notice = _to_dates(series, date_format)
    originals = _texts(series)
    read = converted.notna()
    texts = [text for text, ok in zip(originals, read, strict=True) if ok and isinstance(text, str)]
    named = {text for text in texts if _month_iso(text) is not None} if date_format is None else set()
    named_cells = sum(text in named for text in texts)  # `named` holds distinct cells, a month may repeat
    # A month name says which part is the month (`1 Nov 2026`): only the other cells leave the order open.
    unnamed = pd.Series(
        [isinstance(text, str) and text not in named and not _names_month(text) for text in originals],
        index=series.index,
    )
    order: str | None = None
    year_first = date_format is None and any(_YEAR_FIRST.match(text) for text in texts if text not in named)
    if (
        date_format in (None, "MM/DD/YYYY", *_DAY_FIRST_FORMATS)
        and not year_first
        and _order_open(converted[read & unnamed])
    ):
        order = "month" if date_format == "MM/DD/YYYY" else "day"
    guess = "the day and month order" if order else None
    if date_format is None and any(not _FOUR_DIGITS.search(text) for text in texts):
        guess = "the century of two-digit years"
    if date_format == "YYYY":
        # A number column of 1450, 1890 and 2100 reads as years too: the change line says so, the user checks it.
        return Conversion(converted, failed, "read as years (YYYY, each as 1 January)", notice, with_time, order, guess)
    if date_format:
        how = date_format
    elif texts and named_cells == len(texts):
        return Conversion(converted, failed, MONTH_NAMES_READING, notice, with_time, order, guess)
    else:
        # The cells that were read decide the wording; an unreadable one is counted by the caller.
        others = [text for text in texts if text not in named]
        year_cells = sum(1 for text in others if _YEAR_FIRST.match(text))
        if year_cells == len(others):
            how = "format inferred, year first"  # `2024-06-01` is 1 June, no day-before-month guess
        elif year_cells:
            how = "format inferred, year first where a cell starts with one, else day before month"
        else:
            how = "format inferred, day before month"
        if named:
            how += f"; {_count(named_cells, 'cell')} with a month name and a year as the first day of the month"
    return Conversion(converted, failed, f"read as dates ({how})", notice, with_time, order, guess)


DRY_RUN_SAMPLE = 20
"""The distinct cells a dry run reads first: a column that fails more than `MAX_FAILED_SHARE` of them is no candidate."""


@dataclass(frozen=True)
class DryRun:
    """What a `set_type` of one text column to numbers or dates would do, nothing stored (`dry_run`).

    `read` of `present` cells would convert; `reading` is the change line's words after the
    count; `guess` what the reading would guess (`Conversion.guess`); `order` the direction
    the read dates would run down the rows (`ColumnProfile.order`), for a sort the plot needs;
    `date_format` the format the `set_type` names (`year_run`), None when it infers one.
    """

    column: str
    type: Literal["number", "datetime"]
    present: int
    read: int
    reading: str
    guess: str | None = None
    order: Literal["ascending", "descending"] | None = None
    date_format: DateFormat | None = None

    @property
    def certain(self) -> bool:
        """Every cell converts and the reading guesses nothing: the conversion can be made without a question."""
        return self.read == self.present and self.guess is None


def dry_run(
    frame: pd.DataFrame, column: str, target: Literal["number", "datetime"], decimal: str = "."
) -> DryRun | None:
    """`set_type` of the text column `column` of `frame` (`read_frame`) to `target`, counted, not applied.

    `decimal` is the dataset's own, as `set_type` reads numbers with it first. None when the
    conversion would be refused (`type_mismatch`: more than `MAX_FAILED_SHARE` of the cells
    fail, two units, times with and without an offset): such a column is no candidate. Neither
    is a column of `YYYY-NN` cells for dates: the parser reads months of that shape itself, so
    one it kept text is a span of years (`2009-10`) or holds ids, as its name says (`parse._as_periods`;
    review of #12512). The first `DRY_RUN_SAMPLE` distinct cells are tried first, so a column
    of names or notes costs no full read.
    """
    series = frame[column]
    present = int(series.notna().sum())
    if not present or _kind(series) != "text":
        return None
    cells = series.dropna().unique()
    if target == "datetime" and all(YEAR_MONTH.fullmatch(cell) for cell in cells):
        return None
    distinct = pd.Series(cells[:DRY_RUN_SAMPLE], dtype="str", name=column)
    try:
        sample = _convert(distinct, target, decimal)
        if sample.failed > MAX_FAILED_SHARE * len(distinct):
            return None
        conversion = _convert(series, target, decimal)
    except PrepareError:
        return None
    if conversion.failed > MAX_FAILED_SHARE * present:
        return None
    if conversion.unit is not None and _names_month(conversion.unit):
        return None  # `Nov 26, 2026` is a date, never the number 26.2026 behind a unit `Nov`
    order = _run_order(conversion.values) if target == "datetime" else None
    return DryRun(column, target, present, present - conversion.failed, conversion.reading, conversion.guess, order)


def year_run(frame: pd.DataFrame, column: str) -> DryRun:
    """`set_type` of the whole-number column `column` of `frame` to dates with `YYYY`, counted, not applied.

    The caller names the column: only one of years by its header (`temporal.year_score` 2, `conversions.py`), since
    prices of 1149 to 3000 read as years too (owner's second opinion of 2026-11-02).
    """
    series = frame[column]
    present = int(series.notna().sum())
    conversion = _date_conversion(series, "YYYY")
    read = present - conversion.failed
    return DryRun(
        column, "datetime", present, read, conversion.reading, conversion.guess, _run_order(conversion.values), "YYYY"
    )


@dataclass(frozen=True)
class RangeRun:
    """A text column whose every cell is two numbers around one dash, the first never above the second (`range_run`).

    `reading` is the change line's words for both parts (`read as numbers`, `read as numbers (decimal comma)`).
    """

    column: str
    separator: str
    present: int
    reading: str


def range_run(frame: pd.DataFrame, column: str, decimal: str = ".") -> RangeRun | None:
    """A `split` of the text column `column` of `frame` into a lower and an upper bound, checked, not applied.

    Only a column of one shape throughout qualifies: every cell holds exactly one dash of
    `RANGE_SEPARATORS` (a minus sign that starts a part is no dash, `_cuts`), both parts read as
    plain numbers with the dataset's decimal mark or the other one alike, without a unit and
    without a guess (`Conversion.guess`: leading zeros, spaces as thousands, a decimal mark that
    reads both ways), and the first part is never above the second in any row. An ISO date
    (`2024-11-03`, two dashes), an id (`A-12`), a span of years such as a season (`2019-20`,
    whose second part is the smaller) and a column with one odd cell are none: the user can
    still ask for the `split`. None also for a column that is no text column.
    """
    series = frame[column]
    if _kind(series) != "text":
        return None
    cells = [cell.strip() for cell in series if isinstance(cell, str)]
    if not cells:
        return None
    for separator in RANGE_SEPARATORS:
        if any(len(_cuts(cell, separator)) != 1 for cell in cells):
            continue
        pairs = [_pieces(cell, separator, 2) for cell in cells]
        if any(not low or not high for low, high in pairs):
            continue
        low = _numbers_of([low for low, _ in pairs], decimal)
        high = _numbers_of([high for _, high in pairs], decimal)
        if low is None or high is None or low.reading != high.reading:
            continue
        if any(item.failed or item.unit is not None or item.guess is not None for item in (low, high)):
            continue
        if any(bottom > top for bottom, top in zip(low.values, high.values, strict=True)):
            continue
        return RangeRun(column, separator, len(cells), low.reading)
    return None


def _numbers_of(cells: list[str], decimal: str) -> Conversion | None:
    """The cells read as `set_type` reads numbers, or None when it would refuse them (two units)."""
    try:
        return _number_conversion(pd.Series(cells, dtype="str"), decimal)
    except PrepareError:
        return None


def _run_order(dates: pd.Series) -> Literal["ascending", "descending"] | None:
    values = dates.dropna()
    if values.nunique() < 2:
        return None
    if values.is_monotonic_increasing:
        return "ascending"
    return "descending" if values.is_monotonic_decreasing else None


def _convert(series: pd.Series, target: Literal["number", "datetime"], decimal: str) -> Conversion:
    return _number_conversion(series, decimal) if target == "number" else _date_conversion(series, None)


def read_frame(parsed: ParsedDataset) -> pd.DataFrame:
    """The dataset's frame as the operations read it, for `dry_run`."""
    return _read(parsed)


MONTH_NAMES_READING = "read as months (a month name and a year, each as the first day of the month)"
"""The change line of a `set_type` to dates whose every read cell names a month and a year, as the parser's note says."""
_FOUR_DIGITS = re.compile(r"[0-9]{4}")
_LETTERS = re.compile(r"[^\W\d_]+")


def _names_month(text: str) -> bool:
    """Whether a cell holds a month name or abbreviation as one of its words (`1 Nov 2026`, `März`)."""
    return any(month_number(word) is not None for word in _LETTERS.findall(text))


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


def _decimal_total(values: pd.Series) -> ExactDecimal:
    """The total of a float column's cells as `data.csv` writes them, added in decimals.

    A float's `repr` is its shortest form, the text the user reads, so this is the sum they
    would get by hand. Adding the floats themselves leaves the noise of their binary form in
    a total of decimal numbers, and how much depends on the method: pandas 3.1 dropped its
    compensated group sum for sorted keys (`4024.2` came back as `4024.2000000000003`), and
    even an exactly rounded `math.fsum` gives `377.78000000000003` for cells that add up to
    `377.78`. Such a total would reach `data.csv` and the plot as a value no one wrote.
    `decimal` keeps 28 significant digits, more than a float holds. Infinities of both signs
    have no total: the result is then not a number.
    """
    try:
        return sum((ExactDecimal(repr(value)) for value in values.dropna().tolist()), ExactDecimal(0))
    except InvalidOperation:
        return ExactDecimal("NaN")


def _group_sum(values: pd.Series) -> float:
    """A float group's total (`_decimal_total`); a group with no value totals 0, as in pandas."""
    return float(_decimal_total(values))


def _group_mean(values: pd.Series) -> float:
    """A float group's mean from its decimal total; a group with no value has none."""
    count = values.count()
    return float(_decimal_total(values) / count) if count else math.nan


def _aggregate(frame: pd.DataFrame, op: Aggregate, carried: _Carried) -> tuple[pd.DataFrame, str]:
    keys = _distinct(op.by)
    values = _distinct(op.value_columns)
    for name in [*keys, *values]:
        _require(frame, name)
    for name in values:
        if name in keys:
            raise PrepareError("invalid_operation", f"column '{name}' cannot be both a key and the value")
    if op.how == "count" and len(values) > 1:
        raise PrepareError("invalid_operation", "count counts the rows of each group: give it one column")
    date_keys = [name for name in keys if _kind(frame[name]) == "datetime"]
    if op.period and not date_keys:
        raise PrepareError("invalid_operation", "a period needs a datetime column among the keys")
    kinds = {name: _kind(frame[name]) for name in values}
    for name, kind in kinds.items():
        if op.how in ("sum", "mean") and kind not in ("number", "boolean"):
            raise PrepareError("type_mismatch", f"column '{name}' is {kind}; {op.how} needs a number column")
    value_names = ["count"] if op.how == "count" else values
    if value_names[0] in keys:
        raise PrepareError("invalid_operation", f"a key column is already named '{value_names[0]}'")

    work = frame[[*keys, *values]].copy()
    if op.how in ("first", "last") and date_keys and op.period:
        # A bucket's first and last value are its earliest and latest moment's; rows of one moment keep their order.
        # Without a period every row of a group has the same moment, so the rows' own order decides.
        # One stable sort per key, the last key first: pandas documents `kind` only for a single column, so two date
        # keys sort as two guaranteed-stable passes, the first key deciding and the second breaking its ties.
        for name in reversed(date_keys):
            work = work.sort_values(name, kind="stable", na_position="last")
    if op.period in DATE_PERIODS:
        for name in date_keys:
            work[name] = _period_starts(work[name], op.period)
    elif op.period:
        for name in date_keys:
            work[name] = _period_labels(work[name], op.period)
    for name, kind in kinds.items():
        if kind == "boolean" and op.how in ("sum", "mean"):
            work[name] = work[name].astype("Int64")
    grouped = work.groupby(keys, dropna=False, sort=True)
    reduced: list[pd.Series] = []
    rounded = cast = 0
    for name in values:
        series, whole_rounded_count, cast_count = _reduce(grouped[name], work[name], op.how)
        reduced.append(series.rename(value_names[0] if op.how == "count" else name))
        rounded += whole_rounded_count
        cast += cast_count
    result = pd.concat(reduced, axis=1).reset_index()
    result.columns = pd.Index([*keys, *value_names])
    carried.keep_only([*keys, *value_names])
    if op.period in DATE_PERIODS:
        # Each key is the bucket's first moment: a date for a day or an ISO week (its Monday), a time for an hour.
        carried.forget(date_keys)
        carried.with_time.update(dict.fromkeys(date_keys, op.period == "hour"))
    elif op.period:
        carried.forget(date_keys)  # period labels are text now
        # ... and stay text through the re-parse, which reads `2024-03` and `2024-Q1` as dates since live round 7.
        carried.text_columns.update(date_keys)

    period = _PERIOD_WORDS.get(op.period, op.period) if op.period else ""
    zones = sorted({str(frame[name].dt.tz) for name in date_keys if frame[name].dt.tz is not None})
    if op.period in DATE_PERIODS and zones:
        period += f", by the clock of {', '.join(zones)}"  # the column's own offset decides where a day ends
    by = " and ".join(keys) + (f" ({period})" if period else "")
    verb = _VERBS[op.how]
    if op.how in ("first", "last"):
        verb = verb.replace(" value", " value (by time)" if date_keys and op.period else " value (in row order)")
    change = f"{verb} {_listed(values)} by {by}: {_count(len(result), 'row')}"
    other = frame.shape[1] - len(keys) - len(values)
    if other:
        change += f", {_count(other, 'other column')} dropped"
    if cast:
        return result, _with_notice(change, cast_note(cast, f"in {_listed(values)}"))
    return result, _with_notice(change, whole_rounded(rounded) if rounded else "")


def _reduce(grouped: Any, values: pd.Series, how: str) -> tuple[pd.Series, int, int]:
    """One value column of an `aggregate` reduced per group (`grouped` is its `SeriesGroupBy`), with the counts of
    whole numbers stored as decimals past the int64 range and of inputs past 2**53 a mean read as decimals."""
    match how:
        case "sum" if is_integer_dtype(values.dtype):
            # In Python integers: pandas' Int64 sum wraps around silently past 2**63 (review of 2026-10-15).
            # Summed outside pandas, which would infer a dtype for the totals; the groups come in the order of `size`.
            totals = [sum(int(value) for value in cells.dropna()) for _, cells in grouped]
            aggregated, rounded = _whole_numbers(totals, grouped.size().index)
            return aggregated, rounded, 0
        case "sum":
            return grouped.agg(_group_sum), 0, 0
        case "mean" if is_integer_dtype(values.dtype):
            return grouped.mean(), 0, _past_exact(values)  # a mean is a float: inputs past 2**53 are counted
        case "mean":
            return grouped.agg(_group_mean), 0, 0
        case "count":
            return grouped.count(), 0, 0
        case "min":
            return grouped.min(), 0, 0
        case "max":
            return grouped.max(), 0, 0
        case "first":
            return grouped.first(), 0, 0  # the first value that is there, as `last` the last one
        case _:
            return grouped.last(), 0, 0


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


def _keep_rows(frame: pd.DataFrame, op: KeepRows, carried: _Carried) -> tuple[pd.DataFrame, str]:
    """The first `n` rows in their current order, the others dropped and counted: after a `sort`, the top N. With
    `where` in place of `n`, the rows that match (`_keep_where`).

    A table of `n` rows or fewer keeps every row, and the line says so: nothing is dropped and nothing is refused.
    """
    if op.where is not None:
        return _keep_where(frame, op.where, carried)
    total, n = len(frame), op.n or 0
    if n >= total:
        return frame, f"kept all {_count(total, 'row')}; there were no more than {n}"
    kept = frame.iloc[:n].reset_index(drop=True)
    line = f"kept the first {n} of {_count(total, 'row')}, {total - n} dropped"
    return kept, line + _tie_note(frame, n, carried, MAX_NOTE_CHARS - len(line))


def _keep_where(frame: pd.DataFrame, where: Sequence[Condition], carried: _Carried) -> tuple[pd.DataFrame, str]:
    """The rows for which every condition holds, the others dropped and counted.

    No matching row is refused, as a `drop_rows` that matches every row is. When every row matches, every row
    stays and the line says so.
    """
    mask, clauses = _rows_where(frame, where, carried)
    total, matching = len(frame), int(mask.sum())
    if not matching:
        raise PrepareError("empty_result", "no row matches the conditions; no row would remain")
    words = " and ".join(clauses)
    if matching == total:
        return frame, f"kept all {_count(total, 'row')}; every one matches {words}"
    kept, dropped = frame[mask].reset_index(drop=True), frame[~mask]
    line = f"kept {matching} of {_count(total, 'row')} where {words}, {total - matching} dropped"
    return kept, line + _unvalued_note(dropped, where) + _offsets_note(dropped, kept)


def _unvalued_note(dropped: pd.DataFrame, where: Sequence[Condition]) -> str:
    """What a `keep_rows` line adds when rows it dropped have no value in a tested column.

    An empty cell matches no test on a value, so "only 2024" also drops the rows without a date. They did not fail
    the test, they had nothing to test, and the count of dropped rows alone does not say so.
    """
    parts = []
    for column in _distinct([condition.column for condition in where if condition.test not in VALUE_FREE_TESTS]):
        empty = int(dropped[column].isna().sum())
        if empty:
            parts.append(f"{empty} of them {'has' if empty == 1 else 'have'} no {column}")
    return f"; {' and '.join(parts)}" if parts else ""


def _tie_note(frame: pd.DataFrame, n: int, carried: _Carried, room: int) -> str:
    """What a top N's line adds when its cut falls among rows of one value in the column the rows were sorted by.

    The cut stays at `n`: which of the tied rows are in is the order they had before the sort, nothing the user
    chose. The note counts the tied rows on each side and names them by the first text column, so the reply can
    say so and the user can ask for more rows or for every row down to that value. Past `room` characters the
    names are left out, so the line's clip never cuts the counts: without the names the line stays under
    `MAX_NOTE_CHARS` for the longest column name and value there can be.
    """
    column = carried.sorted_by
    if column is None or column not in frame.columns:
        return ""
    series = frame[column]
    last = series.iloc[n - 1]
    tied = series.isna() if pd.isna(last) else _bools(series == last)
    inside, outside = int(tied.iloc[:n].sum()), int(tied.iloc[n:].sum())
    if not outside:
        return ""
    shown = _cell_text(last, bool(_with_time(series, carried)))
    if shown is None:
        value = f"no {column}"
    else:
        shown = _clip(shown, MAX_CELL_CHARS)
        value = f"{column} '{shown}'" if _kind(series) == "text" else f"{column} {shown}"
    head = f"; the cut falls among {inside + outside} rows with {value}: "
    counted = f"{head}{inside} kept and {outside} dropped"
    label = next((str(name) for name in frame.columns if name != column and _kind(frame[name]) == "text"), None)
    if label is None:
        return counted
    # By position, never by label: a boolean Series as a mask is aligned on the index first.
    names, mask = frame[label], tied.to_numpy(dtype=bool)
    kept = _tied_names(names.iloc[:n][mask[:n]], label)
    dropped = _tied_names(names.iloc[n:][mask[n:]], label)
    named = f"{head}{inside} kept{kept} and {outside} dropped{dropped}"
    return named if len(named) <= room else counted


def _tied_names(cells: pd.Series, label: str) -> str:
    """` (Stadt 'Köln' and 'Basel')`: the tied rows of one side by their label, at most `SHOWN_TIED_ROWS` of them."""
    names = [f"'{_clip(cell, TIED_NAME_CHARS)}'" if isinstance(cell, str) else "(empty)" for cell in cells]
    listed = names[:SHOWN_TIED_ROWS]
    if len(names) > len(listed):
        listed.append(f"{len(names) - len(listed)} more")
    return f" ({label} {_listed(listed)})"


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
        # A melted column's name too: pandas' `melt` refuses a `value_name` that names an input column with a
        # ValueError, which no caller expects (review of #12206: the `.to_long()` route answered 500).
        if name in rest or name in columns:
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
    if len(kinds) > 1:
        # Unlike kinds melt into one text column: each column's canonical texts, a datetime with its time.
        work = frame.assign(**{name: _texts(frame[name], time) for name, time in zip(columns, times, strict=True)})
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
    if all(YEAR_MONTH.fullmatch(name) for name in columns):
        # Month headers (`2025-01`) are the labels of the long table: the re-parse would read them as dates,
        # which a heatmap's `y` or a box plot's `category` does not take as such (review of #12204).
        carried.text_columns.add(op.names_to)
    if kinds == {"datetime"}:
        carried.with_time[op.values_to] = any(bool(time) for time in times)
    change = f"pivoted {len(columns)} columns into {op.names_to}/{op.values_to}: {_count(rows, 'row')}"
    if rounded:
        change = _with_notice(change, cast_note(rounded, f"beside the decimals of {op.values_to}"))
    return melted, change


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
    names = _texts(work[op.names_from], _with_time(work[op.names_from], carried))
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
    carried.keep_only(index)
    if values_text:
        carried.text_columns.update(distinct)
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
        mask, clauses = _rows_where(frame, rule.where, carried)
        hit = mask & open_rows  # the first rule that holds names a row
        labels[hit] = rule.label
        open_rows &= ~hit
        parts.append(f"'{rule.label}' for {_count(int(hit.sum()), 'row')} where {' and '.join(clauses)}")
    rest = int(open_rows.sum())
    if rest and op.otherwise is not None:
        labels[open_rows] = op.otherwise
        fallback = f"'{op.otherwise}' for the other {_count(rest, 'row')}"
    else:
        fallback = f"{_count(rest, 'row')} without a label" if rest else ""
    if not labels.notna().any():
        raise PrepareError("invalid_operation", f"no row matches a rule, so column '{op.name}' would hold no label")
    # Kept text through the re-parse: labels such as `1` and `2` are categories, not numbers.
    carried.text_columns.add(op.name)
    change = f"added column {op.name}: {', '.join(parts)}"
    if fallback:
        # The rows no rule named are counted, with their largest groups, and never cut from the line: a fallback
        # that took two categories silently is the failure this names (persona tests of 2026-11-06).
        fallback += _fallback_groups(frame, op, open_rows)
    return frame.assign(**{op.name: labels}), _with_notice(change, fallback)


def _fallback_groups(frame: pd.DataFrame, op: Classify, rows: pd.Series) -> str:
    """The largest groups of the rows no rule named, by the text column the rules test most often (the first of
    them on a tie): `, the largest by Kategorie: 'Spenden' 3, 'Bank' 2, 'Post' 1`; "" when the rules test no text
    column or those rows hold no value of it (a threshold on numbers says what fell through by itself). A number
    column the rules test as often never hides the text column's groups."""
    named = Counter(
        condition.column
        for rule in op.rules
        for condition in rule.where
        if condition.column in frame.columns and _kind(frame[condition.column]) == "text"
    )
    if not named:
        return ""
    column = named.most_common(1)[0][0]
    groups = Counter(value for value in frame.loc[rows, column] if isinstance(value, str))
    if not groups:
        return ""
    largest = ", ".join(f"'{_clip(value, 24)}' {count}" for value, count in groups.most_common(FALLBACK_GROUPS))
    return f", the largest by {column}: {largest}"


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
                total = values[0].groupby([frame[key] for key in keys], dropna=False).transform(_group_sum)
            else:
                total = pd.Series(_group_sum(values[0]), index=frame.index)
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
    missing = {key: frame[key].isna() for key in keys}
    totals: dict[tuple[object, ...], int] = {}
    running: dict[object, int | None] = {}
    for row in ordered:
        whole = wholes[row]
        if whole is None:
            running[row] = None
            continue
        # Native key values group as pandas does (`-0.0` with `0.0`); every missing kind is one group (`dropna=False`).
        group = tuple(None if missing[key].at[row] else frame.at[row, key] for key in keys)
        totals[group] = totals.get(group, 0) + whole
        running[row] = totals[group]
    return _whole_numbers([running.get(row) for row in frame.index], frame.index)


def _ordered(
    frame: pd.DataFrame, values: pd.Series, column: str, keys: list[str], order: str, how: str
) -> tuple[pd.Series, str, str]:
    """`percent_change`, `cumsum` or `index` of `values` within each group, in the order of `order`, what it
    computed, and the notice of values stored rounded (an integer running total past int64), else "".

    The rows are put in order as for every ordered operation (`_order_rows`).
    """
    ordered = _order_rows(frame, keys, order, f"derive {how}")
    within = f" within each {' and '.join(keys)}" if keys else ""
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


def _order_rows(frame: pd.DataFrame, keys: list[str], order: str, what: str) -> pd.Index:
    """The rows that have an `order` value, sorted by it (stable): the order every ordered operation walks.

    The order column holds numbers or dates, or the period labels an `aggregate` writes
    (`2024-03`, `2024-Q1`, `2024`), whose text sorts in time order: any other text column
    would sort alphabetically (`April` before `Januar`, `10` before `9`) and give a silently
    wrong result. A row without an order value has no place in the order: its cell stays
    empty and its group's other rows skip it. Two rows of a group with the same order value
    make "previous" a guess and are refused. `what` names the operation in a refusal.
    """
    kind = _kind(frame[order])
    if kind not in ("number", "datetime") and not _period_labels_only(frame[order]):
        raise PrepareError(
            "type_mismatch",
            f"column '{order}' is {kind} and would sort alphabetically; {what} needs a number or datetime "
            "order column: set_type it to number or datetime first",
        )
    placed = frame[frame[order].notna()]
    if placed.duplicated(subset=[*keys, order]).any():
        within = f" within each {' and '.join(keys)}" if keys else ""
        raise PrepareError(
            "invalid_operation",
            f"column '{order}' repeats a value{within}, so the order of the rows is unclear; aggregate first",
        )
    return placed.sort_values(order, kind="stable").index


def _period_labels_only(series: pd.Series) -> bool:
    """Whether a text column holds period labels of one shape only (`_PERIOD_LABEL_SHAPES`), and at least one."""
    if _kind(series) != "text":
        return False
    cells = [cell for cell in series if isinstance(cell, str)]
    return bool(cells) and any(all(shape.fullmatch(cell) for cell in cells) for shape in _PERIOD_LABEL_SHAPES)


def _sequences(frame: pd.DataFrame, keys: list[str], ordered: pd.Index) -> list[list[Hashable]]:
    """The rows of `ordered` by group of `keys`, each group's rows in that order.

    Native key values group as pandas does (`-0.0` with `0.0`), and every missing kind is one group, as the
    `dropna=False` groups of the ordered derives (`_integer_cumsum`).
    """
    missing = {key: frame[key].isna() for key in keys}
    groups: dict[tuple[object, ...], list[Hashable]] = {}
    for row in ordered:
        group = tuple(None if missing[key].at[row] else frame.at[row, key] for key in keys)
        groups.setdefault(group, []).append(row)
    return list(groups.values())


def _empty_clause(reasons: Sequence[tuple[int, str]]) -> str:
    """`3 cells are empty (2 with a missing input, 1 with a division by zero)`: the reasons that hold, each with its
    count; "" when no cell is empty. A change line keeps it whole (`_with_notice`)."""
    present = [(count, reason) for count, reason in reasons if count]
    total = sum(count for count, _ in present)
    if not total:
        return ""
    listed = ", ".join(f"{count} {reason}" for count, reason in present)
    return f"{_count(total, 'cell')} {_be(total)} empty ({listed})"


def _joined(*parts: str) -> str:
    """The notices of a change line that hold something, in order."""
    return ", ".join(part for part in parts if part)


def _new_number_column(frame: pd.DataFrame, name: str, values: pd.Series, carried: _Carried) -> pd.DataFrame:
    """`frame` with the number column `name` appended; refused when no row has a value."""
    if not values.notna().any():
        raise PrepareError("invalid_operation", f"no row has a value for column '{name}'; check the input columns")
    carried.forget([name])
    return frame.assign(**{name: values})


def _number_input(frame: pd.DataFrame, column: str, what: str) -> None:
    """Refuse a column that holds no numbers, with the operation that would make it numbers."""
    _require(frame, column)
    kind = _kind(frame[column])
    if kind == "number":
        return
    hint = "date_number turns dates into numbers" if kind == "datetime" else "set_type it to number first"
    raise PrepareError("type_mismatch", f"column '{column}' is {kind}; {what} needs number columns: {hint}")


# --- compute ---------------------------------------------------------------------------------


class _DividedByZero(Exception):
    """A whole-number step divided by zero (`//`, `%`): the row's cell stays empty."""


class _OutOfRange(Exception):
    """A whole-number step went past what a float64 holds (`_FLOAT_MAX_WHOLE`): the row's cell stays empty."""


def _compute(frame: pd.DataFrame, op: Compute, carried: _Carried) -> tuple[pd.DataFrame, str]:
    """A number column from an expression over number columns, row by row.

    The expression is checked by `generate_data`'s whitelist before a cell is read. Where
    every input is a whole-number column and every step keeps whole numbers whole
    (`_whole_tree`), each row is computed in Python integers, exactly, and a result past the
    int64 range is stored as a float and counted, as `derive` does. Plain arithmetic (`+ - *
    /` over the inputs and number literals, `_decimal_tree`) is computed in exact decimals
    with one rounding to a float at the end, as `diff` and `rolling` compute, so `19.99 * 3`
    is 59.97 and `a - b` writes what `diff` writes. Anything else (a power, a function, a
    constant) is computed in float64, as `derive` computes, never rounded to fewer digits. A cell stays
    empty, and is counted by its reason, when an input is missing, when a step divides by
    zero, or when a step leaves a function's domain or the number range (`log` of 0, `sqrt`
    of a negative number, `exp(1000)`), also when a later step would make the value finite
    again (`atan(1/0)`): every step of a written cell is defined.
    """
    _check_new_columns(frame, [op.name])
    try:
        tree = parse_expression(op.expression, frozenset(op.inputs), f"compute {op.name}")
    except GenerateError as exc:
        raise PrepareError("invalid_operation", exc.message) from None
    used = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    unused = [name for name in op.inputs if name not in used]
    if unused:
        raise PrepareError(
            "invalid_operation", f"compute {op.name}: the input '{unused[0]}' is not in the expression; leave it out"
        )
    columns = list(dict.fromkeys(op.inputs.values()))
    for column in columns:
        _number_input(frame, column, "compute")
    missing = np.zeros(len(frame), dtype=bool)
    for column in columns:
        missing |= frame[column].isna().to_numpy()
    whole = all(is_integer_dtype(frame[column].dtype) for column in columns) and _whole_tree(tree, op.inputs)
    notice = ""
    if whole:
        values, divided, outside, rounded = _compute_whole(frame, op, tree, missing)
        notice = whole_rounded(rounded) if rounded else ""
    elif _decimal_tree(tree, op.inputs):
        values, divided, outside, rounded = _compute_decimal(frame, op, tree, missing)
        notice = stored_rounded(rounded) if rounded else ""
    else:
        values, divided, outside = _compute_floats(frame, op, tree, missing)
        cast = sum(_past_exact(frame[column]) for column in columns if is_integer_dtype(frame[column].dtype))
        notice = cast_note(cast, "in the inputs") if cast else ""
    result = _new_number_column(frame, op.name, values, carried)
    change = f"added column {op.name}: {source_text(op.expression)}"
    named = [f"{name} = {column}" for name, column in op.inputs.items() if name != column]
    if named:
        change += f" with {', '.join(named)}"
    empty = _empty_clause(
        [
            (int(missing.sum()), "with a missing input"),
            (divided, "with a division by zero"),
            (outside, "outside a function's domain or the number range"),
        ]
    )
    return result, _with_notice(change, _joined(empty, notice))


def _whole_tree(node: ast.expr, inputs: Collection[str]) -> bool:
    """Whether every step of a checked tree keeps whole numbers whole: whole literals, the `inputs`, a sign, `+ - * //
    %`, a power with a whole literal exponent of 0 or more, `abs`, `sign`, `min` and `max`; a constant is none."""
    match node:
        case ast.Constant(value=int()):
            return True
        case ast.Name(id=name):
            return name in inputs  # an input named like a constant stands for its column (`InputName`)
        case ast.UnaryOp(operand=operand):
            return _whole_tree(operand, inputs)
        case ast.BinOp(left=left, op=ast.Pow(), right=ast.Constant(value=int() as exponent)):
            return exponent >= 0 and _whole_tree(left, inputs)
        case ast.BinOp(left=left, op=operator, right=right):
            return isinstance(operator, _WHOLE_OPERATORS) and _whole_tree(left, inputs) and _whole_tree(right, inputs)
        case ast.Call(func=ast.Name(id=name), args=args):
            return name in _WHOLE_FUNCTIONS and all(_whole_tree(arg, inputs) for arg in args)
    return False


def _whole_value(node: ast.expr, row: dict[str, int]) -> int:
    """One row's value of a whole tree (`_whole_tree`) in Python integers; raises `_DividedByZero` or `_OutOfRange`."""
    result: int
    match node:
        case ast.Constant(value=int() as number):
            result = number
        case ast.Name(id=name):
            result = row[name]
        case ast.UnaryOp(op=operator, operand=operand):
            inner = _whole_value(operand, row)
            result = -inner if isinstance(operator, ast.USub) else inner
        case ast.BinOp(left=left, op=operator, right=right):
            a, b = _whole_value(left, row), _whole_value(right, row)
            if isinstance(operator, _DIVISIONS) and b == 0:
                raise _DividedByZero
            match operator:
                case ast.Add():
                    result = a + b
                case ast.Sub():
                    result = a - b
                case ast.Mult():
                    result = a * b
                case ast.FloorDiv():
                    result = a // b
                case ast.Mod():
                    result = a % b
                case _:  # a power: checked before it is computed, so a huge one never takes the time it would
                    if abs(a) > 1 and (abs(a).bit_length() - 1) * b > _WHOLE_BITS:
                        raise _OutOfRange
                    result = a**b
        case ast.Call(func=ast.Name(id=name), args=args):
            numbers = [_whole_value(arg, row) for arg in args]
            if name == "abs":
                result = abs(numbers[0])
            elif name == "sign":
                result = (numbers[0] > 0) - (numbers[0] < 0)
            else:
                result = min(numbers) if name == "min" else max(numbers)
        case _:
            raise _OutOfRange  # unreachable for a whole tree
    if abs(result) > _FLOAT_MAX_WHOLE:
        raise _OutOfRange  # past any float64: 2**1023 stays, 2**1024 does not
    return result


def _compute_whole(
    frame: pd.DataFrame, op: Compute, tree: ast.expr, missing: np.ndarray
) -> tuple[pd.Series, int, int, int]:
    """The rows in Python integers: the values (`_whole_numbers`), the cells divided by zero and beyond the range,
    and the results past the int64 range stored as floats past 2**53."""
    cells = {name: frame[column].tolist() for name, column in op.inputs.items()}
    results: list[int | None] = []
    divided = outside = 0
    for position, gap in enumerate(missing):
        if gap:
            results.append(None)
            continue
        try:
            results.append(_whole_value(tree, {name: int(values[position]) for name, values in cells.items()}))
        except _DividedByZero:
            divided += 1
            results.append(None)
        except _OutOfRange:
            outside += 1
            results.append(None)
    values, rounded = _whole_numbers(results, frame.index)
    return values, divided, outside, rounded


_DECIMAL_OPERATORS = (ast.Add, ast.Sub, ast.Mult, ast.Div)


def _decimal_tree(node: ast.expr, inputs: Collection[str]) -> bool:
    """Whether a checked tree is plain arithmetic: number literals, the `inputs`, a sign and `+ - * /`.

    Such a tree is computed in exact decimals (`_compute_decimal`), as `diff`, `rolling` and an `aggregate` sum add
    their cells, so `19.99 * 3` is 59.97 and never 59.96999999999999. A power, `//`, `%`, a constant and the functions
    take float64.
    """
    match node:
        case ast.Constant(value=int() | float() as number):
            return math.isfinite(number)
        case ast.Name(id=name):
            return name in inputs
        case ast.UnaryOp(operand=operand):
            return _decimal_tree(operand, inputs)
        case ast.BinOp(left=left, op=operator, right=right):
            return (
                isinstance(operator, _DECIMAL_OPERATORS)
                and _decimal_tree(left, inputs)
                and _decimal_tree(right, inputs)
            )
    return False


def _decimal_value(node: ast.expr, row: dict[str, ExactDecimal]) -> ExactDecimal:
    """One row's value of a plain arithmetic tree (`_decimal_tree`) in exact decimals; raises `_DividedByZero`."""
    match node:
        case ast.Constant(value=int() | float() as number):
            # A literal as written: `0.1` is the decimal 0.1, its float's shortest form.
            return ExactDecimal(number) if isinstance(number, int) else ExactDecimal(repr(number))
        case ast.Name(id=name):
            return row[name]
        case ast.UnaryOp(op=operator, operand=operand):
            inner = _decimal_value(operand, row)
            return -inner if isinstance(operator, ast.USub) else inner
        case ast.BinOp(left=left, op=operator, right=right):
            a, b = _decimal_value(left, row), _decimal_value(right, row)
            if isinstance(operator, ast.Add):
                return a + b
            if isinstance(operator, ast.Sub):
                return a - b
            if isinstance(operator, ast.Mult):
                return a * b
            if b == 0:
                raise _DividedByZero
            return a / b
    raise ValueError("not a plain arithmetic tree")  # unreachable: `_decimal_tree` admits no other node


def _compute_decimal(
    frame: pd.DataFrame, op: Compute, tree: ast.expr, missing: np.ndarray
) -> tuple[pd.Series, int, int, int]:
    """The rows in exact decimals at `_DECIMAL_DIGITS` digits, each cell read as `_ordered_input` reads it (a whole
    number exactly, a decimal as its cell writes it), with one rounding to a float at the end: the values, the cells
    divided by zero, the results beyond the float range, which stay empty, and the results past 2**53 that the float
    holds only rounded (`9007199254740993` becomes ...992; `_past_float`), which the change line counts."""
    cells: dict[str, list[ExactDecimal | None]] = {}
    for name, column in op.inputs.items():
        whole = is_integer_dtype(frame[column].dtype)
        cells[name] = [
            None if pd.isna(value) else ExactDecimal(int(value)) if whole else ExactDecimal(repr(float(value)))
            for value in frame[column]
        ]
    results: list[float] = []
    divided = outside = rounded = 0
    with localcontext() as context:
        context.prec = _DECIMAL_DIGITS
        for position, gap in enumerate(missing):
            row = {name: values[position] for name, values in cells.items()}
            present = {name: value for name, value in row.items() if value is not None}
            if gap or len(present) < len(row):
                results.append(math.nan)
                continue
            try:
                exact = _decimal_value(tree, present)
            except _DividedByZero:
                divided += 1
                results.append(math.nan)
                continue
            number = float(exact)
            if not math.isfinite(number):
                outside += 1
                number = math.nan
            elif _past_float(exact, number):
                rounded += 1
            results.append(number)
    return pd.Series(results, index=frame.index, dtype="float64"), divided, outside, rounded


def _compute_floats(
    frame: pd.DataFrame, op: Compute, tree: ast.expr, missing: np.ndarray
) -> tuple[pd.Series, int, int]:
    """The rows in float64 (`generate.evaluate`): the values, and the cells divided by zero and outside a domain.

    Every step's value is seen (`visit`): a row where a step's divisor is 0 counts as divided by zero, a row where a
    step is not finite as outside a domain or the range; a missing input counts as that alone.
    """
    size = len(frame)
    inputs = {name: frame[column].to_numpy(dtype=np.float64, na_value=np.nan) for name, column in op.inputs.items()}
    seen: dict[int, np.ndarray] = {}
    divided = np.zeros(size, dtype=bool)
    undefined = np.zeros(size, dtype=bool)

    def visit(node: ast.expr, value: np.ndarray) -> None:
        full = np.broadcast_to(value, (size,))
        seen[id(node)] = full
        if isinstance(node, ast.BinOp) and isinstance(node.op, _DIVISIONS):
            np.logical_or(divided, seen[id(node.right)] == 0, out=divided)
        np.logical_or(undefined, ~np.isfinite(full), out=undefined)

    with np.errstate(all="ignore"):
        result = np.array(np.broadcast_to(evaluate(tree, inputs, visit), (size,)), dtype=np.float64)
    divided &= ~missing
    undefined &= ~missing & ~divided
    result[missing | divided | undefined] = np.nan
    return pd.Series(result, index=frame.index, dtype="float64"), int(divided.sum()), int(undefined.sum())


# --- diff and rolling -----------------------------------------------------------------------


def _ordered_input(
    frame: pd.DataFrame, op: Diff | Rolling, what: str
) -> tuple[list[str], pd.Index, dict[Hashable, ExactDecimal | None]]:
    """The checks a `diff` and a `rolling` share, the ordered rows, and each row's value as an exact decimal: the
    whole number, or the decimal the cell writes (`_decimal_total`'s reading); None when missing."""
    _check_new_columns(frame, [op.name])
    keys = _distinct(op.within)
    for name in [*keys, op.order]:
        _require(frame, name)
    _number_input(frame, op.column, what)
    if op.column in {*keys, op.order}:
        raise PrepareError("invalid_operation", "a value column cannot also be a within or order column")
    ordered = _order_rows(frame, keys, op.order, what)
    whole = is_integer_dtype(frame[op.column].dtype)
    cells: dict[Hashable, ExactDecimal | None] = {}
    for row, value in frame[op.column].items():
        if pd.isna(value):
            cells[row] = None
        else:
            cells[row] = ExactDecimal(int(value)) if whole else ExactDecimal(repr(float(value)))
    return keys, ordered, cells


def _number_values(
    frame: pd.DataFrame, results: dict[Hashable, ExactDecimal], whole: bool
) -> tuple[pd.Series, int, str]:
    """The exact results as the new column: whole numbers as integers (`_whole_numbers`), decimals as the nearest
    float. Returns the values, the results beyond the float range, which stay empty, and the notice of results a
    float holds only rounded: whole numbers past the int64 range (`whole_rounded`), or decimals past 2**53, such as
    the mean of two ids that large (`stored_rounded`)."""
    if whole:
        exact = [None if (value := results.get(row)) is None else int(value) for row in frame.index]
        values, rounded = _whole_numbers(exact, frame.index)
        return values, 0, whole_rounded(rounded) if rounded else ""
    floats: list[float] = []
    outside = rounded = 0
    for row in frame.index:
        value = results.get(row)
        number = math.nan if value is None else float(value)
        if value is not None and not math.isfinite(number):
            outside += 1
            number = math.nan
        elif value is not None and _past_float(value, number):
            rounded += 1
        floats.append(number)
    return pd.Series(floats, index=frame.index, dtype="float64"), outside, stored_rounded(rounded) if rounded else ""


def _past_float(exact: ExactDecimal, number: float) -> bool:
    """Whether an exact result past 2**53, where a float holds no fraction and not every whole number, is held by
    its float `number` only rounded."""
    return abs(exact) > _FLOAT_EXACT and ExactDecimal(number) != exact


def stored_rounded(count: int) -> str:
    """The change-line clause of exact results past 2**53 that their float column holds only rounded."""
    return (
        f"{_count(count, 'value')} past 2^53 {_be(count)} stored as decimal numbers "
        "(15 to 17 significant digits; a digit past them is rounded)"
    )


def _diff(frame: pd.DataFrame, op: Diff, carried: _Carried) -> tuple[pd.DataFrame, str]:
    """Each row's value minus the one `lag` rows before it in its group, in the order of `order`.

    The values subtract as exact decimals (`_DECIMAL_DIGITS` digits): whole numbers stay whole and exact, and
    decimals subtract as their cells write them, so `12.3 - 10.1` is `2.2`, as `_decimal_total` adds them, never
    the float noise `2.200000000000001`. The first `lag` rows of each group have no row before them and stay
    empty, as does a row whose value or earlier value is missing; every empty cell is counted by its reason.
    """
    keys, ordered, cells = _ordered_input(frame, op, "diff")
    whole = is_integer_dtype(frame[op.column].dtype)
    results: dict[Hashable, ExactDecimal] = {}
    first = gap = 0
    with localcontext() as context:
        context.prec = _DECIMAL_DIGITS
        for rows in _sequences(frame, keys, ordered):
            for position, row in enumerate(rows):
                if position < op.lag:
                    first += 1
                    continue
                current, previous = cells[row], cells[rows[position - op.lag]]
                if current is None or previous is None:
                    gap += 1
                    continue
                results[row] = current - previous
    values, outside, notice = _number_values(frame, results, whole)
    result = _new_number_column(frame, op.name, values, carried)
    within = f" within each {' and '.join(keys)}" if keys else ""
    before = f"the previous {op.order}" if op.lag == 1 else f"{op.lag} rows before in the order of {op.order}"
    change = f"added column {op.name}: change of {op.column} from {before}{within}"
    empty = _empty_clause(
        [
            (first, f"without {'a row' if op.lag == 1 else f'{op.lag} rows'} before them"),
            (gap, "with a missing value"),
            (len(frame) - len(ordered), f"without a {op.order}"),
            (outside, "beyond the number range"),
        ]
    )
    return result, _with_notice(change, _joined(empty, notice))


def _rolling(frame: pd.DataFrame, op: Rolling, carried: _Carried) -> tuple[pd.DataFrame, str]:
    """The mean or the sum of the `window` rows up to each row in its group, in the order of `order`.

    The window trails: a row and the `window - 1` rows before it, so the first `window - 1` rows of each group stay
    empty, as does a row whose window holds a missing value (a shorter window would be another mean). A whole-number
    sum stays a whole number; every other window adds the decimals its cells write, with `_DECIMAL_DIGITS` digits,
    and a mean divides that total once, so no float noise builds up along the rows. A window over a span of time
    (seven days of irregular readings) is no option: an `aggregate` by `day` first makes it a window of rows.
    """
    keys, ordered, cells = _ordered_input(frame, op, "rolling")
    whole = is_integer_dtype(frame[op.column].dtype) and op.how == "sum"
    results: dict[Hashable, ExactDecimal] = {}
    short = gap = 0
    with localcontext() as context:
        context.prec = _DECIMAL_DIGITS
        for rows in _sequences(frame, keys, ordered):
            # Running totals and running counts of missing cells: a window is the difference of two of each.
            totals, gaps = [ExactDecimal(0)], [0]
            for row in rows:
                cell = cells[row]
                totals.append(totals[-1] + (ExactDecimal(0) if cell is None else cell))
                gaps.append(gaps[-1] + (cell is None))
            for position, row in enumerate(rows):
                start = position + 1 - op.window
                if start < 0:
                    short += 1
                    continue
                if gaps[position + 1] - gaps[start]:
                    gap += 1
                    continue
                total = totals[position + 1] - totals[start]
                results[row] = total if op.how == "sum" else total / op.window
    values, outside, notice = _number_values(frame, results, whole)
    result = _new_number_column(frame, op.name, values, carried)
    within = f" within each {' and '.join(keys)}" if keys else ""
    change = f"added column {op.name}: {op.how} of {op.column} over {op.window} rows in the order of {op.order}{within}"
    empty = _empty_clause(
        [
            (short, f"before a full window of {op.window} rows"),
            (gap, "with a missing value in the window"),
            (len(frame) - len(ordered), f"without a {op.order}"),
            (outside, "beyond the number range"),
        ]
    )
    return result, _with_notice(change, _joined(empty, notice))


# --- blank -----------------------------------------------------------------------------------


def _blank(frame: pd.DataFrame, op: Blank, carried: _Carried) -> tuple[pd.DataFrame, str]:
    """The cells of `columns` emptied in the rows where every condition holds; the rows stay, nothing is filled in.

    Each column counts the cells it had and lost; a column that would lose every value is refused (`drop_columns`
    removes a column). The emptied column's cells as pasted are forgotten, so a later re-reading of the paste
    (`set_type` with a decimal comma) never brings them back.
    """
    columns = _distinct(op.columns)
    for name in columns:
        _require(frame, name)
    mask, clauses = _rows_where(frame, op.where, carried)
    result = frame.copy()
    counts: list[int] = []
    for name in columns:
        series = frame[name]
        hit = mask & series.notna()
        count = int(hit.sum())
        if count and count == int(series.notna().sum()):
            raise PrepareError(
                "invalid_operation",
                f"every value of column '{name}' matches, so it would be empty; drop_columns removes it",
            )
        if is_bool_dtype(series.dtype):
            series = series.astype("boolean")  # a numpy bool column holds no missing cell
        result[name] = series.mask(hit)
        counts.append(count)
        carried.pasted_cells.pop(name, None)
    total = sum(counts)
    where = " and ".join(clauses)
    if len(columns) == 1:
        return result, f"emptied {_count(total, 'cell')} of {columns[0]} where {where}; the rows stay"
    per = ", ".join(f"{count} of {name}" for name, count in zip(columns, counts, strict=True))
    return result, f"emptied {_count(total, 'cell')} ({per}) where {where}; the rows stay"


def _row_number(frame: pd.DataFrame, op: RowNumber, carried: _Carried) -> tuple[pd.DataFrame, str]:
    # The row numbers label the rows, so they stand first; only the order of the columns changes, never a value.
    if op.name in frame.columns:
        if not _numbers_the_rows(frame[op.name]):
            raise PrepareError("invalid_operation", f"a column named '{op.name}' already exists")
        carried.row_numbers.add(op.name)
        if frame.columns[0] == op.name:
            return frame, f"{op.name} already numbers the rows"
        moved = frame[[op.name, *(column for column in frame.columns if column != op.name)]]
        return moved, f"{op.name} already numbers the rows; moved to the first column"
    if frame.shape[1] >= MAX_COLUMNS:
        raise PrepareError("too_wide", f"the data already has {frame.shape[1]} columns; at most {MAX_COLUMNS} fit")
    result = frame.copy()
    result.insert(0, op.name, pd.Series(range(1, len(frame) + 1), index=frame.index, dtype="Int64"))
    carried.row_numbers.add(op.name)
    return result, f"new first column {op.name}: the rows numbered 1 to {len(frame):,}"


def _numbers_the_rows(series: pd.Series) -> bool:
    """Whether a column holds `1` to `n` or `0` to `n - 1`, each once, none missing, as `bindings.row_number_columns`."""
    if _kind(series) != "number" or series.isna().any():
        return False
    values = set(series)
    return values in (set(range(1, len(series) + 1)), set(range(len(series))))


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


def _date_number(frame: pd.DataFrame, op: DateNumber, carried: _Carried) -> tuple[pd.DataFrame, str]:
    """A number column from a datetime column: its year, its decimal year, its days since the earliest date, or its
    Unix time in seconds; a missing date stays missing, and the source column stays as it is."""
    _require(frame, op.column)
    series = frame[op.column]
    kind = _kind(series)
    if kind != "datetime":
        raise PrepareError(
            "type_mismatch",
            f"column '{op.column}' is {kind}; date_number needs a datetime column: set_type it to datetime first",
        )
    taken = {str(name) for name in frame.columns}
    name = op.name or suffixed_name(op.column, date_unit_word(op.unit, carried.language), taken)
    _check_new_columns(frame, [name])
    moments: list[pd.Timestamp | None] = [None if pd.isna(value) else value for value in series]
    present = [moment for moment in moments if moment is not None]
    if not present:
        raise PrepareError(
            "invalid_operation", f"column '{op.column}' holds no date, so column '{name}' would be empty"
        )
    notice = ""
    match op.unit:
        case "year":
            values = pd.Series(pd.array([None if m is None else m.year for m in moments], dtype="Int64"))
            reading = "read as calendar years"
        case "decimal_year":
            values = pd.Series([np.nan if m is None else _decimal_year(m) for m in moments], dtype="float64")
            reading = "read as decimal years (the year plus the part of it gone by)"
        case "days":
            earliest = min(_wall(moment).date() for moment in present)
            days = [None if m is None else (_wall(m).date() - earliest).days for m in moments]
            values = pd.Series(pd.array(days, dtype="Int64"))
            reading = f"read as whole days since {earliest.isoformat()}, the earliest date, which is 0"
        case "timestamp":
            values, notice = _unix_seconds(moments, series, carried)
            reading = "read as Unix time in seconds (UTC)"
    zone = series.dt.tz
    if zone is not None and op.unit != "timestamp":
        reading += f", by the clock of {zone}"  # the column's own offset decides where a year or a day ends
    result = frame.copy()
    result[name] = values.set_axis(frame.index)
    carried.forget([name])
    carried.converted[name] = op.column  # an open required role that takes numbers takes it (`carry_bindings`)
    change = f"new column {name}: {_count(len(present), 'date')} of {op.column} {reading}"
    empty = len(moments) - len(present)
    if empty:
        change += f", {_count(empty, 'cell')} without a date {_be(empty)} empty"
    return result, _with_notice(f"{change}; {op.column} stays as it is", notice)


def date_unit_word(unit: str, language: str) -> str:
    """The word for `unit` in the session language (`DATE_UNIT_WORDS`), English for a language without its words."""
    return DATE_UNIT_WORDS.get(canonical(language), DATE_UNIT_WORDS[DEFAULT_LANGUAGE])[unit]


def suffixed_name(column: str, word: str, taken: Collection[str]) -> str:
    """`<column> (<word>)` within the column-name cap, `_2`, `_3`, ... before the bracket when it is taken."""
    suffix = f" ({word})"
    stem = column[: MAX_COLUMN_NAME_CHARS - len(suffix)].rstrip()
    name, number = stem + suffix, 2
    while name in taken:
        tail = f"_{number}"
        name = column[: MAX_COLUMN_NAME_CHARS - len(suffix) - len(tail)].rstrip() + tail + suffix
        number += 1
    return name


def _wall(moment: pd.Timestamp) -> datetime:
    """The moment on the column's own clock, as its cell writes it, without the offset."""
    clock = moment.tz_localize(None) if moment.tzinfo is not None else moment
    return clock.to_pydatetime(warn=False)


def _decimal_year(moment: pd.Timestamp) -> float:
    """The year plus the part of it gone by at `moment`, on the column's clock: 1 April 2021 is about 2021.2466.

    Counted in whole microseconds against the length of that year (366 days in a leap year), so the only rounding is
    the float's own; a date without a time is the start of its day.
    """
    wall = _wall(moment)
    gone = (wall - datetime(wall.year, 1, 1)) // timedelta(microseconds=1)
    length = (366 if calendar.isleap(wall.year) else 365) * _DAY_MICROSECONDS
    return wall.year + gone / length


def _unix_seconds(moments: list[pd.Timestamp | None], series: pd.Series, carried: _Carried) -> tuple[pd.Series, str]:
    """The Unix time of each moment in seconds, UTC, and the notice of how the column's clock was read.

    A moment with a UTC offset is converted; one without is read as UTC, a date as its midnight UTC. Whole seconds stay
    whole numbers (`Int64`, exact for every year from 1 to 9999); a column with a fraction of a second is float64 with
    the fraction kept as decimals, which the notice says. A float64 keeps every microsecond only below 2**33 seconds,
    about 272 years from 1970 (its spacing there is 2**-20 of a second): a value whose written text (its shortest
    `repr`, as `data.csv` writes it) is not its exact microseconds is counted in the notice. A whole second that far
    away is held exactly and is not counted (Copilot on #12558).
    """
    micros: list[int | None] = []
    for moment in moments:
        if moment is None:
            micros.append(None)
            continue
        value = moment.to_pydatetime(warn=False)
        epoch = _EPOCH.replace(tzinfo=UTC) if value.tzinfo is not None else _EPOCH
        micros.append((value - epoch) // timedelta(microseconds=1))
    zone = series.dt.tz
    if zone is not None:
        notice = "the moments as stored, in UTC" if str(zone) == "UTC" else f"the moments converted to UTC from {zone}"
    elif _with_time(series, carried):
        notice = "times without a UTC offset read as UTC"
    else:
        notice = "each date counted from its midnight UTC"
    if all(value is None or value % _MICROSECONDS == 0 for value in micros):
        whole = [None if value is None else value // _MICROSECONDS for value in micros]
        return pd.Series(pd.array(whole, dtype="Int64")), notice
    seconds = [np.nan if value is None else value / _MICROSECONDS for value in micros]
    notice += "; fractions of a second kept as decimals"
    rounded = sum(
        1
        for value, second in zip(micros, seconds, strict=True)
        if value is not None and ExactDecimal(repr(second)) * _MICROSECONDS != value
    )
    if rounded:
        notice += f", {_count(rounded, 'value')} more than 272 years from 1970 rounded to the float's digits"
    return pd.Series(seconds, dtype="float64"), notice


# --- Text operations -------------------------------------------------------------------------


@dataclass(frozen=True)
class _Typed:
    """The cells of a new column of a text operation as `set_type` reads them (`_typed`), with the change line's words."""

    values: pd.Series
    kind: Literal["number", "datetime", "text"]
    reading: str
    failed: int = 0
    notice: str = ""
    with_time: bool = False
    order: str | None = None


def _typed(texts: pd.Series, decimal: str) -> _Typed:
    """Text cells typed as `set_type` would type them: numbers, else dates, else text.

    Numbers are read with the dataset's decimal mark first and its thousands rules (`_number_conversion`),
    dates with the inferred format (`_date_conversion`); either holds when at most `MAX_FAILED_SHARE` of the
    cells fail, which become missing. A number counts only in a cell the parser reads as one (`value_like`:
    `10 kg`, `CHF 1'200`), never behind a word `set_type` would take off as a unit when asked to (`Q1`, `x3`
    are labels). Numbers with leading zeros stay text, as the parser keeps them (`007` is a code), a number
    behind a month name (`Nov 2026`) is a date, and a column with a cell of digits alone is never one
    (pandas reads `00123` as the year 123). Cells whose decimal mark could as well separate thousands
    (`_mark_open`) stay text too, with `OPEN_MARK_READING`: the parser keeps the pasted cells of such a column
    to read them again, and a new column has none.
    """
    present = int(texts.notna().sum())
    if not present:
        return _Typed(texts, "text", TEXT_READING)
    loose = pd.Series([isinstance(text, str) and not value_like(text) for text in texts], index=texts.index)
    number = _attempt(lambda: _number_conversion(texts.mask(loose), decimal))
    if number is not None:
        failed = number.failed + int(loose.sum())
        if failed <= MAX_FAILED_SHARE * present and not (number.unit and _names_month(number.unit)):
            if number.guess == LEADING_ZEROS:
                return _Typed(texts, "text", TEXT_READING)
            if _mark_open(texts, number):
                return _Typed(texts, "text", OPEN_MARK_READING)
            return _Typed(number.values, "number", number.reading, failed, number.notice)
    if any(isinstance(text, str) and _DIGITS_ONLY.fullmatch(text) for text in texts):
        return _Typed(texts, "text", TEXT_READING)
    dates = _attempt(lambda: _date_conversion(texts, None))
    if dates is not None and dates.failed <= MAX_FAILED_SHARE * present:
        return _Typed(dates.values, "datetime", dates.reading, dates.failed, dates.notice, dates.with_time, dates.order)
    return _Typed(texts, "text", TEXT_READING)


_DIGITS_ONLY = re.compile(r"[0-9]+")


def _attempt(convert: Callable[[], Conversion]) -> Conversion | None:
    """A conversion, or None when `set_type` would refuse it (two units, times with and without an offset)."""
    try:
        return convert()
    except PrepareError:
        return None


def _source_texts(frame: pd.DataFrame, column: str, carried: _Carried, literals: Iterable[str] = ()) -> pd.Series:
    """The cell texts of `column` that a text operation reads, whatever the column's type; `literals` are the texts
    the operation looks for in them.

    A number column's canonical text is not what was pasted (`7.000` is stored as `7`, `38.790` as `38.79`), so an
    operation on its decimal marks would drop digits without a word. It reads the cells as pasted while they still
    lie one per row (`_Carried.pasted_cells`, as `set_type` with a decimal comma does), and is refused otherwise
    when it looks for a `.` or a `,`.
    """
    _require(frame, column)
    series = frame[column]
    if _kind(series) == "number":
        pasted = carried.pasted_cells.get(column)
        if pasted is not None and not carried.rows_changed and len(pasted) == len(frame):
            return pd.Series([cell or None for cell in pasted], index=frame.index, name=column, dtype="object")
        if any("." in literal or "," in literal for literal in literals):
            raise PrepareError(
                "type_mismatch",
                f"column '{column}' holds numbers, stored without the marks and the trailing zeros they were written "
                "with (`7.000` is `7`), so a text operation on its `.` or `,` would lose digits: use the text "
                "column these numbers came from, or undo to the pasted data first",
            )
    return _texts(series, _with_time(series, carried))


def _check_new_columns(frame: pd.DataFrame, names: list[str]) -> None:
    if len(set(names)) != len(names):
        raise PrepareError("invalid_operation", "the new columns need different names")
    for name in names:
        if name in frame.columns:
            raise PrepareError("invalid_operation", f"a column named '{name}' already exists")
    if frame.shape[1] + len(names) > MAX_COLUMNS:
        raise PrepareError(
            "too_wide",
            f"the data has {frame.shape[1]} columns; {len(names)} more would exceed the {MAX_COLUMNS} that fit",
        )


def _place(frame: pd.DataFrame, carried: _Carried, source: str, name: str, typed: _Typed) -> None:
    """`typed` as the new column `name` of `frame`, with what the CSV does not say about it carried."""
    frame[name] = typed.values
    carried.forget([name])
    if typed.kind == "text":
        carried.text_columns.add(name)  # kept text through the re-parse, as the change line says
        return
    carried.converted[name] = source  # an open required role takes it, as it takes a `set_type` with `name`
    if typed.kind == "datetime":
        carried.with_time[name] = typed.with_time
        if typed.order is not None:
            carried.date_order[name] = typed.order


def _readings(names: list[str], typed: list[_Typed]) -> str:
    """The change line's clause of how the new columns read: `min and max read as numbers; b kept as text`."""
    groups: dict[str, list[str]] = {}
    for name, item in zip(names, typed, strict=True):
        groups.setdefault(item.reading, []).append(name)
    clauses = [f"{_listed(group)} {reading}" for reading, group in groups.items()]
    clauses += [
        f"{_count(item.failed, 'cell')} of {name} could not be read and {_be(item.failed)} now missing"
        for name, item in zip(names, typed, strict=True)
        if item.failed
    ]
    return "; ".join(clauses)


def _notices(typed: list[_Typed]) -> str:
    return "; ".join(dict.fromkeys(item.notice for item in typed if item.notice))


def _shown_literal(text: str) -> str:
    """A literal of a text operation as the change line quotes it; spaces alone as words."""
    return "spaces" if not text.strip() else f"'{_clip(text, MAX_CELL_CHARS)}'"


def _cuts(text: str, separator: str) -> list[tuple[int, int]]:
    """Where `separator` cuts the trimmed cell `text`, as (start, end) pairs.

    A separator of spaces cuts at every run of whitespace, so `10  25` is two parts, not three. A `-` or `−`
    that starts a part, with at most spaces before it, right before a number is that part's minus sign, never a
    cut: `-5-10` is -5 and 10, `-10--5` is -10 and -5, `-.5-1` is -.5 and 1.
    """
    if not separator.strip():
        return [(match.start(), match.end()) for match in _SPACES.finditer(text)]
    cuts: list[tuple[int, int]] = []
    start = at = 0
    while (found := text.find(separator, at)) != -1:
        end = found + len(separator)
        if separator in _SIGNS and not text[start:found].strip() and _starts_number(text[end : end + 2]):
            at = end
            continue
        cuts.append((found, end))
        start = at = end
    return cuts


_ASCII_DIGITS = frozenset("0123456789")


def _starts_number(text: str) -> bool:
    """Whether `text` opens with a digit, or with a decimal mark before a digit (`.5`, `,5`)."""
    return text[:1] in _ASCII_DIGITS or (text[:1] in ".," and text[1:2] in _ASCII_DIGITS)


def _pieces(text: str, separator: str, parts: int) -> list[str]:
    """The trimmed cell `text` cut at its first `parts - 1` separators (`_cuts`), each piece trimmed."""
    text = text.strip()
    pieces: list[str] = []
    start = 0
    for begin, end in _cuts(text, separator)[: parts - 1]:
        pieces.append(text[start:begin].strip())
        start = end
    pieces.append(text[start:].strip())
    return pieces


def _split(frame: pd.DataFrame, op: Split, carried: _Carried) -> tuple[pd.DataFrame, str]:
    texts = _source_texts(frame, op.column, carried, [op.separator])
    names = list(op.names)
    _check_new_columns(frame, names)
    parts: list[list[str | None]] = [[] for _ in names]
    present = split = more = 0
    for text in texts:
        if not isinstance(text, str):
            for part in parts:
                part.append(None)
            continue
        present += 1
        cuts = len(_cuts(text.strip(), op.separator))
        split += cuts > 0
        more += cuts >= len(names)
        pieces = _pieces(text, op.separator, len(names))
        for position, part in enumerate(parts):
            part.append((pieces[position] if position < len(pieces) else "") or None)
    if not split:
        raise PrepareError("invalid_operation", f"no cell of column '{op.column}' holds {_shown_literal(op.separator)}")
    for name, part in zip(names, parts, strict=True):
        if not any(part):
            raise PrepareError("invalid_operation", f"no cell has a part for column '{name}'; split into fewer columns")
    typed = [_typed(pd.Series(part, index=frame.index, dtype="str"), carried.decimal) for part in parts]
    result = frame.copy()
    for name, item in zip(names, typed, strict=True):
        _place(result, carried, op.column, name, item)
    carried.splits.append(names)
    change = (
        f"split {op.column} at {_shown_literal(op.separator)} into {_listed(names)}: "
        f"{split} of {_count(present, 'cell')} split"
    )
    if present - split:
        change += f", {_count(present - split, 'cell')} without it kept whole in {names[0]}"
    if more:
        change += f", {more} with more keep the rest in {names[-1]}"
    change += f"; {_readings(names, typed)}; {op.column} stays as it is"
    return result, _with_notice(change, _notices(typed))


# One number inside text: an optional sign at the start, after a space, a bracket, a comparison mark, a currency
# sign or code or an abbreviation's dot (`$-100`, `USD-20`, `ca.-15`; never after a digit or another letter: `A-12`
# is 12, `5-10` holds two
# numbers), with a currency sign or code between the sign and the digits (`-$100`, `−€ 5`); then digits with
# decimal marks or thousands groups of three after a space or an apostrophe, or a fraction that starts with its
# mark (`.5`, not after a letter).
_NUMBER_IN_TEXT = re.compile(
    r"(?:(?:^|(?<=[\s(\[{:=~≈<>$€£¥])|(?<=CHF|EUR|USD|GBP)|(?<=[^\W\d_]\.))"
    r"(?P<sign>[+\-−])(?:(?:[$€£¥]|CHF|EUR|USD|GBP)\s?)?)?"
    r"(?P<body>[0-9]+(?:[.,][0-9]+|[\s'’][0-9]{3}(?![0-9]))*|(?<![^\W\d_])[.,][0-9]+)"
)


def _one_number(text: str) -> str | None:
    """The one number inside `text` (`#12345`, `CHF 1'200`, `ca. -3,5 °C`, `-$100`), its sign and digits as written;
    None for none or several."""
    found = list(_NUMBER_IN_TEXT.finditer(text))
    if len(found) != 1:
        return None
    return (found[0]["sign"] or "") + found[0]["body"].replace("’", "'")


def _kept(text: str, keep: Keep) -> str:
    """Only the ASCII digits of `text`, or only its letters with single spaces where whitespace stood between them."""
    if keep == "digits":
        return "".join(char for char in text if char in _ASCII_DIGITS)
    return " ".join("".join(char for char in text if char.isalpha() or char.isspace()).split())


def _extract(frame: pd.DataFrame, op: Extract, carried: _Carried) -> tuple[pd.DataFrame, str]:
    # The digits of a number drop its decimal mark: on a number column that is an operation on the mark.
    texts = _source_texts(frame, op.column, carried, ["."] if op.keep == "digits" else ())
    _check_new_columns(frame, [op.name])
    present = int(texts.notna().sum())
    result = frame.copy()
    if op.keep == "number":
        found = [_one_number(text) if isinstance(text, str) else None for text in texts]
        without = sum(isinstance(text, str) and number is None for text, number in zip(texts, found, strict=True))
        conversion = _number_conversion(pd.Series(found, index=frame.index, dtype="str"), carried.decimal)
        failed = without + conversion.failed
        if not present or failed / present > MAX_FAILED_SHARE:
            raise PrepareError(
                "type_mismatch", f"column '{op.column}': {failed} of {present} cells hold no number, or more than one"
            )
        typed = _Typed(conversion.values, "number", conversion.reading, failed, conversion.notice)
        _place(result, carried, op.column, op.name, typed)
        change = f"new column {op.name}: the number in {present - failed} of {_count(present, 'cell')} of {op.column}"
        change += f", {conversion.reading}"
        if failed:
            change += f", {_count(failed, 'cell')} without exactly one number {_be(failed)} missing"
        return result, _with_notice(f"{change}; {op.column} stays as it is", conversion.notice)
    kept = [_kept(text, op.keep) or None if isinstance(text, str) else None for text in texts]
    empty = sum(isinstance(text, str) and value is None for text, value in zip(texts, kept, strict=True))
    word = "digit" if op.keep == "digits" else "letter"
    if empty == present:
        raise PrepareError("invalid_operation", f"no cell of column '{op.column}' holds a {word}")
    typed = _typed(pd.Series(kept, index=frame.index, dtype="str"), carried.decimal)
    _place(result, carried, op.column, op.name, typed)
    change = f"new column {op.name}: the {op.keep} of {present - empty} of {_count(present, 'cell')} of {op.column}"
    if empty:
        change += f", {_count(empty, 'cell')} without a {word} {_be(empty)} empty"
    change += f"; {_readings([op.name], [typed])}; {op.column} stays as it is"
    return result, _with_notice(change, typed.notice)


def _strip(frame: pd.DataFrame, op: Strip, carried: _Carried) -> tuple[pd.DataFrame, str]:
    if op.prefix is None and op.suffix is None:
        raise PrepareError("invalid_operation", "strip needs a prefix, a suffix or both")
    texts = _source_texts(frame, op.column, carried, [op.prefix or "", op.suffix or ""])
    _check_new_columns(frame, [op.name])
    prefix, suffix = op.prefix or "", op.suffix or ""
    cells: list[str | None] = []
    present = changed = 0
    for text in texts:
        if not isinstance(text, str):
            cells.append(None)
            continue
        present += 1
        cell = text.strip()
        before = cell
        if prefix and cell.startswith(prefix):
            cell = cell[len(prefix) :].strip()
        if suffix and cell.endswith(suffix):
            cell = cell[: len(cell) - len(suffix)].strip()
        changed += cell != before
        cells.append(cell or None)
    if not changed:
        ends = " or ".join(
            part
            for part in (
                f"starts with {_shown_literal(prefix)}" if prefix else "",
                f"ends with {_shown_literal(suffix)}" if suffix else "",
            )
            if part
        )
        raise PrepareError("invalid_operation", f"no cell of column '{op.column}' {ends}")
    typed = _typed(pd.Series(cells, index=frame.index, dtype="str"), carried.decimal)
    result = frame.copy()
    _place(result, carried, op.column, op.name, typed)
    taken = " and ".join(
        part
        for part in (
            f"{_shown_literal(prefix)} off the start" if prefix else "",
            f"{_shown_literal(suffix)} off the end" if suffix else "",
        )
        if part
    )
    change = f"new column {op.name}: {taken} of {changed} of {_count(present, 'cell')} of {op.column}"
    change += f"; {_readings([op.name], [typed])}; {op.column} stays as it is"
    return result, _with_notice(change, typed.notice)


def _replace(frame: pd.DataFrame, op: Replace, carried: _Carried) -> tuple[pd.DataFrame, str]:
    texts = _source_texts(frame, op.column, carried, [op.old])
    _check_new_columns(frame, [op.name])
    cells: list[str | None] = []
    present = changed = 0
    for text in texts:
        if not isinstance(text, str):
            cells.append(None)
            continue
        present += 1
        if op.old not in text:
            cells.append(text)
            continue
        changed += 1
        cell = text.replace(op.old, op.new).strip()
        if len(cell) > MAX_INPUT_CELL_CHARS:
            raise PrepareError(
                "invalid_operation",
                f"a cell would be longer than the {MAX_INPUT_CELL_CHARS} characters a cell may hold",
            )
        cells.append(cell or None)
    if not changed:
        raise PrepareError("invalid_operation", f"no cell of column '{op.column}' holds {_shown_literal(op.old)}")
    typed = _typed(pd.Series(cells, index=frame.index, dtype="str"), carried.decimal)
    result = frame.copy()
    _place(result, carried, op.column, op.name, typed)
    what = f"replaced with {_shown_literal(op.new)}" if op.new else "removed"
    change = f"new column {op.name}: {_shown_literal(op.old)} {what} in {changed} of {_count(present, 'cell')} of {op.column}"
    change += f"; {_readings([op.name], [typed])}; {op.column} stays as it is"
    return result, _with_notice(change, typed.notice)


# --- Conditions ------------------------------------------------------------------------------


def _matches(series: pd.Series, condition: Condition, with_time: bool | None) -> pd.Series:
    """The rows of `series` that satisfy `condition`, as booleans; a missing cell matches only `is_missing`."""
    column, test, value = condition.column, condition.test, condition.value
    if condition.values is not None:
        if value is not None:
            raise PrepareError(
                "invalid_operation", f"the condition on column '{column}' takes value or values, not both"
            )
        if test not in ANY_OF_TESTS:
            raise PrepareError(
                "invalid_operation", f"values on column '{column}' takes the test eq or contains, not {test}"
            )
        # Any of them: each value is tested as a condition of its own, with the same reading and refusals.
        hit = pd.Series(False, index=series.index)
        for item in condition.values:
            hit |= _matches(series, condition.model_copy(update={"value": item, "values": None}), with_time)
        return hit
    if test in VALUE_FREE_TESTS:
        if value is not None:
            raise PrepareError("invalid_operation", f"the condition {test} on column '{column}' takes no value")
        return series.isna() if test == "is_missing" else series.notna()
    if value is None:
        raise PrepareError("invalid_operation", f"the condition {test} on column '{column}' needs a value")
    if not value:
        raise PrepareError(
            "invalid_operation",
            f"the condition {test} on column '{column}' needs a value; is_missing finds empty cells, not_missing "
            "the others",
        )
    if test == "contains":
        return _bools(_texts(series, with_time).str.contains(value, regex=False))
    kind = _kind(series)
    target: object
    if kind == "number" and is_integer_dtype(series.dtype):
        return _whole_matches(series, test, value, column)
    if kind == "number":
        target = _number(value, column)
    elif kind == "datetime":
        moment = _moment(value, column, series.dt.tz)
        if test in ("le", "gt") and _names_a_day(value):
            # A date without a time is the whole day: "until the 31st" keeps that day's rows whatever their time,
            # and "after the 31st" leaves all of them out. Midnight alone would cut the day's rows in two.
            moment, test = moment + pd.Timedelta(days=1), "lt" if test == "le" else "ge"
        target = moment
    elif kind == "boolean":
        if value.casefold() not in ("true", "false"):
            raise PrepareError("invalid_operation", f"the value for column '{column}' must be true or false")
        if test in ORDER_TESTS:
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
    if test == "ge":
        return _bools(series >= target)
    if test == "le":
        return _bools(series <= target)
    return _bools(series < target)


def _describe(condition: Condition, kind: Kind) -> str:
    if condition.test == "is_missing":
        return f"{condition.column} is missing"
    if condition.test == "not_missing":
        return f"{condition.column} is not missing"
    if condition.values is not None:
        # `Kategorie is 'Miete' or 'Strom'`, `Text contains 'REWE', 'EDEKA', 'LIDL' or 2 more`.
        quoted = condition.test == "contains" or kind == "text"
        clipped = [_clip(item, MAX_CELL_CHARS) for item in condition.values]
        listed = [f"'{item}'" if quoted else item for item in clipped][:SHOWN_ANY_VALUES]
        more = len(condition.values) - len(listed)
        if more:
            listed.append(f"{more} more")
        words = listed[0] if len(listed) == 1 else f"{', '.join(listed[:-1])} or {listed[-1]}"
        return f"{condition.column} {'contains' if condition.test == 'contains' else 'is'} {words}"
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
    value with a fraction is never equal to a cell, so the order tests compare with the
    whole number below or above it (`gt 2.5` and `ge 2.5` are `gt 2`, `lt 2.5` and `le 2.5`
    are `lt 3`).
    """
    _number(value, column)  # the same refusal as any number column for a value that is no number
    exact = ExactDecimal(value.strip())
    present = series.notna()
    if exact == exact.to_integral_value():
        whole = int(exact)
        if not _INT64_MIN <= whole <= _INT64_MAX:  # past every cell: equal to none, above or below all
            above = whole > _INT64_MAX
            hit = test == "ne" or (test in ("lt", "le") and above) or (test in ("gt", "ge") and not above)
            return present.astype(bool) if hit else pd.Series(False, index=series.index)
        if test == "eq":
            return _bools(series == whole)
        if test == "ne":
            return _bools(series != whole) & present
        if test == "gt":
            return _bools(series > whole)
        if test == "ge":
            return _bools(series >= whole)
        return _bools(series <= whole) if test == "le" else _bools(series < whole)
    if test == "eq":
        return pd.Series(False, index=series.index)
    if test == "ne":
        return present.astype(bool)
    floor = int(exact.to_integral_value(rounding=ROUND_FLOOR))
    return _bools(series > floor) if test in ("gt", "ge") else _bools(series < floor + 1)


def _names_a_day(value: str) -> bool:
    """Whether a condition's date value is a date alone (`2024-01-31`), with no time of day."""
    try:
        date.fromisoformat(value.strip())
    except ValueError:
        return False
    return True


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


def _to_numbers(series: pd.Series, decimal: str) -> tuple[pd.Series, str | None, int, str, int, int]:
    """The cells as numbers (`Int64` when every value is whole, else `float64`), the unit removed, the failures, the decimal used,
    the cells a float64 holds only rounded (more significant digits than it keeps, see `parse.keeps_value`), and the
    read cells whose minus was the minus sign (`parse.ascii_minus`: `−100` is -100, `10–20` no number).

    The cells are read with `decimal` first. When some fail and fewer fail with the
    other mark, the column is written that way (a `12,5 %` column in a dot-decimal
    file, `12.5 %` in a decimal-comma file) and every cell is read with the other mark:
    one decimal per column, never a mix.
    """
    if _kind(series) == "boolean":
        return series.astype("Int64"), None, 0, decimal, 0, 0
    texts: list[str | None] = []
    marked: list[bool] = []
    for text in _texts(series):
        if not isinstance(text, str):
            texts.append(None)
            marked.append(False)
            continue
        signed, found = ascii_minus([text])
        texts.append(signed[0])
        marked.append(found > 0)
    numbers, units, failed = _read_numbers(texts, decimal)
    if failed:
        other = "," if decimal == "." else "."
        alternative = _read_numbers(texts, other)
        if alternative[2] < failed:
            (numbers, units, failed), decimal = alternative, other
    if len(units) > 1:
        raise PrepareError("type_mismatch", f"column '{series.name}' mixes {len(units)} different units")
    unit = next(iter(units)) if units else None
    minus = sum(mark and number is not None for mark, number in zip(marked, numbers, strict=True))
    # Whole numbers are read exactly, never through a float64, which rounds past 2**53 (`9007199254740993`).
    exact = [None if number is None else _exact(number) for number in numbers]
    integers = [None if value is None or value != value.to_integral_value() else int(value) for value in exact]
    if all(
        number is None or (integer is not None and _INT64_MIN <= integer <= _INT64_MAX)
        for number, integer in zip(numbers, integers, strict=True)
    ):
        return pd.Series(pd.array(integers, dtype="Int64"), index=series.index), unit, failed, decimal, 0, minus
    values = [None if number is None else float(number) for number in numbers]
    rounded = sum(not keeps_value(number, float(number)) for number in numbers if number is not None)
    return pd.Series(values, index=series.index, dtype="float64"), unit, failed, decimal, rounded, minus


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
        if _is_dash(unit):
            return None, None  # taken off as a unit, the dash of `–5` would drop a sign without a word
    number = _plain_number(body, decimal)
    return number, (unit if number is not None else None)


def _is_dash(text: str) -> bool:
    return all(unicodedata.category(char) == "Pd" or char == "\N{MINUS SIGN}" for char in text)


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
        # A month name with a year (`Nov 2026`, `Okt. 2026`) is its month's first day, in the eleven languages of
        # `months.py`, as the parser reads it; pandas knows English names only (live test of 2026-11-01).
        original = texts
        texts = pd.Series([_month_iso(text) or text for text in texts], index=series.index, dtype="str")
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
        result = _without_filled_in(result, original)
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


def _without_filled_in(result: pd.Series, texts: pd.Series) -> pd.Series:
    """The inferred dates without those pandas made up by filling in what the cell lacks, which become failures.

    pandas reads a cell without a year as the year 1 (`May` as 0001-05-01, `Nov 26` as
    0001-11-26), a time alone as today (`13:00`) and `now` and `today` as the moment of the
    run: none of them is a date the user wrote (review of 2026-11-01: a column of names with
    one `May` would have read as dates, and `Nov 26` as the year 1). A cell without a digit,
    a time alone, and a year 1 not written as `0001` fail and are counted like any other.
    """
    made_up = pd.Series(
        [
            isinstance(text, str) and (not _DIGIT.search(text) or bool(_TIME_ONLY.fullmatch(text.strip())))
            for text in texts
        ],
        index=result.index,
    )
    year_one = (result.dt.year == 1).fillna(False).astype(bool)
    unwritten = pd.Series([not (isinstance(text, str) and "0001" in text) for text in texts], index=result.index)
    return result.mask(made_up | (year_one & unwritten))


_DIGIT = re.compile(r"[0-9]")
_TIME_ONLY = re.compile(r"[0-9]{1,2}:[0-9]{2}(?::[0-9]{2}(?:[.,][0-9]+)?)?\s*(?:[ap]\.?\s?m\.?)?", re.IGNORECASE)


def _month_iso(text: object) -> str | None:
    """`YYYY-MM-01` for a cell that names a month and a year (`months.month_year`) within `MONTH_YEAR_RANGE`, else None."""
    found = month_year(text) if isinstance(text, str) else None
    if found is None:
        return None
    year, month = found
    low, high = MONTH_YEAR_RANGE
    return f"{year:04d}-{month:02d}-01" if low <= year <= high else None


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
    return pd.Series(days - pd.to_timedelta(days.dt.day_of_week, unit="D"), index=series.index)


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


def _texts(series: pd.Series, with_time: bool | None = None) -> pd.Series:
    """Every cell as its canonical text (`str` dtype, missing stays missing), as `data.csv` writes it.

    `with_time` is the datetime column's carried flag; None derives it from the values
    (a column an operation made, or a mixed object column after a melt).
    """
    if with_time is None and _kind(series) == "datetime":
        with_time = _has_time(series)
    return pd.Series([_cell_text(value, bool(with_time)) for value in series], index=series.index, dtype="str")


def _has_time(series: pd.Series) -> bool:
    return bool(((series.dt.normalize() != series) & series.notna()).any())


def _with_time(series: pd.Series, carried: _Carried) -> bool | None:
    """A datetime column's carried time flag, derived from its values when none is carried; None for other kinds."""
    if _kind(series) != "datetime":
        return None
    flag = carried.with_time.get(str(series.name))
    return _has_time(series) if flag is None else flag


def _cell_text(value: object, with_time: bool) -> str | None:
    """One cell's canonical text; the missing scalars of every dtype (None, NA, NaT, NaN) are None."""
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
        # A whole number in its canonical form, as the parser writes it (`parse.number_text`); past 2**53 the `.0`
        # stays, since there a float may hold a whole number only rounded, which its form shows.
        return text[:-2] if text.endswith(".0") and abs(number) < _FLOAT_EXACT else text
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
