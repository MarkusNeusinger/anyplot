"""Data roles whose values cannot be negative, and the binding warnings they raise. No ADK import.

Owner rule of 2026-10-12, after two feedback cases: `polar-scatter` with radius = sin(x)
(a negative radius folded the circle into a cardioid) and `bar-feature-importance`
where the defaults bound a signed `y` to `std`. A measurable property is checked in
code, not left to the reviewer: a role marked here never takes a column with a
negative value by default (`bindings.default_bindings`), and a binding of one, made by
hand or by the root, gets a warning line (`sign_line`, collected as
`BindingCheck.warnings`) that the session block shows the root and the bindings route
and the page's role list (`non_negative`) carry to the user. A warning never refuses the
binding: the user decides, for example to drop the negative rows.

Two tables decide, both by exact name:

* `NON_NEGATIVE_ROLES`: role names that are magnitudes in every spec that uses them
  (a radius, a size, a count, a standard deviation or error, a weight, a duration).
  Names that are signed in some specs stay out (`value`, `width`, `height`,
  `distance`, `error_lower`, `amplitude`, `effect_size`).
* `NON_NEGATIVE_VALUE_SPECS`: the plot types whose `value` is a part of a whole, an
  area or a flow (pie, donut, treemap, sunburst, icicle, waffle, marimekko, sankey,
  rose, the funnel's stages, packed and map bubbles), by spec id or spec-id prefix.
  Every other spec keeps a signed `value` (waterfall, diverging bars, change, SHAP).
"""

from collections.abc import Iterable
from dataclasses import replace

from ..schemas import ColumnProfile
from .roles import DataRole


NON_NEGATIVE_ROLES: frozenset[str] = frozenset(
    {
        "radius",
        "size",
        "count",
        "frequency",
        "std",
        "std_error",
        "stderr",
        "sem",
        "response_sem",
        "importance_std",
        "weight",
        "weights",
        "volume",
        "population",
        "quantity",
        "duration",
        "duration_s",
        "case_count",
        "flow_count",
        "cohort_size",
        "segment_size",
        "set_sizes",
        "flow",  # alluvial-basic, flowmap-origin-destination: a magnitude
        "risk",  # frontier-efficient: a standard deviation
        "total",  # dot-matrix-proportional: the grid size
    }
)
VALUE_ROLES: frozenset[str] = frozenset({"value"})
NON_NEGATIVE_VALUE_SPECS: frozenset[str] = frozenset({"funnel-basic", "bubble-packed", "bubble-map-geographic"})
NON_NEGATIVE_VALUE_PREFIXES: tuple[str, ...] = (
    "pie-",
    "donut-",
    "treemap-",
    "sunburst-",
    "icicle-",
    "waffle-",
    "marimekko-",
    "sankey-",
    "rose-",
)


def is_non_negative(role_name: str, spec_id: str) -> bool:
    """Whether `role_name` of spec `spec_id` needs values of at least 0."""
    name = role_name.casefold()
    if name in NON_NEGATIVE_ROLES:
        return True
    return name in VALUE_ROLES and (
        spec_id in NON_NEGATIVE_VALUE_SPECS or spec_id.startswith(NON_NEGATIVE_VALUE_PREFIXES)
    )


def mark_non_negative(roles: Iterable[DataRole], spec_id: str) -> list[DataRole]:
    """The roles with `non_negative` set by the tables above."""
    return [replace(role, non_negative=is_non_negative(role.name, spec_id)) for role in roles]


def has_negative(column: ColumnProfile) -> bool:
    """Whether a number column's smallest value is below 0 (a text or date column never is)."""
    return column.dtype in ("number", "integer") and isinstance(column.min, int | float) and column.min < 0


def sign_line(role_name: str, column: ColumnProfile) -> str:
    """The warning for a non-negative role bound to `column`, which `has_negative`."""
    low = column.min if isinstance(column.min, int | float) else 0
    return (
        f"{role_name}: column '{column.name}' has negative values (down to {low:g}); "
        "this role needs values of 0 or more"
    )
