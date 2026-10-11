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
  single columns all hold; `sort` by one column.
* `set_type` of one column to `number`, `datetime` or `text`. To number: one unit token
  at either end (`12,5 %`, `€ 12`, `1.200 EUR`) and the thousands separators that go
  with `decimal` (the other mark, and spaces) are removed, then the cell is read as a
  dot-decimal number; the unit must be the same wherever it occurs. To datetime: with
  `date_format` the cells are read in exactly that format, with an optional time
  (`HH:MM[:SS]`) after it; without one pandas infers the format per cell, day before
  month when ambiguous, as the parser reads a slash date. Either way a cell that cannot
  be read becomes missing and the change line counts it; when more than 10 % of the
  non-missing cells fail, the operation is a `type_mismatch` instead. To text: every
  cell becomes its canonical text (the re-parse types the column by content again, so
  a column of plain numbers comes back as numbers). A column that already is a number
  or a datetime column is left as it is ("already numbers, nothing changed"), with one
  exception: `MM/DD/YYYY` on a datetime column whose days are all at most 12 swaps day
  and month, because the parser could only guess the order of such a slash column and
  read it day first (see `_reread_dates`).
* `aggregate`: group by one or two key columns and reduce one value column with `sum`,
  `mean`, `count`, `min` or `max`. A `period` turns every datetime key into `YYYY-MM`,
  `YYYY-Qn` or `YYYY` text before grouping. The result holds the key columns and one
  value column named like the source, or `count`; every other column is dropped, rows
  with a missing key form their own group, and the rows are sorted by the keys.
* `pivot_longer`: 2 to 20 columns become a `names_to`/`values_to` pair (long format,
  one row per source row and column, missing values kept). `pivot_wider`: the distinct
  values of `names_from` become new columns (at most 50, and at most 50 columns in all,
  else `too_wide`) holding `values_from`, one row per distinct index; duplicate index
  and name pairs are refused rather than aggregated.

Values in conditions are never evaluated: a condition compares text with text for a
text column, numbers for a numeric column (the value is a dot-decimal number), moments
for a datetime column (the value is an ISO date or date-time), `true`/`false` for a
boolean column. A missing cell matches only `is_missing`. `contains` searches the
cell's canonical text, case-sensitively.

Errors raise `PrepareError(code, message)`: `unknown_column`, `type_mismatch`,
`empty_result` (no rows or no columns would remain), `too_wide` and
`invalid_operation` (an operation that is well-formed but cannot apply, such as a
condition without its value or a `period` without a datetime key). Messages name
columns, never cells. Change lines name column names bare, condition values quoted
and clipped to 40 characters, and are at most `MAX_NOTE_CHARS` long.
"""

import io
import math
import re
import unicodedata
import warnings
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Literal

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_datetime64_any_dtype, is_numeric_dtype
from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from ..schemas import MAX_CELL_CHARS, MAX_COLUMNS, MAX_NOTE_CHARS, MAX_ROWS, ColumnName
from .parse import ParsedDataset, pandas_dtypes


MAX_OPERATIONS = 5  # per `prepare_data` call, the design's "at most five operations"
MAX_VALUE_CHARS = 200  # a condition value, as long as a parsed cell can be
MAX_DROP_COLUMNS = 10
MAX_CONDITIONS = 3
MAX_KEYS = 2
MAX_LONGER_COLUMNS = 20
MAX_WIDER_COLUMNS = 50
MAX_FAILED_SHARE = 0.10  # of the non-missing cells; more than this is `type_mismatch`
_INT64_MIN, _INT64_MAX = -(2**63), 2**63 - 1

Test = Literal["eq", "ne", "contains", "is_missing", "gt", "lt"]
TargetType = Literal["number", "datetime", "text"]
DateFormat = Literal["DD.MM.YYYY", "MM/DD/YYYY", "YYYY-MM-DD"]
Decimal = Literal[".", ","]
How = Literal["sum", "mean", "count", "min", "max"]
Period = Literal["month", "quarter", "year"]
Kind = Literal["number", "datetime", "boolean", "text"]
PrepareErrorCode = Literal["unknown_column", "type_mismatch", "empty_result", "too_wide", "invalid_operation"]

STRPTIME: dict[str, str] = {"DD.MM.YYYY": "%d.%m.%Y", "MM/DD/YYYY": "%m/%d/%Y", "YYYY-MM-DD": "%Y-%m-%d"}
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
# A number body for the unit split: a sign, then digits with separators, ending in a digit.
_BODY = r"[+-]?[0-9](?:[0-9.,'\s]*[0-9])?"
_TRAILING_UNIT = re.compile(rf"^(?P<body>{_BODY})\s*(?P<unit>[^0-9\s][^0-9]*)$")
_LEADING_UNIT = re.compile(rf"^(?P<unit>[^0-9\s+-][^0-9]*?)\s*(?P<body>{_BODY})$")
_SPACES = re.compile(r"\s+")
_HEADER_BREAKS = re.compile(r"[\t\r\n]")


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


# --- Operation models -----------------------------------------------------------------------


def _clean_name(name: str) -> str:
    """A new column name as the parser would keep it: no surrounding whitespace, breaks or invisible characters."""
    if name != name.strip() or _HEADER_BREAKS.search(name):
        raise ValueError("a column name has no surrounding whitespace, tabs or line breaks")
    if any(unicodedata.category(char) == "Cf" for char in name):
        raise ValueError("a column name has no invisible formatting characters")
    return name


NewName = Annotated[ColumnName, AfterValidator(_clean_name)]
Value = Annotated[str, Field(max_length=MAX_VALUE_CHARS)]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Condition(_Strict):
    """One test on one column; `value` is required for every test but `is_missing`."""

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


Operation = Annotated[
    Rename | DropColumns | DropRows | SetType | Aggregate | Sort | PivotLonger | PivotWider, Field(discriminator="op")
]


# --- Applying ---------------------------------------------------------------------------------


def apply_operations(parsed: ParsedDataset, operations: list[Operation]) -> Prepared:
    """Apply `operations` in order to the canonical CSV of `parsed`; raises `PrepareError`."""
    if not operations:
        raise PrepareError("invalid_operation", "there is no operation to apply")
    if len(operations) > MAX_OPERATIONS:
        raise PrepareError("invalid_operation", f"at most {MAX_OPERATIONS} operations can be applied at once")
    frame = _read(parsed)
    changes: list[str] = []
    for operation in operations:
        match operation:
            case Rename():
                frame, change = _rename(frame, operation)
            case DropColumns():
                frame, change = _drop_columns(frame, operation)
            case DropRows():
                frame, change = _drop_rows(frame, operation)
            case SetType():
                frame, change = _set_type(frame, operation, parsed.profile.decimal)
            case Aggregate():
                frame, change = _aggregate(frame, operation)
            case Sort():
                frame, change = _sort(frame, operation)
            case PivotLonger():
                frame, change = _pivot_longer(frame, operation)
            case PivotWider():
                frame, change = _pivot_wider(frame, operation)
        if not frame.shape[1]:
            raise PrepareError("empty_result", "no column would remain")
        if not len(frame):
            raise PrepareError("empty_result", "no row would remain")
        changes.append(_clip(change, MAX_NOTE_CHARS))
    return Prepared(csv=_write(frame), changes=changes)


def _read(parsed: ParsedDataset) -> pd.DataFrame:
    """The canonical CSV as the loader reads it; `round_trip` keeps every number's shortest form stable."""
    return pd.read_csv(
        io.StringIO(parsed.csv),
        dtype=pandas_dtypes(parsed.column_dtypes),
        parse_dates=list(parsed.parse_dates),
        float_precision="round_trip",
    )


def _write(frame: pd.DataFrame) -> str:
    """Canonical CSV text: every column written through its canonical cell texts."""
    out = pd.DataFrame({str(name): _texts(frame[name]) for name in frame.columns})
    return out.to_csv(index=False, lineterminator="\n")


def _rename(frame: pd.DataFrame, op: Rename) -> tuple[pd.DataFrame, str]:
    _require(frame, op.column)
    if op.name in frame.columns:
        raise PrepareError("invalid_operation", f"a column named '{op.name}' already exists")
    return frame.rename(columns={op.column: op.name}), f"renamed '{op.column}' to '{op.name}'"


def _drop_columns(frame: pd.DataFrame, op: DropColumns) -> tuple[pd.DataFrame, str]:
    columns = _distinct(op.columns)
    for name in columns:
        _require(frame, name)
    if len(columns) >= frame.shape[1]:
        raise PrepareError("empty_result", "dropping these columns would leave no column")
    if len(columns) == 1:
        return frame.drop(columns=columns), f"dropped column {columns[0]}"
    return frame.drop(columns=columns), f"dropped {len(columns)} columns: {', '.join(columns)}"


def _drop_rows(frame: pd.DataFrame, op: DropRows) -> tuple[pd.DataFrame, str]:
    mask = pd.Series(True, index=frame.index)
    clauses: list[str] = []
    for condition in op.where:
        _require(frame, condition.column)
        mask &= _matches(frame[condition.column], condition)
        clauses.append(_describe(condition, _kind(frame[condition.column])))
    dropped = int(mask.sum())
    if dropped == len(frame):
        raise PrepareError("empty_result", "every row matches the conditions; no row would remain")
    kept = frame[~mask].reset_index(drop=True)
    return kept, f"dropped {_count(dropped, 'row')} where {' and '.join(clauses)}"


def _set_type(frame: pd.DataFrame, op: SetType, dataset_decimal: str) -> tuple[pd.DataFrame, str]:
    _require(frame, op.column)
    series = frame[op.column]
    present = int(series.notna().sum())
    kind = _kind(series)
    result = frame.copy()
    if op.type == "text":
        result[op.column] = _texts(series)
        return result, f"{op.column}: {_count(present, 'cell')} now text"
    if op.type == "number":
        if kind == "number":
            # The canonical text of a number is a dot decimal; re-reading it under a decimal comma would be wrong.
            return frame, f"{op.column}: already numbers, nothing changed"
        converted, unit, failed = _to_numbers(series, op.decimal or dataset_decimal)
        _check_failed(op.column, failed, present, "numbers")
        result[op.column] = converted
        change = f"{op.column}: {_count(present - failed, 'cell')} read as numbers"
        if unit:
            change += f", unit '{_clip(unit, MAX_CELL_CHARS)}' removed"
    else:
        if kind == "datetime":
            return _reread_dates(frame, op, present)
        converted, failed = _to_dates(series, op.date_format)
        _check_failed(op.column, failed, present, "dates")
        result[op.column] = converted
        how = op.date_format or "format inferred, day before month"
        change = f"{op.column}: {_count(present - failed, 'cell')} read as dates ({how})"
    if failed:
        verb = "is" if failed == 1 else "are"
        change += f", {_count(failed, 'cell')} could not be read and {verb} now missing"
    return result, change


def _reread_dates(frame: pd.DataFrame, op: SetType, present: int) -> tuple[pd.DataFrame, str]:
    """A datetime column asked for a date format: nothing to read, except the one order the parser could only guess.

    The parser reads a slash column day first when every day and month part is at most
    12 (with its own ambiguity warning), and the canonical CSV no longer holds the
    original text. `MM/DD/YYYY` on such a column (every day at most 12) therefore swaps
    day and month in every cell; any other format, or a column with a day over 12, is
    left as it is.
    """
    series = frame[op.column]
    days = series.dt.day.dropna()
    if op.date_format != "MM/DD/YYYY" or not present or not bool((days <= 12).all()):
        return frame, f"{op.column}: already dates, nothing changed"
    swapped = [
        value.replace(month=value.day, day=value.month) if isinstance(value, pd.Timestamp) else None for value in series
    ]
    result = frame.copy()
    result[op.column] = pd.Series(swapped, index=series.index, dtype=series.dtype)
    return result, f"{op.column}: {_count(present, 'cell')} re-read as dates (MM/DD/YYYY, day and month swapped)"


def _aggregate(frame: pd.DataFrame, op: Aggregate) -> tuple[pd.DataFrame, str]:
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
    if op.period:
        for name in date_keys:
            work[name] = _period_labels(work[name], op.period)
    if value_kind == "boolean" and op.how in ("sum", "mean"):
        work[op.column] = work[op.column].astype("Int64")
    grouped = work.groupby(keys, dropna=False, sort=True)[op.column]
    match op.how:
        case "sum":
            aggregated = grouped.sum()
        case "mean":
            aggregated = grouped.mean()
        case "count":
            aggregated = grouped.count()
        case "min":
            aggregated = grouped.min()
        case "max":
            aggregated = grouped.max()
    result = aggregated.reset_index()
    result.columns = pd.Index([*keys, value_name])

    by = " and ".join(keys) + (f" ({op.period})" if op.period else "")
    change = f"{_VERBS[op.how]} {op.column} by {by}: {_count(len(result), 'row')}"
    other = frame.shape[1] - len(keys) - 1
    if other:
        change += f", {_count(other, 'other column')} dropped"
    return result, change


def _sort(frame: pd.DataFrame, op: Sort) -> tuple[pd.DataFrame, str]:
    _require(frame, op.column)
    try:
        ordered = frame.sort_values(op.column, ascending=not op.descending, kind="stable", na_position="last")
    except TypeError:
        raise PrepareError(
            "type_mismatch", f"column '{op.column}' mixes kinds of values and cannot be sorted"
        ) from None
    order = "descending" if op.descending else "ascending"
    return ordered.reset_index(drop=True), f"sorted by {op.column}, {order}"


def _pivot_longer(frame: pd.DataFrame, op: PivotLonger) -> tuple[pd.DataFrame, str]:
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
    melted = frame.melt(id_vars=rest, value_vars=columns, var_name=op.names_to, value_name=op.values_to)
    return melted, f"pivoted {len(columns)} columns into {op.names_to}/{op.values_to}: {_count(rows, 'row')}"


def _pivot_wider(frame: pd.DataFrame, op: PivotWider) -> tuple[pd.DataFrame, str]:
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
    names = _texts(work[op.names_from])
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
    change = f"pivoted {op.names_from} into {_count(len(distinct), 'column')} with values from {op.values_from}: "
    change += _count(len(wide), "row")
    if left_out:
        change += f", {_count(left_out, 'row')} without a {op.names_from} left out"
    other = frame.shape[1] - len(index) - 2
    if other:
        change += f", {_count(other, 'other column')} dropped"
    return wide, change


# --- Conditions ------------------------------------------------------------------------------


def _matches(series: pd.Series, condition: Condition) -> pd.Series:
    """The rows of `series` that satisfy `condition`, as booleans; a missing cell matches only `is_missing`."""
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
        return _bools(_texts(series).str.contains(value, regex=False))
    kind = _kind(series)
    target: object
    if kind == "number":
        target = _number(value, column)
    elif kind == "datetime":
        target = _moment(value, column)
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


def _moment(value: str, column: str) -> pd.Timestamp:
    try:
        moment = datetime.fromisoformat(value.strip())
    except ValueError:
        raise PrepareError(
            "invalid_operation",
            f"the value for column '{column}' is not an ISO date (YYYY-MM-DD, with an optional time)",
        ) from None
    if moment.tzinfo is not None:
        raise PrepareError("invalid_operation", f"the value for column '{column}' must be a date without a time zone")
    return pd.Timestamp(moment)


def _bools(mask: pd.Series) -> pd.Series:
    """A comparison result as plain booleans: a missing comparison (a nullable dtype's NA) is False."""
    return mask.fillna(False).astype(bool)


# --- Conversions -----------------------------------------------------------------------------


def _to_numbers(series: pd.Series, decimal: str) -> tuple[pd.Series, str | None, int]:
    """The cells as numbers (`Int64` when every value is whole, else `float64`), the unit removed, the failures."""
    if _kind(series) == "boolean":
        return series.astype("Int64"), None, 0
    values: list[float | None] = []
    units: set[str] = set()
    failed = 0
    for text in _texts(series):
        if not isinstance(text, str):
            values.append(None)
            continue
        number, unit = _read_number(text, decimal)
        if number is None:
            failed += 1
        elif unit:
            units.add(unit)
        values.append(number)
    if len(units) > 1:
        raise PrepareError("type_mismatch", f"column '{series.name}' mixes {len(units)} different units")
    unit = next(iter(units)) if units else None
    whole = all(value is None or (value.is_integer() and _INT64_MIN <= value <= _INT64_MAX) for value in values)
    if whole:
        integers = [None if value is None else int(value) for value in values]
        return pd.Series(pd.array(integers, dtype="Int64"), index=series.index), unit, failed
    return pd.Series(values, index=series.index, dtype="float64"), unit, failed


def _read_number(text: str, decimal: str) -> tuple[float | None, str | None]:
    """One cell as a finite number and the unit token taken off it; `(None, None)` when it cannot be read."""
    body, unit = text.strip(), None
    if _plain_number(body, decimal) is None:
        match = _TRAILING_UNIT.match(body) or _LEADING_UNIT.match(body)
        if match is None:
            return None, None
        body, unit = match.group("body"), match.group("unit").strip()
    number = _plain_number(body, decimal)
    return number, (unit if number is not None else None)


def _plain_number(body: str, decimal: str) -> float | None:
    """`body` without its thousands separators, read as a dot decimal; None when it is not a finite number."""
    thousands = "." if decimal == "," else ","
    cleaned = _SPACES.sub("", body).replace(thousands, "").replace("'", "")
    if decimal == ",":
        cleaned = cleaned.replace(",", ".")
    if not _NUMBER.fullmatch(cleaned):
        return None
    number = float(cleaned)
    return number if math.isfinite(number) else None


def _to_dates(series: pd.Series, date_format: str | None) -> tuple[pd.Series, int]:
    """The cells as datetimes (NaT where a cell cannot be read) and how many non-missing cells failed."""
    texts = _texts(series)
    if date_format:
        strptime = STRPTIME[date_format]
        result = pd.to_datetime(pd.Series(pd.NaT, index=series.index))
        for suffix in _TIME_SUFFIXES:
            result = result.fillna(pd.to_datetime(texts, format=strptime + suffix, errors="coerce"))
    else:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = pd.to_datetime(texts, errors="coerce", format="mixed", dayfirst=True)
    failed = int((result.isna() & texts.notna()).sum())
    return result, failed


def _check_failed(column: str, failed: int, present: int, what: str) -> None:
    if present and failed / present > MAX_FAILED_SHARE:
        raise PrepareError("type_mismatch", f"column '{column}': {failed} of {present} cells cannot be read as {what}")


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


def _texts(series: pd.Series) -> pd.Series:
    """Every cell as its canonical text (`str` dtype, missing stays missing), as `data.csv` writes it."""
    with_time = False
    if _kind(series) == "datetime":
        with_time = bool(((series.dt.normalize() != series) & series.notna()).any())
    return pd.Series([_cell_text(value, with_time) for value in series], index=series.index, dtype="str")


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
        return None if math.isnan(number) else repr(number)
    if isinstance(value, pd.Timestamp):
        return value.isoformat(timespec="seconds") if with_time else value.date().isoformat()
    return str(value)


def _require(frame: pd.DataFrame, name: str) -> None:
    if name not in frame.columns:
        raise PrepareError("unknown_column", f"there is no column '{name}'")


def _distinct(names: list[str]) -> list[str]:
    return list(dict.fromkeys(names))


def _count(number: int, noun: str) -> str:
    return f"{number} {noun}" if number == 1 else f"{number} {noun}s"


def _clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"
