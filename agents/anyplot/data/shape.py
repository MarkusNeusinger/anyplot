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
  choice to make). A datetime column is a key: it is kept, and every numeric column
  is pivoted.
* **The result fits:** at most `MAX_ROWS` rows, and the new names (the two role
  names) are not already a kept column's name.

The matrix rule (live test round 7 of 2026-10-16): a heatmap's `x` and `y` (string or
numeric labels) and `value`, or a grouped box's `category`, `subcategory` and `value`,
take a wide matrix such as `Stunde;Mo;Di;...;So` the same way, with one label column
kept. Every condition required:

* **The spec wants a long matrix:** its required single roles are exactly two roles
  that take labels (their kinds include categorical or text; a heatmap's also take
  numbers) and one numeric-only role, and no variadic numeric family.
* **The table is a wide matrix:** exactly one text column, the row labels, with a
  distinct label in every row and none missing, which is kept as the key; at least
  `MIN_MATRIX_COLUMNS` numeric columns (at most `MAX_LONGER_COLUMNS`); and no other
  column. Long data such as `day, hour, count` (two number columns, the day repeated)
  stays as it is.
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

from ..schemas import MAX_ROWS, DatasetProfile
from .prepare import MAX_LONGER_COLUMNS
from .roles import DataRole


_LABEL_KINDS = frozenset({"categorical", "text"})
_NUMERIC_COLUMNS = frozenset({"integer", "number"})
_LABEL_COLUMNS = frozenset({"text", "boolean"})
MIN_MATRIX_COLUMNS = 3
"""The measurement columns a wide matrix has at least (the heatmap specs ask for 5 to 50); two number columns
beside a label column are more often a long table with an integer key."""


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
    numeric = [name for name, dtype in dtypes.items() if dtype in _NUMERIC_COLUMNS]
    if not 2 <= len(numeric) <= MAX_LONGER_COLUMNS:
        return None
    labels = [role for role in single if role.required and role.kinds and set(role.kinds) <= _LABEL_KINDS]
    if len(labels) == 1 and not any(dtype in _LABEL_COLUMNS for dtype in dtypes.values()):
        keys = [name for name, dtype in dtypes.items() if dtype == "datetime"]
        names_to = labels[0].name
    else:
        # The matrix rule: two label roles, one of them for the kept label column.
        pair = [role for role in single if role.required and takes_labels(role)]
        required = [role for role in single if role.required]
        texts = [column for column in profile.columns if column.dtype == "text"]
        if len(pair) != 2 or len(required) != 3 or len(texts) != 1 or "boolean" in dtypes.values():
            return None
        # A matrix: one distinct label per row and at least `MIN_MATRIX_COLUMNS` measures. Long data of
        # `day, hour, count` (an integer key, the label repeated per hour) stays as it is.
        if len(numeric) < MIN_MATRIX_COLUMNS or texts[0].missing or texts[0].unique != profile.rows:
            return None
        keys = [texts[0].name]
        names_to = pair[1].name
    if len(numeric) + len(keys) != len(dtypes):
        return None
    values_to = values[0].name
    if names_to == values_to or {names_to, values_to} & set(keys):
        return None
    rows = profile.rows * len(numeric)
    if rows > MAX_ROWS:
        return None
    return LongSuggestion(numeric, names_to, values_to, keys, rows)
