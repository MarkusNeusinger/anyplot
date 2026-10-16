"""Tests for agents/anyplot/data/shape.py: the wide-table suggestion against real spec roles."""

from pydantic import TypeAdapter

from agents.anyplot.data.bindings import default_bindings, filled_bindings, label_siblings
from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.data.prepare import Operation, apply_operations
from agents.anyplot.data.shape import long_names, long_suggestion
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
            "names_to": "Category",
            "values_to": "Value",
        }
        assert (suggestion.keys, suggestion.rows) == ([], 9)
        assert suggestion.body()["kind"] == "to_long"

    def test_applied_it_gives_the_long_table_and_both_bindings(self) -> None:
        suggestion = suggest("box-basic", SENSORS)
        assert suggestion is not None
        operations = TypeAdapter(list[Operation]).validate_python([suggestion.operation()])

        prepared = apply_operations(parse_dataset(SENSORS), operations)
        parsed = parse_dataset(prepared.csv, text_columns=prepared.text_columns)

        assert prepared.csv.splitlines()[:4] == ["Category,Value", "Sensor_A,51.74", "Sensor_A,48.65", "Sensor_A,50.23"]
        bound = {binding.role: binding.column for binding in default_bindings(roles("box-basic"), parsed.profile)}
        assert bound == {"category": "Category", "value": "Value"}
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
            "names_to": "Weekday",
            "values_to": "Value",
        }
        assert (suggestion.keys, suggestion.rows) == (["Stunde"], 28)

    def test_applied_it_binds_every_role(self) -> None:
        suggestion = suggest("heatmap-basic", VISITORS)
        assert suggestion is not None
        operations = TypeAdapter(list[Operation]).validate_python([suggestion.operation()])

        prepared = apply_operations(parse_dataset(VISITORS), operations)
        parsed = parse_dataset(prepared.csv, text_columns=prepared.text_columns)

        assert prepared.csv.splitlines()[:2] == ["Stunde,Weekday,Value", "08:00,Mo,42"]
        bound = {binding.role: binding.column for binding in default_bindings(roles("heatmap-basic"), parsed.profile)}
        assert bound == {"x": "Stunde", "y": "Weekday", "value": "Value"}
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

    def test_a_second_time_key_is_no_measurement(self) -> None:
        """Review of #12204: `Year` beside the row labels would have been melted with `A`, `B`, `C`."""
        text = "Region,Year,A,B,C\nNord,2025,1,2,3\nSüd,2025,4,5,6\nOst,2025,7,8,9\n"

        assert suggest("heatmap-basic", text) is None

    def test_grouped_charts_get_it_flows_hierarchies_and_codes_do_not(self) -> None:
        """Review of #12204: melting a wide table into a flow's target or a party's color means nothing."""
        for spec_id in ("box-grouped", "bar-grouped", "bar-stacked", "heatmap-annotated"):
            assert suggest(spec_id, VISITORS) is not None, spec_id
        for spec_id in ("sankey-basic", "chord-basic", "icicle-basic", "sunburst-basic", "parliament-basic"):
            assert suggest(spec_id, VISITORS) is None, spec_id


class TestTimeKeys:
    """Review of #12204: a column of years is a key the offer keeps, as the bindings treat it."""

    def test_a_country_beside_one_row_per_year_is_no_quarter(self) -> None:
        """Fable's re-review: `CH` of 1 to 4 right after `Jahr` was taken for a quarter and kept as a key."""
        suggestion = suggest("box-basic", "Jahr,CH,AT,DE\n2000,1,2,3\n2001,2,3,4\n2002,3,4,5\n2003,4,5,6\n")

        assert suggestion is not None and (suggestion.columns, suggestion.keys) == (["CH", "AT", "DE"], ["Jahr"])

    def test_a_numbering_first_column_is_kept(self) -> None:
        text = "id,a,b,c\n" + "".join(f"{i},{i * 2},{i * 3},{i * 5}\n" for i in range(100, 110))

        suggestion = suggest("box-basic", text)

        assert suggestion is not None and (suggestion.columns, suggestion.keys) == (["a", "b", "c"], ["id"])

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


class TestLongNames:
    """Live test round 8 of 2026-10-16: the role names `y` and `value` became the title "Wert nach Wochentag und
    Stunde"; the new columns are named after what the melted headers are, in English whatever the session
    language, so the offer the page shows never changes under it (review of #12206)."""

    ROLES = ("category", "value")

    def test_the_names_column_says_what_the_headers_are(self) -> None:
        assert long_names(["Mo", "Di", "Mi", "Do", "Fr"], [], self.ROLES) == ("Weekday", "Value")
        assert long_names(["Monday", "Tuesday", "Wednesday"], [], self.ROLES) == ("Weekday", "Value")
        assert long_names(["Jan", "Feb", "März"], [], self.ROLES) == ("Month", "Value")
        assert long_names(["2019", "2020", "2021"], ["Region"], self.ROLES) == ("Year", "Value")
        assert long_names(["Sensor_A", "Mo", "Di"], [], self.ROLES) == ("Category", "Value")
        assert long_names(["Mo", "Mo.", "Di"], [], self.ROLES) == ("Category", "Value")  # two distinct days only

    def test_a_name_an_input_column_has_gives_way(self) -> None:
        """Review of #12206: `Value,Other` melted into `Value` made pandas' `melt` raise, a 500 on `.to_long()`."""
        assert long_names(["Value", "Other"], [], self.ROLES) == ("Category", "Value 2")  # case-insensitive
        assert long_names(["Other", "Weight"], ["Value"], ("y", "value")) == ("Category", "Value 2")
        assert long_names(["value", "Other"], ["Category"], self.ROLES) == ("Category 2", "Value 2")
        assert long_names(["2019", "2020", "2021"], ["year"], ("y", "value")) == ("y", "Value")

    def test_names_never_decide_the_offer_and_the_route_never_fails_on_them(self) -> None:
        for text in ("Value,Other\n1.5,2.5\n3.5,4.5\n", "value,Category\n1.5,2.5\n3.5,4.5\n"):
            suggestion = suggest("box-basic", text)
            assert suggestion is not None, text
            operations = TypeAdapter(list[Operation]).validate_python([suggestion.operation()])
            header = apply_operations(parse_dataset(text), operations).csv.splitlines()[0]
            assert header == f"{suggestion.names_to},{suggestion.values_to}"

    def test_the_binding_warning_sees_every_table_the_page_offers(self) -> None:
        """Review of #12206: with names that decided the offer, a table whose headers took the names was offered
        in one language while `label_siblings` (no language) found no wide table and warned about nothing."""
        text = "y,Value,A,B\nr1,1,2,3\nr2,4,5,6\nr3,7,8,9\n"
        profile = parse_dataset(text).profile

        assert suggest("heatmap-basic", text) is not None
        assert label_siblings(roles("heatmap-basic"), profile) == ["Value", "A", "B"]

    def test_the_new_columns_keep_the_roles_they_are_made_for_whatever_their_names(self) -> None:
        """`Category` would take bar-grouped's `category` by its name; the headers are meant for its `group`."""
        text = "Region,Alpha,Beta,Gamma\nNord,1,2,3\nSüd,5,6,7\nOst,9,1,2\n"
        suggestion = suggest("bar-grouped", text)
        assert suggestion is not None and suggestion.names_to == "Category"
        operations = TypeAdapter(list[Operation]).validate_python([suggestion.operation()])
        prepared = apply_operations(parse_dataset(text), operations)
        parsed = parse_dataset(prepared.csv, text_columns=prepared.text_columns)

        pinned = filled_bindings(suggestion.bindings(), roles("bar-grouped"), parsed.profile)

        assert {binding.role: binding.column for binding in pinned} == {
            "category": "Region",
            "group": "Category",
            "value": "Value",
        }
        by_name = {binding.role: binding.column for binding in default_bindings(roles("bar-grouped"), parsed.profile)}
        assert by_name["category"] == "Category"  # what the names alone would have bound
