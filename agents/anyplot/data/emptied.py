"""A role whose column the turn took, and the fills that may not take its place. No ADK import.

The daily mean of the temperature per sensor of a table of timed readings drops the humidity, so the scatter plot's y
axis loses its column. The root then added the timestamps as days since the first date, which nobody asked for, and
the carry of the data version (`bindings.carry_bindings`) or its own `set_bindings` put the new column on an axis (the
prep eval's `de-tagesmittel-pro-sensor`). Turning dates into numbers is an offer the user takes in a later turn, and a
number axis is offered the row numbers before any date (`conversions.py`): the turn that took the axis's column makes
neither by itself. The table holds only what was asked for, the reply says which role lost its column, the plot
waits, and the next turn lists what the server can compute.

One rule, judged on typed records only, never on a word of the request, against the turn's first bindings
(`RequestLedger.turn_start`, the bindings in force when the turn's first data or binding call came, followed through
the turn's renames):

* A role is taken (`taken`) when the column it held at the start of the turn is no longer in the table. A role that
  was open at the start is never taken, so the conversion the user takes from an offer binds as before.
* A held column (`held_columns`) is a column the turn made that holds a date turned into numbers
  (`Prepared.date_numbers`, recorded as the operation runs) or the row numbers (`Prepared.row_numbers`): the two fills
  the server offers for an open number axis. A conversion of a text column, a `set_type` in place and a derived column
  (`derive`, `compute`, `classify`, `make_date`) are none: they are the request's own.
* In a turn with a taken role, no held column is made and none ends on a taken role (`wrong_bindings`), except a
  date number made from the taken role's own column (`replaces`): "the days since the start on x instead of the dates"
  replaces the dates, on that role and no other. Row numbers have no source, so they never replace.

`tools/session.py` acts on it: a call that makes a held column in such a turn, or that ends with one bound by the
root on a taken role, is refused and counts against none of the turn's caps (`RequestLedger.guard_held`); a call
whose carry alone would put an earlier call's held column on a taken role is stored with that column kept off.
One message that both takes an axis's column and asks for the days or the row numbers on it cannot be told from the
fault by these records: it waits one turn.

The other side of the boundary is a known gap: a derived column or a text conversion the root adds unasked and puts on
the taken axis passes. So the guard writes one content-free log line per event (hook `emptied_role`: the tool, the
outcome, the spec's role names and the operations' names, never a column or a cell): `refused`, `kept_off`, `bound`
for a column an operation of the turn added (`added_columns`) on a taken role, and `refilled` (the role only) for a
column that was there before the turn on a taken role. `bound` and `refilled` count and do not judge.
"""

from collections.abc import Collection, Mapping, Sequence

from ..schemas import Binding
from .prepare import Operation, Rename, Split


ADDING_OPS = frozenset(
    {
        *("set_type", "classify", "derive", "make_date", "row_number", "date_number", "split"),
        *("extract", "strip", "replace", "compute", "diff", "rolling"),
    }
)
"""The operations that add a column beside the ones there (`set_type` only with a `name` of its own)."""


def held_columns(
    date_numbers: Sequence[str], row_numbers: Sequence[str], converted: Mapping[str, str], before: Collection[str]
) -> dict[str, str | None]:
    """The new held columns of a call, each with its source: the column its date was read from
    (`Prepared.converted`), or None for the row numbers. Only a column the table the call started from (`before`, its
    column names) did not have is new, so a row-number column the paste already had is none."""
    sources: dict[str, str | None] = {name: converted.get(name) for name in date_numbers}
    sources.update({name: None for name in row_numbers if name not in sources})
    return {name: source for name, source in sources.items() if name not in before}


def added_columns(
    operations: Sequence[Operation], before: Collection[str], after: Collection[str], made: Collection[str]
) -> dict[str, str]:
    """The new columns of a call that an operation added beside the others, each with that operation's name, a closed
    word: what the guard's log line says about a column, never its name. `before` and `after` are the column names of
    the tables the call started from and left; `made` are the call's own held columns, among them a `date_number`'s
    column, whose name the server chose. A column a rename, an `aggregate` or a pivot made is none: it holds what was
    there."""
    named: dict[str, str] = {}
    for operation in operations:
        if isinstance(operation, Rename):
            named = {operation.name if name == operation.column else name: kind for name, kind in named.items()}
        elif operation.op in ADDING_OPS:
            names = operation.names if isinstance(operation, Split) else [getattr(operation, "name", None)]
            named.update({name: operation.op for name in names if name})
    return {
        name: named.get(name, "date_number") for name in after if name not in before and (name in named or name in made)
    }


def renamed(name: str, operations: Sequence[Operation]) -> str:
    """`name` after the `rename` operations of a call, in their order: a column the call renames is still that
    column, for the turn's first bindings and for a held column alike."""
    for operation in operations:
        if isinstance(operation, Rename) and operation.column == name:
            name = operation.name
    return name


def taken(start: Mapping[str, str], columns: Collection[str]) -> dict[str, str]:
    """The roles of `start` (role: the column it held at the start of the turn) whose column `columns` lacks."""
    return {role: column for role, column in start.items() if column not in columns}


def replaces(column: str, role: str, held: Mapping[str, str | None], taken_roles: Mapping[str, str]) -> bool:
    """Whether the held `column` is a date number made from the very column the taken `role` held at the start."""
    return role in taken_roles and held.get(column) is not None and held.get(column) == taken_roles[role]


def wrong_bindings(
    bindings: Sequence[Binding], held: Mapping[str, str | None], taken_roles: Mapping[str, str]
) -> list[Binding]:
    """The bindings that put a held column on a taken role it does not replace."""
    return [
        binding
        for binding in bindings
        if binding.role in taken_roles
        and binding.column in held
        and not replaces(binding.column, binding.role, held, taken_roles)
    ]
