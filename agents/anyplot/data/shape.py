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
"""

from dataclasses import dataclass
from typing import Any

from ..schemas import MAX_ROWS, DatasetProfile
from .prepare import MAX_LONGER_COLUMNS
from .roles import DataRole


_LABEL_KINDS = frozenset({"categorical", "text"})
_NUMERIC_COLUMNS = frozenset({"integer", "number"})
_LABEL_COLUMNS = frozenset({"text", "boolean"})


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


def long_suggestion(roles: list[DataRole], profile: DatasetProfile) -> LongSuggestion | None:
    """The suggestion for this spec and table, or None when the rule above does not hold."""
    single = [role for role in roles if not role.variadic]
    if any(role.variadic and set(role.kinds) == {"numeric"} for role in roles):
        return None
    labels = [role for role in single if role.required and role.kinds and set(role.kinds) <= _LABEL_KINDS]
    values = [role for role in single if role.required and set(role.kinds) == {"numeric"}]
    # Exactly one of each: box-grouped's `category` and `subcategory` would leave one label open.
    if len(labels) != 1 or len(values) != 1:
        return None
    dtypes = {column.name: column.dtype for column in profile.columns}
    if any(dtype in _LABEL_COLUMNS for dtype in dtypes.values()):
        return None
    numeric = [name for name, dtype in dtypes.items() if dtype in _NUMERIC_COLUMNS]
    keys = [name for name, dtype in dtypes.items() if dtype == "datetime"]
    if not 2 <= len(numeric) <= MAX_LONGER_COLUMNS or len(numeric) + len(keys) != len(dtypes):
        return None
    names_to, values_to = labels[0].name, values[0].name
    if names_to == values_to or {names_to, values_to} & set(keys):
        return None
    rows = profile.rows * len(numeric)
    if rows > MAX_ROWS:
        return None
    return LongSuggestion(numeric, names_to, values_to, keys, rows)
