"""The view of the plot: which rows of the session's table a plot run draws.

Owner decision of 2026-11-13: a selection ("only 2024", "without the test stores") and a top N belong with the
plot. They are adjusted like axis limits and fine-tuned after a look at the picture, so as steps of the table every
tweak would send the user back to an earlier table version. Cleaning (a total row, wrong entries, duplicates,
outliers) stays a step of the table, and the user's own word wins either way.

The view is typed state, never text: its selections, each the conditions of one `keep_rows` with `where`, and at
most one top N, a `sort` and the `keep_rows` with `n` after it. `prepare_data` stays the root's one entry for a
change of the rows: `route` splits a call's operations into the table's and the view's by their kind, so the root
never chooses between two tools for one wish, and a `keep_rows` that names `target` `table` is the table's. A
later call merges into the view by kind (`merged`): a new top N replaces the one there, a selection replaces the
one on the same columns, any other selection is added, and `reset_view` clears it first.

A plot run draws `view_of` the session's table: the view's operations applied by the engine that makes a data
version, in a fixed order, the selections and then the top N. Nothing is stored: no version, no number, nothing for
the user to confirm, and the table, its card and `query_data` keep every row. The columns keep their names and
their kinds (a text column stays text also when the rows left would read as numbers), so the bindings the user
confirmed stand.

The view belongs to the data it was set on (`session_state.PLOT_VIEW`). New data takes it away: a paste or a
computed table writes it out of the session, since it would hide rows of a table the user never looked at through
it. A change of the same data keeps it, and it is checked against the table when it is set and again whenever it
is read (`current`): after a rename or an undo it may no longer fit, and then it counts as cleared, with a line
that says so, never applied in part. No ADK import.
"""

import csv
import io
import logging
from collections.abc import Collection
from dataclasses import dataclass, replace
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from core.spec_roles import DataRole

from .data.bindings import check_bindings
from .data.months import month_number, month_order
from .data.parse import MAX_COMPUTED_BYTES, ParsedDataset, ParseError, parse_dataset
from .data.prepare import (
    MAX_CONDITIONS,
    ApplyView,
    Condition,
    DropColumns,
    KeepRows,
    Operation,
    PrepareError,
    ResetView,
    RowNumber,
    Sort,
    apply_operations,
    condition_words,
    suffixed_name,
    with_date_notes,
)
from .data.store import StoredDataset, dataset_size
from .language import DEFAULT_LANGUAGE
from .schemas import MAX_ROWS, Binding, DatasetProfile
from .session_state import PLOT_VIEW, PLOT_VIEW_BEFORE


logger = logging.getLogger("anyplot.agents")

MAX_SELECTIONS = 3
"""The selections one view holds. Each has up to `MAX_CONDITIONS` conditions, so a view of three is already more
than a user keeps in mind; a fourth is refused with the way out (`reset_view`)."""
MAX_PART_CHARS = 120
"""The longest part of a view on the page (`Viewed.shown`): one selection or the top N. A selection that names many
values gives way with an ellipsis, as the view's words do in the plot's line."""


class Top(BaseModel):
    """A top N: the rows sorted by `column`, the first `n` kept."""

    model_config = ConfigDict(extra="forbid")

    column: str = Field(min_length=1)
    descending: bool = False
    n: int = Field(ge=1, le=MAX_ROWS)


class PlotView(BaseModel):
    """The rows a plot run draws: those every selection keeps, and of them the top N when there is one."""

    model_config = ConfigDict(extra="forbid")

    selections: list[list[Condition]] = Field(default_factory=list, max_length=MAX_SELECTIONS)
    top: Top | None = None
    combine: Literal["sum", "mean"] | None = None
    """How the user said rows of the view that share the plot's key combine (`repeated_keys.combine_in_view`), once
    a run asked and they answered. It stays with the view, since nothing else remembers it: without a view the
    answer becomes a data version, under a view nothing is stored, and every later run would ask again. It is no
    row operation, goes with the view when that is cleared, and a view of it alone is none."""

    @property
    def empty(self) -> bool:
        return not self.selections and self.top is None

    def operations(self) -> list[Operation]:
        """The view as the engine's operations, in the order it applies them: the selections, then the top N."""
        steps: list[Operation] = [KeepRows(op="keep_rows", where=list(where)) for where in self.selections]
        if self.top is not None:
            steps.append(Sort(op="sort", column=self.top.column, descending=self.top.descending))
            steps.append(KeepRows(op="keep_rows", n=self.top.n))
        return steps

    def parts(self, text_columns: Collection[str] = ()) -> list[str]:
        """The view's parts in words, one per selection and one for the top N: `Jahr = 2024`, `Land is 'CH' or 'AT'`,
        `top 10 by Umsatz`. `text_columns` are the table's text columns, whose values are quoted."""
        parts = [
            " and ".join(condition_words(condition, text=condition.column in text_columns) for condition in where)
            for where in self.selections
        ]
        if self.top is not None:
            parts.append(f"{'top' if self.top.descending else 'lowest'} {self.top.n} by {self.top.column}")
        return parts

    def words(self, text_columns: Collection[str] = ()) -> str:
        """The view in a line's words: its `parts`, as `Jahr = 2024; Land is 'CH' or 'AT'; top 10 by Umsatz`."""
        return "; ".join(self.parts(text_columns))

    def stamp(self) -> dict[str, Any] | None:
        """What a plot version records of the view it drew, or None for every row: two runs drew the same rows of a
        table, combined the same way, exactly when their stamps are equal."""
        return None if self.empty else self.model_dump(mode="json", exclude_none=True)


class ViewRefused(ValueError):
    """A call's operations cannot become a view: the message names the reason in the root's terms, never a cell."""


@dataclass(frozen=True)
class Routed:
    """One `prepare_data` call's operations by where they land: `table` as a data version, `selections` and `top` in
    the view of the plot, `reset` when the call clears the view first, `apply` when it clears it by making the
    rows it shows the table's (`apply_view`: the caller puts the view's operations before `table`)."""

    table: list[Operation]
    selections: list[list[Condition]]
    top: Top | None
    reset: bool
    apply: bool = False

    @property
    def view(self) -> bool:
        """Whether the call touches the view at all."""
        return self.reset or bool(self.selections) or self.top is not None


def _for_plot(operation: Operation) -> bool:
    return isinstance(operation, KeepRows) and operation.target == "plot"


def route(operations: list[Operation]) -> Routed:
    """Split one call's operations into the table's and the view's.

    The view's are the end of the call: any number of `keep_rows` with `where`, then at most one `sort` followed by
    a `keep_rows` with `n`, the order in which a view applies them. Everything before is the table's. A `keep_rows`
    that an operation of the table follows (the selected rows summed per month, a column computed for the top 10)
    is the table's too, since that operation works on the rows it leaves, and so is one without a `sort` before its
    `n`, which ranks the rows by nothing a view could keep: the whole call then lands in the table. `reset_view`
    and `apply_view` come first or not at all, and a call has one of them (`ViewRefused`): both leave the view
    empty before the rest applies, `apply_view` by moving its rows into the table.
    """
    reset = bool(operations) and isinstance(operations[0], ResetView)
    apply = bool(operations) and isinstance(operations[0], ApplyView)
    rest = list(operations[1:] if reset or apply else operations)
    if any(isinstance(operation, ResetView | ApplyView) for operation in rest):
        raise ViewRefused(
            "reset_view and apply_view are the first operation of a call, and a call has one of them: they settle "
            "the view before the others apply"
        )
    end = len(rest)
    top: Top | None = None
    if end >= 2:
        last, before = rest[end - 1], rest[end - 2]
        if _for_plot(last) and isinstance(last, KeepRows) and last.n is not None and isinstance(before, Sort):
            top = Top(column=before.column, descending=before.descending, n=last.n)
            end -= 2
    selections: list[list[Condition]] = []
    while end > 0:
        operation = rest[end - 1]
        if not (_for_plot(operation) and isinstance(operation, KeepRows) and operation.where is not None):
            break
        selections.insert(0, list(operation.where))
        end -= 1
    table = rest[:end]
    if any(_for_plot(operation) for operation in table):
        return Routed(table=rest, selections=[], top=None, reset=reset or apply, apply=apply)
    return Routed(table=table, selections=selections, top=top, reset=reset or apply, apply=apply)


def table_only(operations: list[Operation]) -> Routed:
    """A call whose every operation is the table's, whatever its `keep_rows` say: one that starts from an earlier
    version (`from_version`) rebuilds the table. A `reset_view` in it still clears the view, first or not at all;
    an `apply_view` is refused (`ViewRefused`), since the view shows rows of the current table, not of that one."""
    routed = route(operations)
    if routed.apply:
        raise ViewRefused("apply_view works on the current table, whose rows the view shows: leave from_version out")
    rest: list[Operation] = [operation for operation in operations if not isinstance(operation, ResetView)]
    return Routed(table=rest, selections=[], top=None, reset=routed.reset)


def merged(view: PlotView, routed: Routed) -> PlotView:
    """The view after a call: cleared first when the call says so, each of its selections in place of the one on the
    same columns or added, its top N in place of the one there. Raises `ViewRefused` past `MAX_SELECTIONS`."""
    base = PlotView() if routed.reset else view
    selections = [list(where) for where in base.selections]
    for where in routed.selections:
        columns = {condition.column for condition in where}
        selections = [held for held in selections if {condition.column for condition in held} != columns]
        selections.append(list(where))
    if len(selections) > MAX_SELECTIONS:
        raise ViewRefused(
            f"the view of the plot holds at most {MAX_SELECTIONS} selections, each with up to {MAX_CONDITIONS} "
            "conditions: start the call with reset_view and name the selections that stay"
        )
    top = routed.top if routed.top is not None else base.top
    return PlotView(selections=selections, top=top, combine=base.combine)


@dataclass(frozen=True)
class Viewed:
    """A table as a view shows it: the rows left, as a parsed dataset, and the engine's line for each step."""

    parsed: ParsedDataset
    changes: list[str]
    of_rows: int
    """The rows of the table the view was applied to."""

    @property
    def rows(self) -> int:
        return self.parsed.profile.rows

    def summary(self, data_version: int) -> str:
        """`the plot draws 10 of 248 rows of data v3`, the server's line over the view's steps."""
        return f"the plot draws {self.rows} of {self.of_rows} rows of data v{data_version}"

    def note(self, view: PlotView, data_version: int, limit: int) -> str:
        """The first line of a plot's "what changed" while a view holds: `The plot draws 10 of the 248 rows of data v3
        (view: Jahr = 2024; top 10 by Umsatz)`, within `limit` characters. The counts always stand; the view's
        words give way."""
        head = f"The plot draws {self.rows} of the {self.of_rows} rows of data v{data_version} (view: "
        words = view.words(self._text_columns())
        return head + _within(words, limit - len(head) - 1) + ")"

    def shown(self, view: PlotView) -> dict[str, Any]:
        """The view as the page shows it beside the plot and the data (`ShownView` in `app/src/lib/agent.ts`): the
        counts of `note`, and the view's parts, each within `MAX_PART_CHARS`. The parts name the user's columns and
        values, so this goes to the page alone, never into a tool result the root reads."""
        parts = [_within(part, MAX_PART_CHARS) for part in view.parts(self._text_columns())]
        return {"rows": self.rows, "of_rows": self.of_rows, "parts": parts}

    def _text_columns(self) -> list[str]:
        return [name for name, dtype in self.parsed.column_dtypes.items() if dtype == "text"]


def _within(words: str, room: int) -> str:
    """`words` as they are, or cut to `room` characters with an ellipsis at the end."""
    return words if len(words) <= room else words[: max(room - 1, 0)] + "…"


def view_of(parsed: ParsedDataset, view: PlotView, language: str = DEFAULT_LANGUAGE) -> Viewed:
    """`parsed` as `view` shows it; raises `PrepareError` when a step does not fit the table or no row is left.

    The result is parsed again as a data version is, except that every text column stays text: the rows left may
    all read as numbers or dates, and a column that changed its kind would move the bindings the user confirmed.
    """
    return _seen(parsed, view.operations(), language)


def _seen(parsed: ParsedDataset, operations: list[Operation], language: str) -> Viewed:
    """`parsed` after `operations` that only choose or order its rows, read back with its text columns kept text."""
    prepared = apply_operations(parsed, operations, language=language)
    text = [name for name, dtype in parsed.column_dtypes.items() if dtype == "text"]
    try:
        again = parse_dataset(
            prepared.csv,
            text_columns=[*prepared.text_columns, *text],
            find_table=False,
            max_bytes=MAX_COMPUTED_BYTES,
            canonical=True,
        )
    except ParseError as exc:  # the rows are a subset of a stored table, so a refusal here is a bug
        raise PrepareError("invalid_operation", "the view's rows could not be read back") from exc
    return Viewed(with_date_notes(again, prepared), list(prepared.changes), parsed.profile.rows)


def viewed_dataset(dataset: StoredDataset, viewed: Viewed) -> StoredDataset:
    """The dataset a plot run draws under a view: `dataset` with the view's rows, under the same id and number, since
    it is the same data version seen through the view. Never stored, and without the cells kept as pasted, whose
    rows are no longer these."""
    parsed = viewed.parsed
    return replace(
        dataset,
        csv=parsed.csv,
        profile=parsed.profile,
        column_dtypes=dict(parsed.column_dtypes),
        parse_dates=list(parsed.parse_dates),
        preview=[list(row) for row in parsed.preview],
        size_bytes=dataset_size(parsed),
        pasted_cells={},
    )


OLDEST_FIRST_LINE = "The plot draws the rows oldest first by '{column}'; the table runs newest first and stays as it is"
"""What a run says when it ordered its rows by a date column (`drawn_in_order`)."""


CALENDAR_ORDER_LINE = (
    "The plot draws the rows in calendar order by '{column}'; "
    "the table lists its months in another order and stays as it is"
)
"""What a run says when it ordered its rows by a column of month names (`drawn_in_order`)."""


@dataclass(frozen=True)
class RunOrder:
    """The order a run puts its rows in before it draws them: by `column`, with the engine's `operations`, and the
    `line` that says so."""

    column: str
    operations: list[Operation]
    line: str


def run_order(bindings: list[Binding], shown: StoredDataset, view: PlotView) -> RunOrder | None:
    """The order a run puts the rows it draws in, by the first bound column that asks for one, or None.

    A date column asks for one when its dates run newest first down those rows (`ColumnProfile.order`): oldest
    first. A text column of month names (`ColumnProfile.months`) asks for one when its months are out of calendar
    order (`months.month_order`): from January on, or, for a run that goes backward over the turn of the year, the
    reverse of the rows. Months that already run along the calendar, a fiscal year among them, stand.

    A bound date column is the plot's time axis, whichever way it runs: month names bound beside it are labels of
    its rows, and ordering the rows by them would take the dates out of their order. So month names are asked only
    when no date column is bound.

    None too while the view's top N ranks the rows by another column: that order is the one the user asked for, and
    dates or months that happen to fall along it are no reason to undo it. A top N by the column itself ("the
    latest 12") leaves the newest rows newest first, and those are drawn in order like any other.
    """
    ranked_by = view.top.column if view.top is not None else None
    columns = {column.name: column for column in shown.profile.columns}
    bound = [columns[binding.column] for binding in bindings if binding.column in columns]
    orderable = [column for column in bound if ranked_by in (None, column.name)]
    for column in orderable:
        if column.dtype == "datetime" and column.order == "descending":
            return RunOrder(column.name, [Sort(op="sort", column=column.name)], OLDEST_FIRST_LINE)
    if any(column.dtype == "datetime" for column in bound):
        return None
    for column in orderable:
        if column.dtype == "text" and column.months is not None:
            operations = _month_operations(shown, column.name)
            if operations:
                return RunOrder(column.name, operations, CALENDAR_ORDER_LINE)
    return None


def _cells(shown: StoredDataset, column: str) -> list[str]:
    """The cells of `column` down the rows of `shown` as `data.csv` writes them, an empty one as `""`."""
    rows = csv.reader(io.StringIO(shown.csv, newline=""))
    header = next(rows, [])
    if column not in header:
        return []
    place = header.index(column)
    return [row[place] for row in rows]


def _month_operations(shown: StoredDataset, column: str) -> list[Operation]:
    """The engine's operations that put the rows of `shown` in the order of the month names of `column`; none when
    they stand as they are (`months.month_order`)."""
    order = month_order([month_number(cell) if cell else None for cell in _cells(shown, column)])
    if order == "calendar":
        return [Sort(op="sort", column=column)]  # the engine orders month names by the calendar, stable
    if order == "reversed":
        # The engine has no operation that turns the rows round: number them, sort by the number, drop it again.
        number = suffixed_name(column, "row", shown.column_dtypes)
        return [
            RowNumber(op="row_number", name=number),
            Sort(op="sort", column=number, descending=True),
            DropColumns(op="drop_columns", columns=[number]),
        ]
    return []


def drawn_in_order(
    shown: StoredDataset, bindings: list[Binding], view: PlotView, language: str = DEFAULT_LANGUAGE
) -> tuple[StoredDataset, str | None]:
    """The rows a run draws, in the order a bound date or month column asks for, and the line that says so; `shown`
    as it is and None when no bound column asks for one (`run_order`).

    A time series is drawn in date order, and what the plot code computes along the rows (a rolling mean, a running
    total, the last value it labels) reads them in that order too. The order is the plot's (owner decision of
    2026-11-13), so the table is not sorted for it: `shown` is ordered for the run alone, by the engine's own stable
    `sort`, under the table's id and number, and stored nowhere. Rows without a date or a month come last, except
    in a run of months turned round, where each row keeps its place in the run.
    """
    order = run_order(bindings, shown, view)
    if order is None:
        return shown, None
    try:
        seen = _seen(shown.as_parsed(), order.operations, language)
    except PrepareError:
        return shown, None  # a column the engine cannot order is drawn as it stands
    if dict(seen.parsed.column_dtypes) != dict(shown.column_dtypes) or seen.rows != shown.profile.rows:
        # The same rows read back as another kind of column would move the bindings the user confirmed.
        logger.warning("rows not ordered for the run: the ordered table reads differently")
        return shown, None
    return viewed_dataset(shown, seen), order.line.format(column=order.column)


def read_view(state: Any, key: str = PLOT_VIEW) -> PlotView:
    """The session's view as stored under `key`, or the empty view: for nothing stored and for a value that does not
    validate, which no code path writes."""
    raw = state.get(key)
    if not raw:
        return PlotView()
    try:
        return PlotView.model_validate(raw)
    except ValidationError:
        return PlotView()


def view_delta(view: PlotView) -> dict[str, Any]:
    """The state delta that stores `view`; an empty view is stored as none."""
    return {PLOT_VIEW: None if view.empty else view.model_dump(mode="json", exclude_none=True)}


def settled_delta(view: PlotView) -> dict[str, Any]:
    """The state delta of a view the root set or cleared for the user: `view_delta`, and the view a paste had taken
    away is forgotten (`PLOT_VIEW_BEFORE`), since the user has now said what the plot of this data shows."""
    return {**view_delta(view), PLOT_VIEW_BEFORE: None}


def view_before(state: Any, dataset: StoredDataset, language: str = DEFAULT_LANGUAGE) -> str | None:
    """The words of the view a paste took away (`PLOT_VIEW_BEFORE`), when it would fit `dataset`, the new table: what
    the summary of the new data names and offers again. None when there is none, or when it fits no row or no column
    of the new table, where there is nothing to offer."""
    before = read_view(state, PLOT_VIEW_BEFORE)
    if before.empty:
        return None
    try:
        view_of(dataset.as_parsed(), before, language)
    except PrepareError:
        return None
    return before.words([name for name, dtype in dataset.column_dtypes.items() if dtype == "text"])


@dataclass(frozen=True)
class Current:
    """The session's view as it holds for a table: `view` (empty when none is set or it no longer fits), the table
    seen through it (`viewed`, None for every row), and `cleared`, the line for a view that no longer fits."""

    view: PlotView
    viewed: Viewed | None = None
    cleared: str | None = None


CLEARED_LINE = "the view of the plot no longer fits this table and was cleared: the plot draws every row again"
"""What a run or a data change says when the stored view cannot be applied to the table any more (a column it
names is gone or changed its kind, or no row would be left)."""
EVERY_ROW_LINE = "The view of the plot is cleared: the plot draws every row of data v{number}, {rows} in all"
"""What a run says when the version it changes drew a view of the plot and none is set any more (the chat's
`reset_view`, the page's `.show_all()`, a change of the table the view no longer fit): the count comes back as it
went, in the first line of "what changed". It says nothing of "again", since the data may be a later version than
the one the view was set on."""


def breaks_bindings(
    bindings: list[Binding], roles: list[DataRole], table: DatasetProfile, seen: DatasetProfile
) -> bool:
    """Whether bindings that hold on the table stop holding on a view's rows: a view may narrow what the plot shows,
    never leave it without a column it needs (every cell of a bound column empty among the rows left)."""
    before = check_bindings(bindings, roles, table)
    if not before.complete or before.errors:
        return False  # nothing to break: the bindings wait for the user either way
    after = check_bindings(bindings, roles, seen)
    return not after.complete or bool(after.errors)


def current(
    state: Any,
    dataset: StoredDataset,
    language: str = DEFAULT_LANGUAGE,
    *,
    bindings: list[Binding] | None = None,
    roles: list[DataRole] | None = None,
) -> Current:
    """The stored view applied to `dataset`, or cleared when it no longer fits: a step that does not apply, no row
    left, or, with the session's `bindings` and the spec's `roles`, rows on which bindings that hold on the table no
    longer hold (`breaks_bindings`). Every reader of the view passes them, so the run, the session block and
    `prepare_data` agree on whether a view is in force. Reads only: the caller that may write the state stores
    `view_delta(PlotView())` for a cleared one."""
    view = read_view(state)
    if view.empty:
        return Current(view)
    try:
        seen = view_of(dataset.as_parsed(), view, language)
    except PrepareError:
        return Current(PlotView(), cleared=CLEARED_LINE)
    if bindings is not None and roles is not None:
        if breaks_bindings(bindings, roles, dataset.profile, seen.parsed.profile):
            return Current(PlotView(), cleared=CLEARED_LINE)
    return Current(view, seen)
