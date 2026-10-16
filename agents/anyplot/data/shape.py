"""The wide-table suggestion: a deterministic `pivot_longer` offered when the spec wants long data.

A box, violin, strip or bar spec wants one category column and one value column
(`category` (string), `value` (numeric)); a pasted table such as
`Sensor_A,Sensor_B,Sensor_C` holds the same quantity side by side instead, so the
default bindings leave the category open and bind only the first column.
`long_suggestion` recognises that shape from the spec's roles and the dataset
profile alone, and returns the one operation that makes the table long:
`pivot_longer` of the measurement columns, the column names into the category role's
name, the values into the value role's name. The page offers it as `.to_long()`
(applied by `POST /v1/sessions/{sid}/dataset/to_long`, no model call), and the root's
summary mentions it. No ADK import.

The rule, every condition required:

* **The spec wants long data:** it has exactly one required single (not variadic)
  role whose kinds are categorical or text only, and exactly one required single role
  whose kinds are numeric only (a spec with two required labels, such as box-grouped's
  `category` and `subcategory`, would keep one of them open). A spec with a variadic numeric family (`y1, y2, ...`, which
  takes wide data as it is) or with two required numeric roles (a scatter's `x` and
  `y`) never gets the suggestion.
* **The table is wide:** at least two numeric columns (`integer` or `number`), at
  most `MAX_LONGER_COLUMNS`, and no text or boolean column, which could already be
  the category (a table with a label column is long, or its labels are the user's
  choice to make). A datetime column is a key: it is kept, and so is a column of
  years or of a part of a date (`temporal.time_keys`: `Jahr` beside `CO2` and
  `Bevölkerung`), and so is a first column that numbers the rows (`_numbering_key`:
  `id`, `Nr`, `Stunde` 0 to 3); every other numeric column is pivoted.
* **The result fits:** at most `MAX_ROWS` rows, and the new names (the two role
  names) are not already a kept column's name.

The matrix rule (live test round 7 of 2026-10-16): a heatmap's `x` and `y` (string or
numeric labels) and `value`, or a grouped box's `category`, `subcategory` and `value`,
take a wide matrix such as `Stunde;Mo;Di;...;So` the same way, with one label column
kept. Every condition required:

* **The spec wants a long matrix:** its required single roles are exactly two roles
  that take labels (their kinds include categorical or text; a heatmap's also take
  numbers), both of a grid or grouped chart (`MATRIX_ROLES`: never a flow's `source`
  and `target`, a hierarchy or a party's color), and one numeric-only role, and no
  variadic numeric family.
* **The table is a wide matrix:** one row-label column (`_row_key`: the one text
  column, else the one date column, else a first column of whole numbers that is a
  year or every hour of a range, `Stunde` 0 to 23), with a distinct label in every
  row and none missing, which is kept as the key; at least `MIN_MATRIX_COLUMNS` other
  numeric columns (at most `MAX_LONGER_COLUMNS`); and no other column. Long data such
  as `day, hour, count` (two number columns, the day repeated) stays as it is.
* **The result fits:** as above. The column names go into the second label role in
  spec order (`y`, `subcategory`), the values into the value role; the default
  bindings give the kept label column to the first (`x`, `category`), as they do for
  the wide table already.

Before this rule the default bindings put a heatmap's `y` on the numbers of `Mo` and
its `value` on `Di`, and the plot drew 14 rows of nonsense; `bindings.label_siblings`
now keeps a label role off the measurement columns of a table this module calls wide.
"""

from dataclasses import dataclass
from typing import Any

from ..schemas import MAX_ROWS, ColumnProfile, DatasetProfile
from .parse import ID_WORDS
from .prepare import MAX_LONGER_COLUMNS
from .roles import DataRole
from .temporal import WORDS, time_keys


_LABEL_KINDS = frozenset({"categorical", "text"})
_NUMERIC_COLUMNS = frozenset({"integer", "number"})
_LABEL_COLUMNS = frozenset({"text", "boolean"})
MIN_MATRIX_COLUMNS = 3
"""The measurement columns a wide matrix has at least (the heatmap specs ask for 5 to 50); two number columns
beside a label column are more often a long table with an integer key."""
MATRIX_ROLES: frozenset[str] = frozenset(
    {
        *("x", "y", "x_category", "y_category", "fill_category", "row_labels", "column_labels"),
        *("category", "subcategory", "group", "component", "series", "split_group"),
        *("angular", "radial", "entity", "period", "season", "cycle"),
    }
)
"""Label roles whose pair makes a grid or a grouped chart, where melting a wide matrix is meaningful (review of
#12204). A pair of other roles is a flow (`source`, `target`), a hierarchy (`name`, `parent`, `level_1`), a
geometry, a color or a code (`party`, `color`, `newick_string`): their wide tables are no matrix of one measure."""


@dataclass(frozen=True)
class LongSuggestion:
    """The `pivot_longer` that makes a wide table long for the spec's category and value roles."""

    columns: list[str]
    names_to: str
    values_to: str
    keys: list[str]
    rows: int

    def operation(self) -> dict[str, Any]:
        """The `prepare_data` operation, as `prepare.Operation` validates it."""
        return {
            "op": "pivot_longer",
            "columns": list(self.columns),
            "names_to": self.names_to,
            "values_to": self.values_to,
        }

    def body(self) -> dict[str, Any]:
        """The `suggestion` field of a dataset answer: what the page names and what `.to_long()` applies."""
        return {
            "kind": "to_long",
            "columns": list(self.columns),
            "names_to": self.names_to,
            "values_to": self.values_to,
            "keys": list(self.keys),
            "rows": self.rows,
        }


def takes_labels(role: DataRole) -> bool:
    """Whether a role labels or splits the marks: its kinds include categorical or text (a heatmap's `x` and `y`,
    which also take numbers, included)."""
    return bool(set(role.kinds) & _LABEL_KINDS)


def long_suggestion(roles: list[DataRole], profile: DatasetProfile) -> LongSuggestion | None:
    """The suggestion for this spec and table, or None when neither rule above holds."""
    single = [role for role in roles if not role.variadic and not role.computed]  # a computed role takes no column
    if any(role.variadic and set(role.kinds) == {"numeric"} for role in roles):
        return None
    values = [role for role in single if role.required and set(role.kinds) == {"numeric"}]
    if len(values) != 1:
        return None
    dtypes = {column.name: column.dtype for column in profile.columns}
    time = time_keys(profile)  # years and parts of a date say where a value sits: keys, never melted
    labels = [role for role in single if role.required and role.kinds and set(role.kinds) <= _LABEL_KINDS]
    if len(labels) == 1 and not any(dtype in _LABEL_COLUMNS for dtype in dtypes.values()):
        # A first column that numbers the rows (`id`, `Nr`, `Stunde` 0 to 3) is a key too, never a measure
        # (review of #12204: melted, it kept `category` off every column of `id,a,b,c`).
        numbering = _numbering_key(profile)
        keys = [name for name, dtype in dtypes.items() if dtype == "datetime" or name in time or name == numbering]
        names_to, least = labels[0].name, 2
    else:
        # The matrix rule: two label roles of a grid or grouped chart, one of them for the kept row labels.
        pair = [role for role in single if role.required and takes_labels(role)]
        required = [role for role in single if role.required]
        if len(pair) != 2 or len(required) != 3 or any(role.name not in MATRIX_ROLES for role in pair):
            return None
        key = _row_key(profile, time)
        # Another year or date-part column besides the row labels is a second key, no measurement to melt.
        if key is None or "boolean" in dtypes.values() or time - {key}:
            return None
        keys = [key]
        names_to, least = pair[1].name, MIN_MATRIX_COLUMNS
    measures = [name for name, dtype in dtypes.items() if dtype in _NUMERIC_COLUMNS and name not in keys]
    if not least <= len(measures) <= MAX_LONGER_COLUMNS or len(measures) + len(keys) != len(dtypes):
        return None
    values_to = values[0].name
    if names_to == values_to or {names_to, values_to} & set(keys):
        return None
    rows = profile.rows * len(measures)
    if rows > MAX_ROWS:
        return None
    return LongSuggestion(measures, names_to, values_to, keys, rows)


def _row_key(profile: DatasetProfile, time: set[str]) -> str | None:
    """The row labels of a wide matrix, or None: the one text column, else the one date column, else a first
    column of whole numbers that is a time key or every number of its range (`Stunde` 0 to 23). Each with a
    distinct value in every row and none missing: long data such as `day, hour, count` repeats its labels."""
    columns = profile.columns
    texts = [column for column in columns if column.dtype == "text"]
    dates = [column for column in columns if column.dtype == "datetime"]
    if texts:
        key = texts[0] if len(texts) == 1 and not dates else None
    elif dates:
        key = dates[0] if len(dates) == 1 else None
    else:
        first = columns[0] if columns else None
        key = first if first is not None and first.dtype == "integer" and (first.name in time or _run(first)) else None
    if key is None or key.missing or key.unique != profile.rows:
        return None
    return key.name


def _numbering_key(profile: DatasetProfile) -> str | None:
    """The first column when it numbers the rows: whole numbers, one per row, none missing, and every number of
    its range (`1` to `n`, `100` to `109`, an hour `0` to `3`) or a name that says ids (`id`, `Nr`, `Code`)."""
    first = profile.columns[0] if profile.columns else None
    if first is None or first.dtype != "integer" or first.missing or first.unique != profile.rows:
        return None
    named = bool(set(WORDS.findall(first.name.casefold())) & ID_WORDS)
    return first.name if named or _run(first) else None


def _run(column: ColumnProfile) -> bool:
    """Whole numbers that hold every number of their range, at least three (`0` to `23`): steps, not measures."""
    if not isinstance(column.min, float | int) or not isinstance(column.max, float | int):
        return False
    return 3 <= column.unique == int(column.max - column.min) + 1
