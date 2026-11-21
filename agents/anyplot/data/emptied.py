"""A role whose column the turn took, and the fills that may not take its place. No ADK import.

The daily mean of the temperature per sensor of a table of timed readings drops the humidity, so the scatter plot's y
axis loses its column. The root then added the timestamps as days since the first date, which nobody asked for, and
the carry of the data version (`bindings.carry_bindings`) or its own `set_bindings` put the new column on an axis (the
prep eval's `de-tagesmittel-pro-sensor`). Turning dates into numbers is an offer the user takes in a later turn, and a
number axis is offered the row numbers before any date (`conversions.py`): the turn that took the axis's column makes
neither by itself. The table holds only what was asked for, the reply says which role lost its column, the plot
waits, and the next turn lists what the server can compute.

One rule, judged on typed records only, never on a word of the request, against the turn's first bindings
(`RequestLedger.turn_start`, the bindings in force when the turn's first data or binding call came, kept per required
role of the spec by `start_columns` and followed through the turn's renames):

* A required role of the spec is taken (`taken`) when none of the columns it held at the start of the turn is left in
  the table. A family of roles (the series `y1`, `y2`, ... of a multi-series plot) is one role, taken only when its
  last series is gone, and a binding is judged by the spec's role it names (`family_name`), so `y4` belongs to the
  family of `y1`. An optional role, and one the plot computes when it is open (`DataRole.computed`), never makes a
  turn a taken turn: the plot does not wait for it. A role that was open at the start is never taken, so the
  conversion the user takes from an offer binds as before.
* A held column (`held_columns`) is a column the turn made that holds a date turned into numbers
  (`Prepared.date_numbers`, recorded as the operation runs) or the row numbers (`Prepared.row_numbers`): the two fills
  the server offers for an open number axis. A conversion of a text column, a `set_type` in place and a derived column
  (`derive`, `compute`, `classify`, `make_date`) are none: they are the request's own.
* In a turn with a taken role, no held column is made and none ends on a taken role (`wrong_bindings`), except a
  date number made from one of the taken role's own columns (`replaces`): "the days since the start on x instead of
  the dates" replaces the dates, on that role and no other. Row numbers have no source, so they never replace.

`tools/session.py` acts on it: a call that makes a held column in such a turn, or that ends with one bound by the
root on a taken role, is refused and counts against none of the turn's caps (`RequestLedger.guard_held`); a call
whose carry alone would put an earlier call's held column on a taken role is stored with that column kept off.
One message that both takes the column of a required role and asks for the days or the row numbers on it cannot be
told from the fault by these records: it waits one turn.

A second trigger needs no taken role (`date_misfits`): a `set_bindings` of the turn refused because it put a date
column on a role that takes numbers (`BindingCheck.misfits`, the typed record of the refusal). The root then turned
the dates into numbers by itself and bound them (the prep eval's `en-date-from-year-month-text`, where the axis was
open, and `de-tagesmittel-pro-sensor` once its root kept every column). That refusal carries a fixed `message`: which
numbers a date becomes is the user's choice, an offer. From then on the turn makes no held column: a `prepare_data`
call that would make one is refused the same way and counts against none of the turn's caps. A root asked for the
numbers makes them first and binds them after, so the trigger never sees it; a root that tries the dates first on a
message that did ask for the numbers waits one turn, as on a taken role, and one that turns dates into numbers unasked
without trying the dates first passes.

Named limits, pinned as they stand and none of them a promise: a family that keeps one of its series is not taken, so
a held column made in the turn joins it as a series, put on the open member by the carry alone or bound by the root; a held column made under the old name of a column the turn renamed
away keeps that binding, since the start follows the rename; a role's column read as text stays in the table, so the
role is not taken though the column no longer fits it; the carry itself can refill a taken role with a spare column
(the year or the month an `aggregate` keeps), and the turn stays taken, so a date number the user asks for then waits
one turn, as after a refill by the root; `run_data_code`, `generate_data` and the next turn's carry are not covered.

The other side of the boundary is a known gap: a derived column or a text conversion the root adds unasked and puts on
the taken axis passes. So the guard writes one content-free log line per event (hook `emptied_role`: the tool, the
outcome, the spec's role names and the operations' names, never a column or a cell): `refused`, `kept_off`, `bound`
for a column an operation of the turn added (`added_columns`) on a taken role, and `refilled` (the role only) for a
column that was there before the turn on a taken role. `bound` and `refilled` count and do not judge. The second
trigger writes `misfit` (the roles only) for each `set_bindings` refused for a date column on a role that takes
numbers, and `offer_held` for a call it refused after one, so the two halves of that trace are counted apart.
"""

from collections.abc import Collection, Mapping, Sequence

from core.spec_roles import DataRole

from ..schemas import Binding
from .bindings import Misfit, resolve_role
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


def family_name(role: str, roles: list[DataRole]) -> str:
    """The spec role a binding's role names (`y` for its member `y2`), as `check_bindings` lists a missing one."""
    spec_role = resolve_role(role, roles)
    return spec_role.name if spec_role is not None else role


def start_columns(bindings: Sequence[Binding], roles: list[DataRole]) -> dict[str, list[str]]:
    """The bindings at the start of the turn as the guard keeps them: each required role of the spec that holds a
    column (neither an optional role nor one the plot computes, the roles `check_bindings` never lists as missing)
    with the columns it holds, a family's members together under the family's name, in binding order."""
    required = {role.name for role in roles if role.required and not role.computed}
    start: dict[str, list[str]] = {}
    for binding in bindings:
        name = family_name(binding.role, roles)
        if name in required:
            start.setdefault(name, []).append(binding.column)
    return start


def taken(start: Mapping[str, Sequence[str]], columns: Collection[str]) -> dict[str, list[str]]:
    """The roles of `start` (role: the columns it held at the start of the turn) none of whose columns `columns`
    holds: a family keeps its role while one of its series is left."""
    return {role: list(held) for role, held in start.items() if not any(column in columns for column in held)}


def replaces(
    column: str,
    role: str,
    held: Mapping[str, str | None],
    taken_roles: Mapping[str, Sequence[str]],
    roles: list[DataRole],
) -> bool:
    """Whether the held `column` on `role` (a binding's role or a spec role) is a date number made from one of the
    very columns the taken spec role held at the start."""
    source = held.get(column)
    family = family_name(role, roles)
    return family in taken_roles and source is not None and source in taken_roles[family]


def date_misfits(misfits: Sequence[Misfit], roles: list[DataRole]) -> dict[str, str]:
    """The spec roles a refused `set_bindings` put a date column on although they take numbers, each with that column
    (`BindingCheck.misfits`, the typed record of the refusal): a role that takes dates too never refuses one."""
    return {
        family_name(misfit.role, roles): misfit.column
        for misfit in misfits
        if misfit.dtype == "datetime" and "numeric" in misfit.kinds
    }


def wrong_bindings(
    bindings: Sequence[Binding],
    held: Mapping[str, str | None],
    taken_roles: Mapping[str, Sequence[str]],
    roles: list[DataRole],
) -> list[Binding]:
    """The bindings that put a held column on a member of a taken spec role it does not replace."""
    return [
        binding
        for binding in bindings
        if family_name(binding.role, roles) in taken_roles
        and binding.column in held
        and not replaces(binding.column, binding.role, held, taken_roles, roles)
    ]
