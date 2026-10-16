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


class TestMatrix:
    """Live test round 7 of 2026-10-16: a heatmap of visitors per hour and weekday, pasted wide."""

    def test_the_wide_heatmap_gets_the_long_form_with_its_row_labels_kept(self) -> None:
        suggestion = suggest("heatmap-basic", VISITORS)

        assert suggestion is not None
        assert suggestion.operation() == {
            "op": "pivot_longer",
            "columns": ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"],
            "names_to": "y",
            "values_to": "value",
        }
        assert (suggestion.keys, suggestion.rows) == (["Stunde"], 28)

    def test_applied_it_binds_every_role(self) -> None:
        suggestion = suggest("heatmap-basic", VISITORS)
        assert suggestion is not None
        operations = TypeAdapter(list[Operation]).validate_python([suggestion.operation()])

        prepared = apply_operations(parse_dataset(VISITORS), operations)
        parsed = parse_dataset(prepared.csv, text_columns=prepared.text_columns)

        assert prepared.csv.splitlines()[:2] == ["Stunde,y,value", "08:00,Mo,42"]
        bound = {binding.role: binding.column for binding in default_bindings(roles("heatmap-basic"), parsed.profile)}
        assert bound == {"x": "Stunde", "y": "y", "value": "value"}
        assert long_suggestion(roles("heatmap-basic"), parsed.profile) is None

    def test_long_heatmap_data_with_an_integer_key_stays(self) -> None:
        text = "day,hour,count\n" + "".join(f"{day},{hour},{hour * 2}\n" for day in ("Mon", "Tue") for hour in (9, 10))

        assert suggest("heatmap-basic", text) is None

    def test_row_labels_that_repeat_are_no_matrix(self) -> None:
        assert suggest("heatmap-basic", "label,a,b,c\nA,1,2,3\nA,4,5,6\nB,7,8,9\n") is None

    def test_two_number_columns_are_no_matrix(self) -> None:
        assert suggest("heatmap-basic", "label,a,b\nA,1,2\nB,4,5\nC,7,8\n") is None

    def test_an_hour_column_of_whole_numbers_is_the_row_key(self) -> None:
        text = "Stunde;Mo;Di;Mi\n8;42;35;35\n9;48;39;43\n10;46;53;56\n11;55;44;64\n"

        suggestion = suggest("heatmap-basic", text)

        assert suggestion is not None and (suggestion.keys, suggestion.columns) == (["Stunde"], ["Mo", "Di", "Mi"])

    def test_a_date_column_is_the_row_key(self) -> None:
        text = "Datum,A,B,C\n2025-01-01,1,2,3\n2025-01-02,4,5,6\n2025-01-03,7,8,9\n"

        suggestion = suggest("heatmap-basic", text)

        assert suggestion is not None and suggestion.keys == ["Datum"]

    def test_grouped_charts_get_it_flows_hierarchies_and_codes_do_not(self) -> None:
        """Review of #12204: melting a wide table into a flow's target or a party's color means nothing."""
        for spec_id in ("box-grouped", "bar-grouped", "bar-stacked", "heatmap-annotated"):
            assert suggest(spec_id, VISITORS) is not None, spec_id
        for spec_id in ("sankey-basic", "chord-basic", "icicle-basic", "sunburst-basic", "parliament-basic"):
            assert suggest(spec_id, VISITORS) is None, spec_id


class TestTimeKeys:
    """Review of #12204: a column of years is a key the offer keeps, as the bindings treat it."""

    def test_a_year_column_is_kept_not_melted(self) -> None:
        suggestion = suggest("box-basic", "Jahr,CO2,Bevoelkerung\n2000,43.6,7184003\n2001,45.1,7226391\n")

        assert suggestion is not None
        assert (suggestion.columns, suggestion.keys) == (["CO2", "Bevoelkerung"], ["Jahr"])


# Four rows of the owner's paste of round 7.
VISITORS = (
    "Stunde;Mo;Di;Mi;Do;Fr;Sa;So\n"
    "08:00;42;35;35;46;32;48;40\n"
    "09:00;48;39;43;51;38;61;41\n"
    "10:00;46;53;56;57;51;57;57\n"
    "11:00;55;44;64;60;60;63;68\n"
)


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
