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

The view is checked against the table when it is set and again when it is read (`current`): a table that changed
since (a rename, another paste, an undo) may no longer fit it, and then the view is cleared with a line that says
so, never applied in part. No ADK import.
"""

from collections.abc import Collection
from dataclasses import dataclass, replace
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .data.parse import MAX_COMPUTED_BYTES, ParsedDataset, ParseError, parse_dataset
from .data.prepare import (
    MAX_CONDITIONS,
    Condition,
    KeepRows,
    Operation,
    PrepareError,
    ResetView,
    Sort,
    apply_operations,
    condition_words,
    with_date_notes,
)
from .data.store import StoredDataset, dataset_size
from .language import DEFAULT_LANGUAGE
from .schemas import MAX_ROWS
from .session_state import PREFIX


PLOT_VIEW = PREFIX + "plot_view"
"""The session's view of the plot, `PlotView.model_dump()`; absent or empty when the plot draws every row. It
outlives a library switch, a start over and a new paste, as the plot memory does, and is cleared when it no longer
fits the table (`current`)."""
MAX_SELECTIONS = 3
"""The selections one view holds. Each has up to `MAX_CONDITIONS` conditions, so a view of three is already more
than a user keeps in mind; a fourth is refused with the way out (`reset_view`)."""


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

    def words(self, text_columns: Collection[str] = ()) -> str:
        """The view in a line's words: `Jahr = 2024; Land is 'CH' or 'AT'; top 10 by Umsatz`. `text_columns` are the
        table's text columns, whose values are quoted."""
        parts = [
            " and ".join(condition_words(condition, text=condition.column in text_columns) for condition in where)
            for where in self.selections
        ]
        if self.top is not None:
            parts.append(f"{'top' if self.top.descending else 'lowest'} {self.top.n} by {self.top.column}")
        return "; ".join(parts)

    def stamp(self) -> dict[str, Any] | None:
        """What a plot version records of the view it drew, or None for every row: two runs drew the same rows of a
        table exactly when their stamps are equal."""
        return None if self.empty else self.model_dump(mode="json", exclude_none=True)


class ViewRefused(ValueError):
    """A call's operations cannot become a view: the message names the reason in the root's terms, never a cell."""


@dataclass(frozen=True)
class Routed:
    """One `prepare_data` call's operations by where they land: `table` as a data version, `selections` and `top` in
    the view of the plot, `reset` when the call clears the view first."""

    table: list[Operation]
    selections: list[list[Condition]]
    top: Top | None
    reset: bool

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
    comes first or not at all (`ViewRefused`).
    """
    reset = bool(operations) and isinstance(operations[0], ResetView)
    rest = list(operations[1:] if reset else operations)
    if any(isinstance(operation, ResetView) for operation in rest):
        raise ViewRefused("reset_view is the first operation of a call: it clears the view before the others apply")
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
        return Routed(table=rest, selections=[], top=None, reset=reset)
    return Routed(table=table, selections=selections, top=top, reset=reset)


def table_only(operations: list[Operation]) -> Routed:
    """A call whose every operation is the table's, whatever its `keep_rows` say: one that starts from an earlier
    version (`from_version`) rebuilds the table. A `reset_view` in it still clears the view, first or not at all."""
    routed = route(operations)
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
    return PlotView(selections=selections, top=routed.top if routed.top is not None else base.top)


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
        text = [name for name, dtype in self.parsed.column_dtypes.items() if dtype == "text"]
        words = view.words(text)
        room = limit - len(head) - 1
        return head + (words if len(words) <= room else words[: max(room - 1, 0)] + "…") + ")"


def view_of(parsed: ParsedDataset, view: PlotView, language: str = DEFAULT_LANGUAGE) -> Viewed:
    """`parsed` as `view` shows it; raises `PrepareError` when a step does not fit the table or no row is left.

    The result is parsed again as a data version is, except that every text column stays text: the rows left may
    all read as numbers or dates, and a column that changed its kind would move the bindings the user confirmed.
    """
    prepared = apply_operations(parsed, view.operations(), language=language)
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


def read_view(state: Any) -> PlotView:
    """The session's view as stored, or the empty view: for nothing stored and for a value that does not validate,
    which no code path writes."""
    raw = state.get(PLOT_VIEW)
    if not raw:
        return PlotView()
    try:
        return PlotView.model_validate(raw)
    except ValidationError:
        return PlotView()


def view_delta(view: PlotView) -> dict[str, Any]:
    """The state delta that stores `view`; an empty view is stored as none."""
    return {PLOT_VIEW: None if view.empty else view.model_dump(mode="json", exclude_none=True)}


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


def current(state: Any, dataset: StoredDataset, language: str = DEFAULT_LANGUAGE) -> Current:
    """The stored view applied to `dataset`, or cleared when it no longer fits. Reads only: the caller that may write
    the state stores `view_delta(PlotView())` for a cleared one."""
    view = read_view(state)
    if view.empty:
        return Current(view)
    try:
        return Current(view, view_of(dataset.as_parsed(), view, language))
    except PrepareError:
        return Current(PlotView(), cleared=CLEARED_LINE)
