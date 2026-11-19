"""A required role that the turn's own change of the data left without its column, and the fills that wait for it.

No ADK import. The daily mean of the temperature per sensor of a table of timed readings drops the humidity, so the
scatter plot's y axis loses its column and no column is left to take it. The root then added the timestamps as days
since the first date, which nobody asked for, and the carry of the data version (`bindings.carry_bindings`) or its
own `set_bindings` put the new column on an axis (the prep eval's `de-tagesmittel-pro-sensor`). Turning dates into
numbers is an offer the user takes in a later turn, and a number axis is offered the row numbers before any date
(`conversions.py`): the turn that emptied the axis makes neither by itself. The table holds only what was asked for,
the reply says which role lost its column, the plot waits, and the next turn lists what the server can compute.

The guard reads typed records only, never a word of the request:

* `emptied`: the required roles a `prepare_data` call leaves open that were bound before it. They are judged with
  the turn's fills that no role held before the call hidden (`hidden`), so a call that empties a role and fills it
  with one of its own counts as emptying it.
* `made_columns`: the new columns that hold a date turned into numbers (`Prepared.date_numbers`: a `date_number`, or
  `extract` with `digits` on a column that is a date when the operation runs, so a column read as dates and numbered
  in the same call counts) or the row numbers (`Prepared.row_numbers`): the two fills the server offers
  for an open number axis, which no request of the turn's own needs to fill one. A conversion of a text column (a
  `set_type` into a column of its own, `extract`, `strip`, `replace`, `split`) is none: it is usually the request's
  own, a price read from `CHF 1'200` and then summed per region by the same call, whose aggregate takes the axes'
  columns. Neither is a `set_type` in place (a decimal mark) or a derived column (`derive`, `compute`, `classify`,
  `make_date`): a request that names one gets it on the axis it names, also in a turn that emptied another.
* `held_bindings`: the bindings that put such a column on a role that did not hold it before.

Once a call of the turn has emptied a role, the root's tools refuse a `prepare_data` call that makes such a column,
and a `set_bindings` call that binds one (`tools/session.py`); the refusal counts against none of the turn's caps
(`RequestLedger.guard_held`). A call that makes none, but whose carry would put a fill an earlier call of the turn made
on a role, is the user's change: it is stored, the fill stays in the table and off every role, and the role waits for
the user, since the decided outcome is that the role waits, not the change. The two cannot be told apart by these
records when one message both empties an axis and asks for the days or the row numbers on it: that request waits one
turn, and the next turn lists the offer.

The other side of the boundary is a known gap: a derived column or a text conversion the root adds unasked and puts on
the emptied axis passes. So four outcomes write one content-free log line each (hook `emptied_role`: the tool, the
outcome, the spec's role names and the names of the operations that made the columns, never a column or a cell):
`refused`, `kept_off` for a change stored with an earlier fill kept off the role, `bound` for a column another
operation of the turn added (`added_columns`) taking a role whose column the turn took, and `refilled` (the role only)
for a column that was there before the turn put on a role the turn emptied, by `set_bindings` or by a later call's
carry. `bound` and `refilled` count and do not judge: an asked binding writes them too. They are how real use and the
eval show whether the root goes round the guard that way.
"""

from collections.abc import Collection, Sequence
from dataclasses import dataclass

from core.spec_roles import DataRole

from ..schemas import Binding, DatasetProfile
from .bindings import carry_bindings, check_bindings, resolve_role
from .prepare import Operation, Rename, Split


@dataclass(frozen=True)
class Emptied:
    """A required role a change of the data left open, and the column it was bound to before the change."""

    role: str
    column: str

    def line(self) -> str:
        """`y: Feuchte`, as the session block lists it inside a data fence (the column is the user's)."""
        return f"{self.role}: {self.column}"


def made_columns(date_numbers: Sequence[str], row_numbers: Sequence[str], before: Collection[str]) -> list[str]:
    """The new columns of a call that hold a date turned into numbers or the row numbers, in order:
    `Prepared.date_numbers`, which the engine records when the operation runs on a column that is a date at that
    moment, and `Prepared.row_numbers`, each only when the table the call started from (`before`, its column names)
    did not have it, so a row-number column the paste already had is none."""
    return [name for name in dict.fromkeys([*date_numbers, *row_numbers]) if name not in before]


ADDING_OPS = frozenset(
    {
        *("set_type", "classify", "derive", "make_date", "row_number", "date_number", "split"),
        *("extract", "strip", "replace", "compute", "diff", "rolling"),
    }
)
"""The operations that add a column beside the ones there (`set_type` only with a `name` of its own)."""


def added_columns(
    operations: Sequence[Operation], before: Collection[str], after: Collection[str], made: Collection[str]
) -> dict[str, str]:
    """The new columns of a call that an operation added beside the others, each with that operation's name, a closed
    word: what the guard's log line says about a column, never its name. `before` and `after` are the column names of
    the tables the call started from and left; `made` are the call's own `made_columns`, among them a `date_number`'s
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


def renamed(names: Sequence[str], operations: Sequence[Operation]) -> list[str]:
    """`names` after the `rename` operations of a call, in their order: a column of row numbers the call renames
    still holds them."""
    current = list(names)
    for operation in operations:
        if isinstance(operation, Rename):
            current = [operation.name if name == operation.column else name for name in current]
    return current


def open_roles(
    before: list[Binding],
    roles: list[DataRole],
    previous: DatasetProfile,
    profile: DatasetProfile,
    hidden: Collection[str],
) -> list[str]:
    """The required roles a change of the data leaves open, as the carry (`carry_bindings`) of `before`, the bindings
    on `previous`, leaves them on `profile` with the columns named in `hidden` left out."""
    shown = profile.model_copy(update={"columns": [column for column in profile.columns if column.name not in hidden]})
    return check_bindings(carry_bindings(before, roles, shown, previous), roles, shown).missing_roles


def emptied(
    before: list[Binding], roles: list[DataRole], previous: DatasetProfile, open_now: Collection[str]
) -> list[Emptied]:
    """The roles of `open_now` (`open_roles`: open after a change, its fills hidden) that `before`, the bindings on
    `previous`, held.

    A role open before the change is none of them: it was not this change's doing. A role the carry fills with a column
    that is not hidden (a rename's, an aggregate's own, a free column that fits) is not open and is none either."""
    open_before = set(check_bindings(before, roles, previous).missing_roles)
    held: dict[str, str] = {}
    for binding in before:
        role = resolve_role(binding.role, roles)
        if role is not None:
            held.setdefault(role.name, binding.column)
    return [Emptied(name, held[name]) for name in open_now if name not in open_before and name in held]


def held_bindings(bindings: Sequence[Binding], before: Collection[Binding], made: Collection[str]) -> list[Binding]:
    """The bindings of `bindings` that put a column of `made` on a role that `before` did not bind to it."""
    return [binding for binding in bindings if binding.column in made and binding not in before]
