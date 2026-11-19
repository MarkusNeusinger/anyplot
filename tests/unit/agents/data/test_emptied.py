"""The pure parts of the guard on a taken role (`agents/anyplot/data/emptied.py`)."""

from pydantic import TypeAdapter

from agents.anyplot.data.emptied import held_columns, renamed, replaces, taken, wrong_bindings
from agents.anyplot.data.prepare import Operation
from agents.anyplot.schemas import Binding


OPERATIONS = TypeAdapter(list[Operation])


def test_held_columns_are_the_new_date_numbers_with_their_source_and_the_new_row_numbers() -> None:
    held = held_columns(["Tage"], ["Nr"], {"Tage": "Datum", "Nr": "Nr"}, before={"Datum", "Wert"})

    assert held == {"Tage": "Datum", "Nr": None}


def test_a_row_number_column_the_table_already_had_is_no_held_column() -> None:
    """`row_number` reuses a column of that name that already numbers the rows: nothing was made."""
    assert held_columns([], ["index"], {}, before={"index", "Wert"}) == {}


def test_the_turns_start_follows_a_rename_so_a_renamed_column_is_not_taken() -> None:
    operations = OPERATIONS.validate_python([{"op": "rename", "column": "Feuchte", "name": "Humidity"}])
    start = {"x": "Temperatur", "y": renamed("Feuchte", operations)}

    assert taken(start, {"Temperatur", "Humidity"}) == {}
    assert taken(start, {"Temperatur"}) == {"y": "Humidity"}


def test_a_date_number_replaces_only_the_role_whose_own_column_it_was_made_from() -> None:
    held: dict[str, str | None] = {"Tage": "Datum", "Nr": None}
    taken_roles = {"x": "Datum", "y": "Wert"}

    assert replaces("Tage", "x", held, taken_roles)
    assert not replaces("Tage", "y", held, taken_roles) and not replaces("Nr", "x", held, taken_roles)
    bindings = [Binding(role="x", column="Tage"), Binding(role="y", column="Tage"), Binding(role="color", column="Nr")]
    # Only taken roles count: a held column on a role whose column is still there is no wrong binding.
    assert wrong_bindings(bindings, held, taken_roles) == [Binding(role="y", column="Tage")]
