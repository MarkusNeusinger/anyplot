"""What the plot draws of the rows: a key that repeats, and rows without a value to draw. No ADK import.

Owner decision of 2026-11-08 (the decision memo on `adapter.md:36`): the plot draws every row of the data it gets,
and a change of the rows goes only through the data step, where `prepare_data` counts it, the data card shows it and
`.undo()` takes it back. In the persona round of 2026-11-06 two plots changed the rows in their code while the
confirmed data still held every one: a line chart of 27 measurements over 9 lengths averaged them to 9 points, and a
weekly series lost a week. Two facts of the data make such changes visible, for all 15 libraries alike, because they
come from the profile, never from the plot code:

* A key that repeats (`repeated_key`). A spec in `KEY_ROLES` draws one value per key: one bar, slice or stage per
  category, one cell per pair, one point per x or date of each series. When the bound key columns hold fewer keys
  than the rows that need a mark, rows share a key, and the plot either draws them on top of each other, as a
  zigzag, or groups them in its code without a count. The binding check of complete bindings (a mark is drawn
  only then) then warns with the counts
  (`RepeatedKey.line`: `x: column 'Length' holds 9 values in 27 rows; ...`), the session block names the key and the
  counts (`RepeatedKey.fact`), and the root offers the counted `aggregate` of `prepare_data` (root.md, "Step 1: the
  data"). It is a fact of the rows, not of the binding: it never refuses a binding, and `bindings.carry_by_name`
  carries a binding over it (`BindingCheck.fit_warnings`).
* Rows without a value to draw (`left_out_line`). A row whose bound column for a mark is empty has nothing to draw
  there: the adapter leaves it out for that mark (`adapter.md`: "Drop rows with missing values only for the columns
  a mark needs"; the JavaScript and Julia slots filter them in code). The pipeline puts one server line with the
  counts into the shipped version's "what changed", right after the loader's notes (`pipeline.finish`).

The rule for a key, decided with this module:

* Which specs. `KEY_ROLES` lists each spec whose plot type draws one value per key, with the roles whose values
  together name a mark (`bar-grouped`: the category and the group). A role it lists is marked `DataRole.key`
  (`mark_keys`). The table is explicit, as `signs.py` and `computed.py` are: a spec where repeats are the point
  (scatter, box, violin, strip, swarm, histogram, density, a count of rows) is never listed, and neither is a line
  that may turn back on itself (a parametric curve, a phase portrait, stress and strain) or whose x may repeat by
  design (a win probability per game minute, several plays a minute). A new spec stays unkeyed until it is listed:
  a missing warning is the safe side, a false one would send the user to an aggregate the plot does not need.
* Which columns. The key is the bound key roles, plus every other bound role that takes labels or dates (a series,
  a group, a colour, a role without kinds), since such a role may split the marks into series; a computed role is
  never part of it, and a column on several roles counts once. The rest of the bound roles are the measures.
* Which count. The profile knows each column's distinct values and empty cells, not their combinations, so the check
  fires only when a repeat of drawn marks is certain: the keys the columns can make are at most the product of
  their distinct values (a splitting column's empty cells one more group), and the rows that draw a mark are at
  least the rows minus the empty cells of the key columns and of every required single measure (a candle needs all
  four prices), minus those of the fullest member of a required family (one series of a wide table needs only its
  own column). An optional measure and a value written in one row only count for nothing. More such rows than
  keys means that marks share one. A key that repeats only inside one series of a split stays unwarned: the
  profile cannot tell it.

The rule for rows without a value, decided with this module: a bound role counts when it is required (a family
member counts by its family), not computed, and a key or a role that takes numbers or dates, the roles that place a
mark; a role that takes text only labels one (a name, an annotation) and leaves no row out, and an optional one
(a third level of a sunburst, an error bar) may stay empty by design. Not counted: a spec whose
data is no table of observations (`spec_roles.spec_shape`: a matrix, a network, generated parameters); a role
`SEPARATE_ROLES` lists, whose column holds a shorter list or one value beside the rows by the spec's own words (the
event dates of an annotated line, a patient's measurements beside the reference curves, a base value); and a column
filled in at most one row, which is such a single value whatever the spec. The counts are the profile's empty cells
per column, each exact; no total is claimed, since one row may miss two values.

The rule for a repeated key that reaches a plot run, owner decision of 2026-11-09 (`key_aggregate`): the adapter,
asked by its prompt to draw every row, still averaged such rows per key in its code (2 of 2 measured runs), so the
server combines them first, as a data step of its own (`repeated_keys.combine_repeated_key`): the `aggregate` that
`prepare_data` makes, by the key's columns (`RepeatedKey.columns`, at most `prepare.MAX_KEYS`) of every other bound
column, stored as the next data version, announced with its counts (`combined_line`) and undone with `.undo()`.

* Which function. A keyed spec draws a measurement per key (a bar's height, a line's value, a cell's colour, a
  price): `mean`. A spec in `SUM_SPECS` draws parts of a whole or counts that add up (a slice, a stacked segment, a
  tile, a funnel stage, a Pareto count, a waterfall change): `sum`. A role bound to a column of counts is summed
  with the rest; `count` never fits, since it counts rows and drops the bound column.
* When the server combines nothing. A spec in `UNREDUCED_SPECS`, whose measures need several functions (a candle's
  first, highest, lowest and last price; a zone's minutes beside its bounds; a value beside its goal; an estimate
  beside its interval, whose averaged bounds bound nothing); a spec with a
  bound `SEPARATE_ROLES` role, whose list lies beside the rows; a key of more than `prepare.MAX_KEYS` columns; and a
  bound column besides the key that holds no numbers. The binding warning stands then, and the root offers the step.
"""

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, replace
from typing import Literal

from core.spec_roles import DataRole, spec_shape

from ..schemas import MAX_CHANGE_CHARS, ColumnProfile
from .prepare import MAX_AGGREGATE_COLUMNS, MAX_KEYS


KEY_ROLES: dict[str, frozenset[str]] = {
    # One bar, slice, stage, spoke or interval per category (per group, component or series where the spec has one).
    "bar-3d-categorical": frozenset({"x_category", "y_category"}),
    "bar-basic": frozenset({"category"}),
    "bar-diverging": frozenset({"category"}),
    "bar-diverging-likert": frozenset({"question"}),
    "bar-error": frozenset({"category"}),
    "bar-feature-importance": frozenset({"feature"}),
    "bar-grouped": frozenset({"category", "group"}),
    "bar-heart-rate-zones": frozenset({"zone"}),
    "bar-horizontal": frozenset({"category"}),
    "bar-pareto": frozenset({"category"}),
    "bar-permutation-importance": frozenset({"feature"}),
    "bar-spine": frozenset({"x_category", "fill_category"}),
    "bar-stacked": frozenset({"category", "component"}),
    "bar-stacked-labeled": frozenset({"category", "component"}),
    "bar-stacked-percent": frozenset({"category", "component"}),
    "bar-tornado-sensitivity": frozenset({"parameter"}),
    "coefficient-confidence": frozenset({"variable"}),
    "donut-basic": frozenset({"category"}),
    "donut-nested": frozenset({"level_1", "level_2"}),
    "dot-matrix-proportional": frozenset({"category"}),
    "dumbbell-basic": frozenset({"category"}),
    "funnel-basic": frozenset({"stage"}),
    "gauge-activity-rings": frozenset({"metric"}),
    "lollipop-basic": frozenset({"category"}),
    "lollipop-grouped": frozenset({"category", "series"}),
    "marimekko-basic": frozenset({"x_category", "y_category"}),
    "pictogram-basic": frozenset({"category"}),
    "pie-basic": frozenset({"category"}),
    "point-basic": frozenset({"category"}),
    "polar-bar": frozenset({"direction"}),
    "pyramid-basic": frozenset({"category"}),
    "radar-basic": frozenset({"category"}),
    "radar-multi": frozenset({"category", "series"}),
    "range-interval": frozenset({"category"}),
    "rose-basic": frozenset({"category"}),
    "shap-waterfall": frozenset({"feature"}),
    "slope-basic": frozenset({"entity"}),
    "sunburst-basic": frozenset({"level_1", "level_2", "level_3"}),
    "treemap-basic": frozenset({"category", "subcategory"}),
    "waffle-basic": frozenset({"category"}),
    "waterfall-basic": frozenset({"category"}),
    # One cell per pair.
    "heatmap-annotated": frozenset({"x", "y"}),
    "heatmap-basic": frozenset({"x", "y"}),
    "heatmap-calendar": frozenset({"date"}),
    "heatmap-chromagram": frozenset({"time", "pitch_class"}),
    "heatmap-cohort-retention": frozenset({"cohort", "period"}),
    "heatmap-polar": frozenset({"angular", "radial"}),
    "heatmap-stripes-climate": frozenset({"year"}),
    # One point per x or date of each series: lines, areas, steps, stems and price charts.
    "area-basic": frozenset({"x"}),
    "area-cumulative-flow": frozenset({"date", "stage"}),
    "area-stacked": frozenset({"x", "category"}),
    "area-stacked-confidence": frozenset({"x", "category"}),
    "area-stacked-percent": frozenset({"time", "category"}),
    "bump-basic": frozenset({"entity", "period"}),
    "burndown-sprint": frozenset({"day"}),
    "candlestick-basic": frozenset({"date"}),
    "candlestick-volume": frozenset({"date"}),
    "drawdown-basic": frozenset({"date"}),
    "elbow-curve": frozenset({"k_values"}),
    "horizon-basic": frozenset({"date", "series"}),
    "indicator-bollinger": frozenset({"date"}),
    "indicator-ema": frozenset({"date"}),
    "indicator-ichimoku": frozenset({"date"}),
    "indicator-macd": frozenset({"date"}),
    "indicator-rsi": frozenset({"date"}),
    "indicator-sma": frozenset({"date"}),
    "kagi-basic": frozenset({"date"}),
    "line-basic": frozenset({"x"}),
    "line-confidence": frozenset({"x"}),
    "line-cycle-seasonal": frozenset({"season", "cycle"}),
    "line-filled": frozenset({"x"}),
    "line-loss-training": frozenset({"epoch"}),
    "line-markers": frozenset({"x"}),
    "line-multi": frozenset({"x"}),
    "line-pca-variance-cumulative": frozenset({"n_components"}),
    "line-retention-cohort": frozenset({"time_period", "cohort"}),
    "line-stepwise": frozenset({"x"}),
    "line-stock-comparison": frozenset({"date", "symbol"}),
    "line-styled": frozenset({"x"}),
    "line-timeseries": frozenset({"date"}),
    "line-timeseries-rolling": frozenset({"date"}),
    "line-training-load-pmc": frozenset({"date"}),
    "ohlc-bar": frozenset({"date"}),
    "point-and-figure-basic": frozenset({"date"}),
    "renko-basic": frozenset({"date"}),
    "stem-basic": frozenset({"x"}),
    "step-basic": frozenset({"x"}),
    "streamgraph-basic": frozenset({"time", "category"}),
    "timeseries-decomposition": frozenset({"date"}),
    "timeseries-forecast-uncertainty": frozenset({"date"}),
}
"""Per spec, the roles whose values together name one mark of a plot that draws one value per key (the module
docstring has the rule). `tests/unit/agents/data/test_fidelity.py` checks that each listed role is a single role of
its spec that the plot does not compute, and that no spec whose repeats are the point is listed."""

SEPARATE_ROLES: dict[str, frozenset[str]] = {
    "bar-tornado-sensitivity": frozenset({"base_value"}),
    "campbell-basic": frozenset({"engine_order", "critical_speeds"}),
    "histogram-capability": frozenset({"lsl", "usl", "target"}),
    "lightcurve-transit": frozenset({"period"}),
    "line-annotated-events": frozenset({"event_date"}),
    "line-growth-percentile": frozenset({"patient_age", "patient_value"}),
    "phase-diagram-pt": frozenset({"triple_point", "critical_point"}),
    "recurrence-basic": frozenset({"threshold"}),
    "scatter-constellation-diagram": frozenset({"ideal_i", "ideal_q"}),
    "shap-waterfall": frozenset({"base_value"}),
    "spectrogram-basic": frozenset({"sample_rate"}),
    "spectrogram-mel": frozenset({"sample_rate", "n_mels"}),
    "stock-event-flags": frozenset({"event_date"}),
    "timeseries-forecast-uncertainty": frozenset(
        {"actual", "forecast", "lower_80", "upper_80", "lower_95", "upper_95"}
    ),
}
"""Per spec, the required number or date roles whose column holds a shorter list or a single value beside the rows,
by the spec's own words ("3-10 event markers" beside 50-500 points, "a single constant value", 30-150 historical
points beside 10-50 forecast ones): their empty cells are the layout, never rows left out (`left_out_line`)."""

SPLIT_KINDS: frozenset[str] = frozenset({"categorical", "text", "boolean", "datetime"})
"""The kinds of a bound role that may split the marks into series, groups or colours: part of a key (`repeated_key`)."""
MARK_KINDS: frozenset[str] = frozenset({"numeric", "datetime"})
"""The kinds of a required role whose empty cell leaves a row without its mark (`left_out_line`)."""
LEFT_OUT_HEAD = "The plot draws no mark where a value is missing: "
"""The server's line in "what changed" for rows without a value to draw, before its counts per role."""
COMBINED_HEAD = "Rows that share a key were combined in data version "
"""The server's line in "what changed" for a repeated key it combined before the run, before the version's number."""
COMBINED_IN_VIEW_HEAD = "Rows of the view that share a key were combined for the plot only"
"""The same for a key that repeats among the rows a view of the plot shows (`combined_in_view_line`): combined for
the run alone, with no data version."""

SUM_SPECS: frozenset[str] = frozenset(
    {
        # Parts of a whole: the slices, rings, tiles and stacked segments of rows that share a key add up.
        "pie-basic",
        "donut-basic",
        "donut-nested",
        "treemap-basic",
        "sunburst-basic",
        "marimekko-basic",
        "bar-stacked",
        "bar-stacked-labeled",
        "bar-stacked-percent",
        "area-stacked",
        "area-stacked-percent",
        "streamgraph-basic",
        # Counts and amounts per key, and changes that add up to a total.
        "bar-pareto",
        "bar-spine",
        "funnel-basic",
        "pictogram-basic",
        "waterfall-basic",
    }
)
"""The keyed specs whose rows that share a key add up to one mark (`key_aggregate`: `sum`); every other one draws a
measurement per key, and its rows are averaged (`mean`)."""

UNREDUCED_SPECS: frozenset[str] = frozenset(
    {
        # Prices: a period's first, highest, lowest and last price take four functions, and the volume a fifth.
        "candlestick-basic",
        "candlestick-volume",
        "ohlc-bar",
        "indicator-ichimoku",
        "point-and-figure-basic",
        # A measure beside a bound, a goal, a total or a scope change of another kind.
        "bar-heart-rate-zones",
        "dot-matrix-proportional",
        "gauge-activity-rings",
        "burndown-sprint",
        # An estimate beside its interval or its spread: the mean of the bounds is no bound of the mean.
        "area-stacked-confidence",
        "bar-error",
        "bar-feature-importance",
        "bar-permutation-importance",
        "coefficient-confidence",
        "line-confidence",
        "point-basic",
        "range-interval",
    }
)
"""The keyed specs whose measures no single function combines: the server leaves their repeated key to the user's
data step (`key_aggregate` returns None), and the binding warning stands."""

How = Literal["mean", "sum"]


@dataclass(frozen=True)
class KeyAggregate:
    """The `aggregate` operation the server makes for a repeated key: its key columns (`by`), value columns and
    function, and the operation as `prepare_data` takes it (`operation`)."""

    by: tuple[str, ...]
    values: tuple[str, ...]
    how: How

    @property
    def operation(self) -> dict[str, object]:
        """The operation in `prepare.Aggregate`'s form: `column` for one value column, `columns` for several."""
        values: dict[str, object] = (
            {"column": self.values[0]} if len(self.values) == 1 else {"columns": list(self.values)}
        )
        return {"op": "aggregate", "by": list(self.by), **values, "how": self.how}


Held = tuple[str, DataRole, ColumnProfile]
"""A valid binding: its binding name (`y1` for a family member), its role and its column's profile."""


def mark_keys(roles: Iterable[DataRole], spec_id: str) -> list[DataRole]:
    """The roles with `key` set for the ones `KEY_ROLES` lists for `spec_id`."""
    listed = KEY_ROLES.get(spec_id, frozenset())
    return [replace(role, key=role.name in listed) for role in roles]


@dataclass(frozen=True)
class RepeatedKey:
    """A key of the marks that the rows repeat: the bound key and splitting roles, their columns and the counts.

    `roles` are binding names, the spec's first key role first; `columns` their columns in the same order;
    `values` the distinct values of the first column; `combinations` the most keys all the columns can make
    (`values` for one column); `rows` the table's rows.
    """

    roles: tuple[str, ...]
    columns: tuple[str, ...]
    values: int
    combinations: int
    rows: int

    def per(self) -> str:
        """What the plot draws one value per: `x`, `x and series`, `x, y and series`."""
        if len(self.roles) == 1:
            return self.roles[0]
        return f"{', '.join(self.roles[:-1])} and {self.roles[-1]}"

    def line(self) -> str:
        """The binding warning, which names the columns (user text, fenced wherever it goes)."""
        noun = "value" if self.values == 1 else "values"
        text = f"{self.roles[0]}: column '{self.columns[0]}' holds {self.values:,} {noun} in {self.rows:,} rows"
        if len(self.roles) > 1:
            others = ", ".join(
                f"{role} ('{column}')" for role, column in zip(self.roles[1:], self.columns[1:], strict=True)
            )
            text += f", at most {self.combinations:,} combinations with {others}"
        per = self.per()
        return f"{text}; the plot draws one value per {per}, so rows with the same {per} need an aggregate first"

    def fact(self) -> str:
        """The key and its counts for the session block: role names and numbers only, never a column name."""
        if len(self.roles) == 1:
            noun = "value" if self.values == 1 else "values"
            return f"{self.roles[0]} has {self.values:,} {noun} in {self.rows:,} rows"
        return f"{self.per()} have at most {self.combinations:,} combinations in {self.rows:,} rows"


def repeated_key(held: Sequence[Held], rows: int) -> RepeatedKey | None:
    """The key the rows certainly repeat, or None: the module docstring has the rule.

    `held` are the valid bindings in spec order (`bindings.check_bindings`), `rows` the table's rows. None as well
    when no key role is bound.
    """
    keys: list[tuple[str, ColumnProfile]] = []
    splits: list[tuple[str, ColumnProfile]] = []
    singles: dict[str, ColumnProfile] = {}  # the required single measures, which one mark may need together
    members: dict[str, ColumnProfile] = {}  # the members of required families, each a series of its own
    seen: set[str] = set()
    for name, role, column in held:
        if role.computed:
            continue
        if role.key and not role.variadic:
            target = keys
        elif not role.kinds or set(role.kinds) & SPLIT_KINDS:
            target = splits
        else:
            # An optional measure (an error bar) never decides whether a mark is drawn, and neither does a value
            # written in one row only (a base value, a limit).
            if role.required and rows - column.missing > 1:
                (members if role.variadic else singles)[column.name] = column
            continue
        if column.name not in seen:
            target.append((name, column))
        seen.add(column.name)
    if not keys:
        return None
    keyed = rows - sum(column.missing for _, column in keys)
    # Rows with a key, every required single measure and the fullest family member: at least this many, whatever
    # rows the empty cells fall on (a candle needs all four prices, one series of a wide table only its own column).
    without = sum(column.missing for name, column in singles.items() if name not in seen)
    drawn = keyed - without - min((column.missing for name, column in members.items() if name not in seen), default=0)
    combinations = math.prod(column.unique for _, column in keys) * math.prod(
        column.unique + (1 if column.missing else 0) for _, column in splits
    )
    if drawn <= combinations:
        return None
    named = [*keys, *splits]
    return RepeatedKey(
        roles=tuple(name for name, _ in named),
        columns=tuple(column.name for _, column in named),
        values=keys[0][1].unique,
        combinations=combinations,
        rows=rows,
    )


def left_out_counts(held: Sequence[Held], spec_id: str, roles: Sequence[DataRole], rows: int) -> list[Held]:
    """The valid bindings whose empty cells leave rows without a mark, in spec order (a family's members in their
    binding order), each column once (the module docstring has the rule); the count is each column's `missing`."""
    if spec_shape(spec_id, roles) != "table":
        return []
    separate = SEPARATE_ROLES.get(spec_id, frozenset())
    order = {role.name: position for position, role in enumerate(roles)}
    counted: list[Held] = []
    seen: set[str] = set()
    for name, role, column in sorted(held, key=lambda item: order.get(item[1].name, len(order))):
        places = role.required and (role.key or bool(set(role.kinds) & MARK_KINDS))
        if (
            not places
            or role.computed
            or role.name in separate
            or column.name in seen
            or not column.missing
            or rows - column.missing <= 1
        ):
            continue
        counted.append((name, role, column))
        seen.add(column.name)
    return counted


def left_out_line(held: Sequence[Held], spec_id: str, roles: Sequence[DataRole], rows: int) -> str | None:
    """The server's change line for rows without a value to draw, with the count per role, or None.

    `The plot draws no mark where a value is missing: 1 row without x ('Datum'), 3 without y ('Umsatz')`, the roles
    in spec order: as many as fit a change note (`MAX_CHANGE_CHARS`), the rest counted as `and N more roles`. The
    first always fits: a role name has at most 32 characters (`spec_roles.MAX_ROLE_NAME_CHARS`), a column name at
    most 64 (`schemas.MAX_COLUMN_NAME_CHARS`) and a count at most six digits with its comma.
    """
    counted = left_out_counts(held, spec_id, roles, rows)
    if not counted:
        return None
    items = [
        f"{column.missing:,} {_rows(column.missing) if index == 0 else 'without'} {name} ('{column.name}')"
        for index, (name, _, column) in enumerate(counted)
    ]
    for shown in range(len(items), 1, -1):
        more = len(items) - shown
        rest = f", and {more} more role{'s' if more != 1 else ''}" if more else ""
        line = LEFT_OUT_HEAD + ", ".join(items[:shown]) + rest
        if len(line) <= MAX_CHANGE_CHARS:
            return line
    more = len(items) - 1
    rest = f", and {more} more role{'s' if more != 1 else ''}" if more else ""
    return (LEFT_OUT_HEAD + items[0] + rest)[:MAX_CHANGE_CHARS]


def _rows(count: int) -> str:
    return "row without" if count == 1 else "rows without"


VALUE_DTYPES: frozenset[str] = frozenset({"integer", "number"})
"""The profile types of the value columns an aggregate of a repeated key averages or sums."""


def key_aggregate(
    held: Sequence[Held], repeated: RepeatedKey, spec_id: str, how: How | None = None
) -> KeyAggregate | None:
    """The `aggregate` that combines the rows sharing `repeated`'s key, or None when the server combines nothing (the
    module docstring has the rule): by the key's columns, of every other bound column, each once, in binding order.

    `how` is the function the user chose, and it counts only where the plot type leaves the choice open
    (`function_is_open`): the slices of a pie add up whatever a call names, so a spec whose marks add up
    (`SUM_SPECS`) is always summed. Without a choice an open spec takes `mean`, which only a run that was not asked
    reaches (the tool guard asks first).

    `held` are the valid bindings (`bindings.valid_bindings`), so every bound column the plot reads survives the
    aggregate under its name and the bindings carry over; the columns nothing binds leave with it, as the aggregate's
    own change line counts.
    """
    if spec_id in UNREDUCED_SPECS or len(repeated.columns) > MAX_KEYS:
        return None
    separate = SEPARATE_ROLES.get(spec_id, frozenset())
    if any(role.name in separate for _, role, _ in held):
        return None
    keys = set(repeated.columns)
    values: list[str] = []
    for _, _, column in held:
        if column.name in keys or column.name in values:
            continue
        if column.dtype not in VALUE_DTYPES:
            return None  # a label, a date or a flag beside the key: no function of `mean` and `sum` keeps it
        values.append(column.name)
    if not values or len(values) > MAX_AGGREGATE_COLUMNS:
        return None
    chosen: How = (how or "mean") if function_is_open(spec_id) else "sum"
    return KeyAggregate(by=repeated.columns, values=tuple(values), how=chosen)


def function_is_open(spec_id: str) -> bool:
    """Whether the plot type leaves open how rows that share a key combine: every spec whose marks do not add up by
    their nature. A bar of amounts sums and a bar of rates averages, and the spec cannot tell which the user's
    column is, so the user is asked instead of getting a mean nobody chose."""
    return spec_id not in SUM_SPECS


_COMBINED_VERBS: dict[How, str] = {"mean": "averaged", "sum": "summed"}


def combined_line(aggregate: KeyAggregate, rows: int, groups: int, version: int) -> str:
    """The server's change line for a repeated key it combined: `Rows that share a key were combined in data version
    2: averaged 'Reading' over 27 rows into 9, one per 'Length'`, at most `MAX_CHANGE_CHARS`. The value columns are
    counted instead of named when there are more than two or their names would not fit; key names too long to fit
    end in `…`, so the counts and the version always stand."""
    return _combined(f"{COMBINED_HEAD}{version}", aggregate, rows, groups)


def combined_in_view_line(aggregate: KeyAggregate, rows: int, groups: int) -> str:
    """The server's change line for a repeated key it combined among the rows a view of the plot shows, for the plot
    alone (`plot_view.py`): `Rows of the view that share a key were combined for the plot only: summed 'Betrag' over
    24 rows into 12, one per 'Monat'`, built as `combined_line` is. The table keeps every row, so no version is
    named."""
    return _combined(COMBINED_IN_VIEW_HEAD, aggregate, rows, groups)


def _combined(head: str, aggregate: KeyAggregate, rows: int, groups: int) -> str:
    verb = _COMBINED_VERBS[aggregate.how]
    by = " and ".join(f"'{name}'" for name in aggregate.by)
    named = " and ".join(f"'{name}'" for name in aggregate.values)
    counted = f"{len(aggregate.values)} column{'s' if len(aggregate.values) != 1 else ''}"
    for values in ([named] if len(aggregate.values) <= 2 else []) + [counted]:
        line = f"{head}: {verb} {values} over {rows:,} rows into {groups:,}, one per {by}"
        if len(line) <= MAX_CHANGE_CHARS:
            return line
    return line[: MAX_CHANGE_CHARS - 1] + "…"
