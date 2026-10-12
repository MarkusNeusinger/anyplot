"""Tests for agents/anyplot/data/shape.py: the wide-table suggestion against real spec roles."""

from pydantic import TypeAdapter

from agents.anyplot.data.bindings import default_bindings
from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.data.prepare import Operation, apply_operations
from agents.anyplot.data.shape import long_suggestion
from agents.anyplot.dev_fixture import snapshot_from_repo


# The owner's paste of 2026-10-12 on box-basic: three sensors side by side.
SENSORS = "Sensor_A,Sensor_B,Sensor_C\n51.74,58.12,41.05\n48.65,53.40,62.88\n50.23,55.91,47.30\n"


def roles(spec_id: str):
    return snapshot_from_repo(spec_id, "matplotlib").roles()


def suggest(spec_id: str, text: str):
    return long_suggestion(roles(spec_id), parse_dataset(text).profile)


class TestSuggestion:
    def test_the_owners_sensor_table_on_a_box_plot(self) -> None:
        suggestion = suggest("box-basic", SENSORS)

        assert suggestion is not None
        assert suggestion.operation() == {
            "op": "pivot_longer",
            "columns": ["Sensor_A", "Sensor_B", "Sensor_C"],
            "names_to": "category",
            "values_to": "value",
        }
        assert (suggestion.keys, suggestion.rows) == ([], 9)
        assert suggestion.body()["kind"] == "to_long"

    def test_applied_it_gives_the_long_table_and_both_bindings(self) -> None:
        suggestion = suggest("box-basic", SENSORS)
        assert suggestion is not None
        operations = TypeAdapter(list[Operation]).validate_python([suggestion.operation()])

        prepared = apply_operations(parse_dataset(SENSORS), operations)
        parsed = parse_dataset(prepared.csv, text_columns=prepared.text_columns)

        assert prepared.csv.splitlines()[:4] == ["category,value", "Sensor_A,51.74", "Sensor_A,48.65", "Sensor_A,50.23"]
        bound = {binding.role: binding.column for binding in default_bindings(roles("box-basic"), parsed.profile)}
        assert bound == {"category": "category", "value": "value"}
        assert long_suggestion(roles("box-basic"), parsed.profile) is None  # long now: no second offer

    def test_other_long_data_specs_get_it_too(self) -> None:
        for spec_id in ("violin-basic", "strip-basic"):
            assert suggest(spec_id, SENSORS) is not None, spec_id

    def test_a_date_key_is_kept(self) -> None:
        text = "Datum,Sensor_A,Sensor_B\n2024-01-01,1.5,2.5\n2024-01-02,1.7,2.1\n"

        suggestion = suggest("box-basic", text)

        assert suggestion is not None
        assert (suggestion.columns, suggestion.keys, suggestion.rows) == (["Sensor_A", "Sensor_B"], ["Datum"], 4)


class TestNoSuggestion:
    def test_a_scatter_wants_two_numbers(self) -> None:
        assert suggest("scatter-basic", "x,y\n1,2\n3,4\n") is None

    def test_already_long_data(self) -> None:
        assert suggest("box-basic", "group,score\nA,1\nB,2\nA,3\n") is None

    def test_a_label_column_is_the_users_choice(self) -> None:
        assert suggest("box-basic", "Region,Q1,Q2\nNord,1,2\nSüd,3,4\n") is None

    def test_a_variadic_family_takes_wide_data_as_it_is(self) -> None:
        assert suggest("line-multi", "x,a,b\n1,2,3\n2,3,4\n") is None

    def test_two_required_labels_would_leave_one_open(self) -> None:
        assert suggest("box-grouped", SENSORS) is None

    def test_one_numeric_column_is_not_wide(self) -> None:
        assert suggest("box-basic", "Sensor_A\n1\n2\n") is None
