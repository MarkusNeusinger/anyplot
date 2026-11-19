"""The marks of a turn that changed the table: what it did to the plot's axes, in the server's own words. No ADK import.

A turn in which the root changes the table (`prepare_data`, `generate_data`, `run_data_code`) can also put other
columns on the plot's roles, by its own `set_bindings` or by the bindings a data step carries over
(`bindings.carry_bindings`). In the prep eval the root, asked for a daily mean, also turned the dates into days since
the first one and put that column on x and the mean on y, in one run of five; the page learned the new bindings
silently from the turn's `done`, and whether the reply said so was up to the model. So every role such a turn
reassigned shows as a line in the server's own words, whatever the reply says, and nothing is blocked
(`docs/decisions/2026-11-19-marks-on-a-data-turn.md`). The marks are a list that grows: a new mark is one more entry
of `MARKS`, with its own test, and the callers stay as they are.

* `axis_moved`: a role that held a column when the turn began holds another column, or none, when it ended.
* `new_column_bound`: a column the turn made, one the table did not have when the turn began, stands on a role when
  the turn ended.

One role gets one line, whichever marks it stands for: `x takes the new column 'Day' instead of 'Temperature'` says
both. The column names stand side by side, so they are quoted as the `rename` change line quotes them.

The facts are the table's version, its column names and the bindings at both ends of the turn (`TableFacts`):

* Only a turn whose end names another data version than its start is marked. A turn that only re-binds, the user's
  own change in the data panel (`PUT /bindings`, no turn) and a turn on a table it did not change get no mark.
* The start is where the root's own steps begin. The `/messages` route takes it before the run; a step the server
  makes itself in the turn moves it to the version that step left, so its own bindings are never marked: the `certain`
  conversions of a paste's summary turn (`paste_conversions.py`, which bind what they made by design and say so) and
  the repeated key a plot run combines (`repeated_keys.py`, announced with the plot).
* A `rename` keeps its column: `prepare_data` moves the start's names through the turn's renames (`renamed`), so a
  renamed bound column is no new column and its role did not move, while a new column that takes the old name later
  is the turn's.
* A turn that began without a table gets none: no role held a column it could have moved, and the first table's
  bindings are the defaults the data card shows.
* A table that replaces the data (`generate_data`, `run_data_code`) is judged by names like any other: a name it has
  again counts as the same column, so asking for `cos(x)` after `sin(x)` (`x` and `y` both times) marks nothing.

The lines join the turn's change lines in the `done` event only (`agents/main.py`, `_session_sync`), after the data
steps' own. They never join the ledger's change lines, a stored version's or a tool result: the root reads none of
them. The `chat_turn` telemetry line counts the codes (`turn_marks`), never a role or a column.
"""

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from typing import Literal

from .schemas import MAX_NOTE_CHARS, Binding, DatasetProfile


TurnMark = Literal["axis_moved", "new_column_bound"]
"""The closed codes of the marks, in the order a role's codes are listed."""


@dataclass(frozen=True)
class TableFacts:
    """The table and the plot's roles at one end of a turn: the data version's id, its column names and the bindings,
    as (role, column) in their order."""

    dataset_id: str
    columns: frozenset[str]
    bindings: tuple[tuple[str, str], ...]

    def renamed(self, rename: Callable[[str], str]) -> "TableFacts":
        """These facts with every column under the name `rename` gives it: the start of the turn after a step that
        renamed columns, so each column is still itself."""
        return TableFacts(
            self.dataset_id,
            frozenset(rename(name) for name in self.columns),
            tuple((role, rename(column)) for role, column in self.bindings),
        )


def table_facts(dataset_id: str, profile: DatasetProfile, bindings: Iterable[Binding]) -> TableFacts:
    """The facts of the data version `dataset_id` with `profile` and the bindings in force on it."""
    return TableFacts(
        dataset_id,
        frozenset(column.name for column in profile.columns),
        tuple((binding.role, binding.column) for binding in bindings),
    )


@dataclass(frozen=True)
class Axis:
    """One role across the turn: the column it held when the turn began and the one it holds when it ended (None for
    none), and whether that one is a column the turn made."""

    role: str
    before: str | None
    now: str | None
    new: bool


MARKS: tuple[tuple[TurnMark, Callable[[Axis], bool]], ...] = (
    ("axis_moved", lambda axis: axis.before is not None and axis.now != axis.before),
    ("new_column_bound", lambda axis: axis.now is not None and axis.new),
)
"""Each mark with the test of a role that it fires on."""


@dataclass(frozen=True)
class RoleMark:
    """One role's line, with the code of every mark it stands for."""

    codes: tuple[TurnMark, ...]
    line: str


def turn_marks(start: TableFacts | None, end: TableFacts | None) -> list[RoleMark]:
    """The marks of a turn from the table it began on (`start`) to the one it ended on (`end`): one per role that a
    mark fires on, in the order of the start's bindings and then the end's. Empty when the turn changed no table (the
    same version at both ends) or began or ended without one."""
    if start is None or end is None or start.dataset_id == end.dataset_id:
        return []
    before, now = dict(start.bindings), dict(end.bindings)
    marks: list[RoleMark] = []
    for role in dict.fromkeys([*before, *now]):
        column = now.get(role)
        axis = Axis(role, before.get(role), column, column is not None and column not in start.columns)
        codes = tuple(code for code, fires in MARKS if fires(axis))
        if codes:
            marks.append(RoleMark(codes, line(axis)))
    return marks


def line(axis: Axis) -> str:
    """The role's line in the style of the change lines, cut to `MAX_NOTE_CHARS` as theirs are."""
    now = f"the new column '{axis.now}'" if axis.new else f"'{axis.now}'"
    if axis.now is None:
        text = f"{axis.role} lost its column '{axis.before}' and holds none now"
    elif axis.before is None:
        text = f"{axis.role} takes {now}"
    else:
        text = f"{axis.role} takes {now} instead of '{axis.before}'"
    return text if len(text) <= MAX_NOTE_CHARS else text[: MAX_NOTE_CHARS - 1] + "…"


def mark_codes(marks: Sequence[RoleMark]) -> list[TurnMark]:
    """The distinct codes of `marks`, sorted: what the `chat_turn` line counts."""
    return sorted({code for mark in marks for code in mark.codes})
