"""The pure parts of the guard on a taken role (`agents/anyplot/data/emptied.py`)."""

from pydantic import TypeAdapter

from agents.anyplot.data.bindings import Misfit, check_bindings
from agents.anyplot.data.emptied import (
    date_misfits,
    held_columns,
    renamed,
    replaces,
    start_columns,
    taken,
    wrong_bindings,
)
from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.data.prepare import Operation
from agents.anyplot.schemas import Binding
from core.spec_roles import DataRole


OPERATIONS = TypeAdapter(list[Operation])
ROLES = [
    DataRole(name="x", kinds=("datetime", "numeric"), required=True, variadic=False, description="the time"),
    DataRole(name="y", kinds=("numeric",), required=True, variadic=True, description="one series per member"),
    DataRole(name="series", kinds=("categorical",), required=False, variadic=False, description="the groups"),
    DataRole(name="band", kinds=("numeric",), required=True, variadic=False, description="a band", computed=True),
]
"""A multi-series line: x, the family y (`y1`, `y2`, ...), an optional series and a band the plot computes."""
SCATTER = [
    DataRole(name="x", kinds=("numeric",), required=True, variadic=False, description="x"),
    DataRole(name="y", kinds=("numeric",), required=True, variadic=False, description="y"),
]


def test_held_columns_are_the_new_date_numbers_with_their_source_and_the_new_row_numbers() -> None:
    held = held_columns(["Tage"], ["Nr"], {"Tage": "Datum", "Nr": "Nr"}, before={"Datum", "Wert"})

    assert held == {"Tage": "Datum", "Nr": None}


def test_a_row_number_column_the_table_already_had_is_no_held_column() -> None:
    """`row_number` reuses a column of that name that already numbers the rows: nothing was made."""
    assert held_columns([], ["index"], {}, before={"index", "Wert"}) == {}


def test_the_start_keeps_the_required_roles_with_a_familys_members_together() -> None:
    """An optional role and one the plot computes are no part of the start: they never make a turn a taken turn."""
    bindings = [
        Binding(role="x", column="Datum"),
        Binding(role="y1", column="A"),
        Binding(role="series", column="Gruppe"),
        Binding(role="y2", column="B"),
        Binding(role="band", column="Band"),
    ]

    assert start_columns(bindings, ROLES) == {"x": ["Datum"], "y": ["A", "B"]}


def test_the_turns_start_follows_a_rename_so_a_renamed_column_is_not_taken() -> None:
    operations = OPERATIONS.validate_python([{"op": "rename", "column": "Feuchte", "name": "Humidity"}])
    start = {"x": ["Temperatur"], "y": [renamed("Feuchte", operations)]}

    assert taken(start, {"Temperatur", "Humidity"}) == {}
    assert taken(start, {"Temperatur"}) == {"y": ["Humidity"]}


def test_a_family_is_taken_only_when_none_of_its_series_is_left() -> None:
    start = {"x": ["Datum"], "y": ["A", "B", "C"]}

    assert taken(start, {"Datum", "B", "C"}) == {}
    assert taken(start, {"Datum", "C"}) == {}
    assert taken(start, {"Datum", "Wert"}) == {"y": ["A", "B", "C"]}


def test_a_date_number_replaces_only_the_role_whose_own_column_it_was_made_from() -> None:
    held: dict[str, str | None] = {"Tage": "Datum", "Nr": None}
    taken_roles = {"x": ["Datum"], "y": ["Wert"]}

    assert replaces("Tage", "x", held, taken_roles, SCATTER)
    assert not replaces("Tage", "y", held, taken_roles, SCATTER) and not replaces("Nr", "x", held, taken_roles, SCATTER)
    bindings = [Binding(role="x", column="Tage"), Binding(role="y", column="Tage"), Binding(role="color", column="Nr")]
    # Only taken roles count: a held column on a role whose column is still there is no wrong binding.
    assert wrong_bindings(bindings, held, taken_roles, SCATTER) == [Binding(role="y", column="Tage")]


def test_a_member_is_judged_by_its_family_whatever_its_number() -> None:
    """The family y held A and B at the start and lost both: `y4` belongs to it as `y1` does, so the row numbers land
    on no member, and a date number made from one of its own columns replaces it on any member."""
    held: dict[str, str | None] = {"Nr": None, "Tage": "B"}
    taken_roles = {"y": ["A", "B"]}
    bindings = [Binding(role="x", column="Datum"), Binding(role="y4", column="Nr"), Binding(role="y1", column="Tage")]

    assert wrong_bindings(bindings, held, taken_roles, ROLES) == [Binding(role="y4", column="Nr")]
    assert replaces("Tage", "y3", held, taken_roles, ROLES) and replaces("Tage", "y", held, taken_roles, ROLES)
    # An optional role is never taken, so a held column on it is no wrong binding either.
    assert wrong_bindings([Binding(role="series", column="Nr")], held, taken_roles, ROLES) == []


def test_a_date_column_refused_on_a_number_role_is_a_date_misfit_and_nothing_else_is() -> None:
    """The second trigger reads the typed record of the refusal, by the spec's role (`y2` is `y`), never its line."""
    table = parse_dataset("Datum,Wert,Name\n2026-03-01,1.5,a\n2026-03-02,2.5,b\n").profile
    bindings = [
        Binding(role="x", column="Wert"),
        Binding(role="y2", column="Datum"),
        Binding(role="series", column="Wert"),
    ]

    check = check_bindings(bindings, ROLES, table)

    assert check.misfits == [
        Misfit("y2", "Datum", "datetime", ("numeric",)),
        Misfit("series", "Wert", "number", ("categorical",)),
    ]
    assert len(check.errors) == 2
    # A number column on a role that takes labels is a misfit too, but not a date on a number role.
    assert date_misfits(check.misfits, ROLES) == {"y": "Datum"}


def test_a_role_that_takes_dates_too_never_refuses_one() -> None:
    table = parse_dataset("Datum,Wert\n2026-03-01,1.5\n2026-03-02,2.5\n").profile

    check = check_bindings([Binding(role="x", column="Datum"), Binding(role="y1", column="Wert")], ROLES, table)

    assert check.misfits == [] and date_misfits(check.misfits, ROLES) == {}
    assert date_misfits(check_bindings([Binding(role="x", column="Datum")], SCATTER, table).misfits, SCATTER) == {
        "x": "Datum"
    }
