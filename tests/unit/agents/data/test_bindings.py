"""Tests for agents/anyplot/data/bindings.py: default bindings and their validation."""

import pytest
from pydantic import TypeAdapter

from agents.anyplot.data.bindings import (
    MAX_VARIADIC_DEFAULT,
    accepts,
    carry_bindings,
    check_bindings,
    default_bindings,
    name_similarity,
    resolve_role,
)
from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.data.prepare import Operation, apply_operations
from agents.anyplot.data.roles import DataRole, RoleKind, parse_roles
from agents.anyplot.schemas import Binding, ColumnDtype, DatasetProfile
from tests.unit.agents.data.test_roles import AREA_STACKED, LINE_MULTI


OPERATIONS = TypeAdapter(list[Operation])


def profile(csv: str) -> DatasetProfile:
    return parse_dataset(csv).profile


def role(name: str, *kinds: RoleKind, required: bool = True, variadic: bool = False) -> DataRole:
    return DataRole(name=name, kinds=kinds, required=required, variadic=variadic, description="")


def as_pairs(bindings: list[Binding]) -> list[tuple[str, str]]:
    return [(binding.role, binding.column) for binding in bindings]


def bind(*pairs: tuple[str, str]) -> list[Binding]:
    return [Binding(role=role_name, column=column) for role_name, column in pairs]


class TestDefaultBindingsOnRealSpecs:
    def test_area_stacked_wide(self) -> None:
        roles = parse_roles(AREA_STACKED)
        data = profile("month,Shoes,Hats,Bags\n2024-01-01,1.5,2,3\n2024-02-01,1,2,3\n")
        bindings = default_bindings(roles, data)

        assert as_pairs(bindings) == [("x", "month"), ("y1", "Shoes"), ("y2", "Hats"), ("y3", "Bags")]
        # Wide data has no category column, and the bullet does not say "optional".
        assert check_bindings(bindings, roles, data).missing_roles == ["category"]

    def test_area_stacked_long(self) -> None:
        roles = parse_roles(AREA_STACKED)
        data = profile("month,product,revenue\n2024-01-01,Shoes,1.5\n2024-01-01,Hats,2\n")
        bindings = default_bindings(roles, data)

        assert as_pairs(bindings) == [("x", "month"), ("y1", "revenue"), ("category", "product")]
        assert check_bindings(bindings, roles, data).complete

    def test_line_multi_prefers_the_date_column_for_x(self) -> None:
        roles = parse_roles(LINE_MULTI)
        data = profile("a,date,b,c\n1,2024-01-01,2,3\n4,2024-01-02,5,6\n")
        bindings = default_bindings(roles, data)

        assert as_pairs(bindings) == [("x", "date"), ("y1", "a"), ("y2", "b"), ("y3", "c")]
        check = check_bindings(bindings, roles, data)
        assert check.complete
        assert check.missing_roles == []

    def test_line_multi_without_dates_uses_the_first_number_for_x(self) -> None:
        roles = parse_roles(LINE_MULTI)
        data = profile("step,a,b\n1,0.5,0.7\n2,0.6,0.8\n")

        assert as_pairs(default_bindings(roles, data)) == [("x", "step"), ("y1", "a"), ("y2", "b")]

    def test_line_multi_long(self) -> None:
        roles = parse_roles(LINE_MULTI)
        data = profile("date,company,price\n2024-01-01,A,10.5\n2024-01-01,B,11\n")
        bindings = default_bindings(roles, data)

        assert as_pairs(bindings) == [("x", "date"), ("y1", "price"), ("series", "company")]
        assert check_bindings(bindings, roles, data).complete

    def test_line_multi_never_groups_by_a_single_valued_column(self) -> None:
        # A statistics-office export: a text column with one value (the region) before the one that varies.
        roles = parse_roles(LINE_MULTI)
        data = profile("Year,Region,Group,Count\n2020,All,A,10\n2020,All,B,12\n2021,All,A,11\n2021,All,B,13\n")

        assert dict(as_pairs(default_bindings(roles, data)))["series"] == "Group"


BAR_BASIC = [
    "`category` (categorical) - Labels for each bar on the x-axis",
    "`value` (numeric) - Heights of the bars representing the measured quantity",
]
# Live test round 2 of 2026-10-15: before the parse read the thousands dots, `Bevölkerung` was a text column;
# mixed number formats keep it text here.
CH_CO2_TEXT_POPULATION = (
    "Jahr,CO2 (Mio. t),CO2 pro Kopf (t),Bevölkerung\n"
    "2000,43.621,6.07,7.184.003\n2001,45.085,6.24,7226391.5\n2002,43.467,5.97,7.278.744\n"
)


class TestCategoryAndMeasureRanking:
    """A category role takes a real category or the year; a value role takes a measure, never the year."""

    def test_bar_basic_on_the_swiss_co2_paste(self) -> None:
        from tests.unit.agents.data.test_parse import CH_CO2_DE

        data = profile(CH_CO2_DE)

        assert as_pairs(default_bindings(parse_roles(BAR_BASIC), data)) == [
            ("category", "Jahr"),
            ("value", "CO2 (Mio. t)"),
        ]

    def test_a_text_column_of_numbers_ranks_after_the_year(self) -> None:
        data = profile(CH_CO2_TEXT_POPULATION)

        assert dict(as_pairs(default_bindings(parse_roles(BAR_BASIC), data)))["category"] == "Jahr"

    def test_a_real_category_still_comes_first(self) -> None:
        data = profile("year,country,co2\n2023,Austria,6.2\n2023,Germany,7.0\n2023,France,4.1\n")

        assert as_pairs(default_bindings(parse_roles(BAR_BASIC), data)) == [("category", "country"), ("value", "co2")]

    def test_a_category_of_too_many_values_ranks_after_the_year(self) -> None:
        rows = "".join(f"{2000 + i % 10},id-{i},{i}.5\n" for i in range(80))
        data = profile("year,id,amount\n" + rows)

        assert dict(as_pairs(default_bindings(parse_roles(BAR_BASIC), data)))["category"] == "year"

    def test_the_value_role_skips_a_year_column_for_a_measure(self) -> None:
        roles = [role("value", "numeric")]
        data = profile("Jahr,Einwohner\n2020,8670300\n2021,8738800\n")

        assert as_pairs(default_bindings(roles, data)) == [("value", "Einwohner")]

    def test_a_named_year_ranks_after_a_value_that_only_looks_like_years(self) -> None:
        roles = [role("value", "numeric")]
        data = profile("year,price\n2020,1250\n2021,1310\n")

        assert as_pairs(default_bindings(roles, data)) == [("value", "price")]

    def test_prices_in_the_year_range_are_measures(self) -> None:
        # Review of 2026-10-15: a price of 1000 to 2200 scored as a year and lost the value role to the quantity.
        data = profile("Produkt;Preis;Menge\nA;1250;3\nB;1400;5\nC;1990;2\n")

        assert as_pairs(default_bindings(parse_roles(BAR_BASIC), data)) == [("category", "Produkt"), ("value", "Preis")]

    def test_an_unnamed_run_of_whole_years_still_counts(self) -> None:
        roles = [role("value", "numeric")]
        data = profile("t,amount\n2019,7\n2020,9\n2021,8\n")

        assert as_pairs(default_bindings(roles, data)) == [("value", "amount")]

    def test_a_quarter_ranks_before_a_measure_in_the_year_range_as_category(self) -> None:
        roles = [role("category", "categorical")]
        data = profile("Umsatz,Quartal\n1250,1\n1400,2\n1990,3\n1700,4\n")

        assert as_pairs(default_bindings(roles, data)) == [("category", "Quartal")]

    def test_name_similarity_decides_before_the_year_rank(self) -> None:
        roles = [role("value", "numeric")]
        data = profile("Jahr,amount,value_eur\n2020,3.5,1.5\n2021,4.5,2.5\n2022,5.5,3.5\n")

        assert as_pairs(default_bindings(roles, data)) == [("value", "value_eur")]

    def test_a_time_axis_prefers_the_year_among_numbers(self) -> None:
        roles = [role("x", "datetime", "numeric"), role("y", "numeric")]
        data = profile("population,year\n7.5,2020\n7.6,2021\n")

        assert as_pairs(default_bindings(roles, data)) == [("x", "year"), ("y", "population")]

    def test_a_year_column_is_the_category_of_a_wide_table(self) -> None:
        roles = [role("category", "categorical"), role("y", "numeric", variadic=True)]
        data = profile("Jahr,Shoes,Hats\n2020,1,2\n2021,3,4\n")

        assert as_pairs(default_bindings(roles, data)) == [("category", "Jahr"), ("y1", "Shoes"), ("y2", "Hats")]


# Generalised from the live tests of 2026-10-15 (a World Bank API download, a MeteoSwiss monthly series):
# a long table with a code and a name column of the same countries and a constant number column.
INDICATOR = (
    "country.id,country.value,countryiso3code,date,value,decimal\n"
    "AT,Austria,AUT,2020,81.2,0\n"
    "AT,Austria,AUT,2021,81.3,0\n"
    "CH,Switzerland,CHE,2020,83.0,0\n"
    "CH,Switzerland,CHE,2021,83.9,0\n"
    "DE,Germany,DEU,2020,81.0,0\n"
    "DE,Germany,DEU,2021,80.9,0\n"
)
ROLLING = [
    "`date` (datetime) - Timestamp values representing points in time",
    "`value` (numeric) - Raw measurements or observations at each timestamp",
    "`rolling_avg` (numeric) - Computed rolling average (e.g., 7-day, 30-day window)",
]


def monthly(header: str, years: int = 2) -> str:
    """`Year`, a month 1 to 12 and two measures, `years` years long, with the given header."""
    lines = [header]
    for year in range(2020, 2020 + years):
        lines.extend(f"{year},{month},{month * 1.5 - 4:.1f},{40 + month * 3}.5" for month in range(1, 13))
    return "\n".join(lines) + "\n"


class TestWeakMeasures:
    def test_a_constant_column_never_joins_a_number_family(self) -> None:
        roles = parse_roles(LINE_MULTI)
        bindings = default_bindings(roles, profile(INDICATOR))

        assert ("y1", "value") in as_pairs(bindings)
        assert all(binding.column != "decimal" for binding in bindings)

    def test_a_required_family_takes_a_weak_column_rather_than_none(self) -> None:
        roles = [role("y", "numeric", variadic=True), role("group", "categorical")]
        data = profile("group,flag\na,0\nb,0\nc,0\nd,0\ne,0\n")

        assert as_pairs(default_bindings(roles, data)) == [("y1", "flag"), ("group", "group")]

    def test_a_constant_measure_ranks_last_for_a_single_role(self) -> None:
        roles = [role("x", "numeric")]
        data = profile("level,value\n1.5,2.5\n1.5,3.5\n1.5,4.5\n1.5,5.5\n1.5,6.5\n")

        assert as_pairs(default_bindings(roles, data)) == [("x", "value")]

    def test_an_optional_measure_stays_open_rather_than_take_a_weak_column(self) -> None:
        roles = [role("x", "numeric"), role("y", "numeric"), role("size", "numeric", required=False)]
        data = profile("a,b,unit_code\n1,2.5,7\n2,3.5,7\n3,1.5,7\n4,2.0,7\n5,4.5,7\n")

        assert as_pairs(default_bindings(roles, data)) == [("x", "a"), ("y", "b")]

    def test_a_constant_named_like_a_member_or_a_role_is_still_skipped(self) -> None:
        roles = [role("x", "numeric"), role("y", "numeric", variadic=True), role("size", "numeric", required=False)]
        data = profile("x,y1,y2,size\n1,2.5,0,7\n2,3.5,0,7\n3,1.5,0,7\n4,2.0,0,7\n5,4.5,0,7\n")

        assert as_pairs(default_bindings(roles, data)) == [("x", "x"), ("y1", "y1")]

    def test_a_year_named_like_the_role_is_meant(self) -> None:
        roles = [role("year", "numeric"), role("value", "numeric")]
        data = profile("year,value\n2020,1.5\n2021,2.5\n2022,3.5\n")

        assert as_pairs(default_bindings(roles, data)) == [("year", "year"), ("value", "value")]

    def test_a_short_table_keeps_a_one_valued_year_named_like_the_role(self) -> None:
        roles = [role("year", "numeric"), role("measurement", "numeric")]
        data = profile("year,value\n2024,1.5\n2024,2.5\n")

        assert as_pairs(default_bindings(roles, data)) == [("year", "year"), ("measurement", "value")]

    def test_an_optional_measure_still_takes_a_real_measure(self) -> None:
        roles = [role("x", "numeric"), role("y", "numeric"), role("size", "numeric", required=False)]
        data = profile("a,b,c\n1,2.5,7\n2,3.5,8\n3,1.5,9\n4,2.0,7\n5,4.5,8\n")

        assert as_pairs(default_bindings(roles, data)) == [("x", "a"), ("y", "b"), ("size", "c")]

    def test_a_month_column_is_no_value_of_a_time_series(self) -> None:
        roles = parse_roles(ROLLING)
        data = profile(monthly("Year,Month,Temperature,Precipitation"))

        # No column is named like a rolling average, so the plot computes `rolling_avg` (owner decision of 2026-10-15).
        assert as_pairs(default_bindings(roles, data)) == [("value", "Temperature")]

    @pytest.mark.parametrize("name", ["Monat", "month_no", "Quartal", "Woche", "weekOfYear"])
    def test_a_named_date_part_is_weak(self, name: str) -> None:
        roles = [role("value", "numeric")]
        data = profile(f"{name},Messwert\n1,2.5\n2,3.5\n3,1.5\n")

        assert as_pairs(default_bindings(roles, data)) == [("value", "Messwert")]

    @pytest.mark.parametrize(
        "name", ["Dauer (Minuten)", "Days to ship", "kW", "Months since start", "Tag", "hour", "Stunden"]
    )
    def test_durations_and_units_are_measures(self, name: str) -> None:
        """Unit and duration words are no date parts: the first measure keeps its place (review of 2026-10-15)."""
        roles = [role("value", "numeric")]
        data = profile(f"Jahr,{name},Messwert\n2020,1,2.5\n2021,30,3.5\n2022,45,1.5\n")

        assert as_pairs(default_bindings(roles, data)) == [("value", name)]

    def test_a_named_month_outside_its_range_is_a_measure(self) -> None:
        roles = [role("value", "numeric")]
        data = profile("Month,Messwert\n1,2.5\n24,3.5\n36,1.5\n")

        assert as_pairs(default_bindings(roles, data)) == [("value", "Month")]

    def test_an_unnamed_month_counts_only_beside_a_year(self) -> None:
        roles = [role("value", "numeric")]

        assert as_pairs(default_bindings(roles, profile(monthly("Jahr,M,Wert,Regen")))) == [("value", "Wert")]
        # Without a year column, 1 to 12 is any measure: the column order stands.
        twelve = "M,Wert\n" + "".join(f"{m},{m * 2.5}\n" for m in range(1, 13))
        assert as_pairs(default_bindings(roles, profile(twelve))) == [("value", "M")]

    def test_weak_measures_a_family_leaves_out_are_no_series(self) -> None:
        """A constant `target` or a `Dauer (Minuten)` the family skips never becomes the optional series label."""
        roles = parse_roles(LINE_MULTI)
        constant = profile("year,actual,target\n2020,1.5,100\n2021,2.5,100\n2022,3.5,100\n2023,2.0,100\n2024,4.0,100\n")
        assert as_pairs(default_bindings(roles, constant)) == [("x", "year"), ("y1", "actual")]


class TestAxisRoles:
    """A scatter's `x (numeric)` is the independent variable: a month, a rank or a year stays on x."""

    SCATTER = (role("x", "numeric"), role("y", "numeric"))

    @pytest.mark.parametrize(
        ("csv_text", "expected"),
        [
            ("Months since start,Revenue\n1,10.5\n2,12.5\n3,15.0\n", [("x", "Months since start"), ("y", "Revenue")]),
            ("Month,Temperature\n1,-0.5\n2,1.5\n3,5.0\n", [("x", "Month"), ("y", "Temperature")]),
            (
                "Year,Quarter,Sales\n2024,1,10.5\n2024,2,12.5\n2024,3,9.0\n2024,4,11.0\n",
                [("x", "Year"), ("y", "Sales")],
            ),
            ("Rating,Score\n1,10.5\n5,12.5\n12,15.0\n", [("x", "Rating"), ("y", "Score")]),
            ("Rank,Points\n1,99.5\n2,80.5\n3,70.0\n", [("x", "Rank"), ("y", "Points")]),
            ("Grade,Income\n1,30.5\n2,40.5\n3,50.0\n", [("x", "Grade"), ("y", "Income")]),
            ("Kinder,Ausgaben\n1,300.5\n2,400.5\n4,500.0\n", [("x", "Kinder"), ("y", "Ausgaben")]),
        ],
    )
    def test_x_keeps_the_first_column(self, csv_text: str, expected: list[tuple[str, str]]) -> None:
        assert as_pairs(default_bindings(list(self.SCATTER), profile(csv_text))) == expected

    def test_x_still_skips_a_constant(self) -> None:
        data = profile("flag,a,b\n1,1.5,2\n1,2.5,3\n1,3.5,1\n1,4.5,5\n1,5.5,4\n")

        assert as_pairs(default_bindings(list(self.SCATTER), data)) == [("x", "a"), ("y", "b")]


class TestComputedRoles:
    """Owner decision of 2026-10-15, "both allowed": bound on a clear name match or by hand, else computed."""

    def test_without_a_matching_column_the_plot_computes_it(self) -> None:
        roles = parse_roles(ROLLING)
        rolling = next(item for item in roles if item.name == "rolling_avg")
        data = profile("date,value,smooth\n2024-01-01,1.5,1.4\n2024-01-02,2.5,2.0\n")

        assert rolling.computed and not any(item.computed for item in roles if item.name != "rolling_avg")
        assert as_pairs(default_bindings(roles, data)) == [("date", "date"), ("value", "value")]
        check = check_bindings(default_bindings(roles, data), roles, data)
        assert check.complete and check.missing_roles == []

    def test_a_hand_binding_is_allowed(self) -> None:
        roles = parse_roles(ROLLING)
        data = profile("date,value,smooth\n2024-01-01,1.5,1.4\n2024-01-02,2.5,2.0\n")
        bindings = bind(("date", "date"), ("value", "value"), ("rolling_avg", "smooth"))

        check = check_bindings(bindings, roles, data)
        assert check.complete and check.errors == []

    @pytest.mark.parametrize("name", ["rolling_avg", "Rolling Avg (7d)", "SMA 20", "SMA20", "gleitender Durchschnitt"])
    def test_a_column_named_so_is_bound(self, name: str) -> None:
        roles = parse_roles(ROLLING)
        data = profile(f"date,{name},value\n2024-01-01,1.4,1.5\n2024-01-02,2.0,2.5\n2024-01-03,2.2,2.0\n")

        assert as_pairs(default_bindings(roles, data)) == [("date", "date"), ("value", "value"), ("rolling_avg", name)]

    def test_the_name_match_comes_before_the_measure_ranking(self) -> None:
        """`value` would take the first number column; the named rolling column is kept for `rolling_avg`."""
        roles = parse_roles(ROLLING)
        data = profile("date,SMA 20,Temperature\n2024-01-01,1.4,1.5\n2024-01-02,2.0,2.5\n2024-01-03,2.2,2.0\n")

        assert as_pairs(default_bindings(roles, data)) == [
            ("date", "date"),
            ("value", "Temperature"),
            ("rolling_avg", "SMA 20"),
        ]

    @pytest.mark.parametrize(
        "bullet",
        [
            "`x` (numeric) — x-coordinate values computed as x(t)",
            "`features` (numeric matrix) - measurement values, used to compute distances",
            "`sma` (numeric) - Simple moving average (middle band), typically 20-period",
        ],
    )
    def test_only_a_description_that_starts_with_computed_marks_a_role(self, bullet: str) -> None:
        assert not parse_roles([bullet])[0].computed

    def test_the_adapter_reads_bound_or_computed_and_the_page_gets_an_optional_role(self) -> None:
        from agents.anyplot.briefs import describe_role
        from agents.main import _page_roles

        roles = parse_roles(ROLLING)
        rolling = next(item for item in roles if item.name == "rolling_avg")

        # The spec's own words come along: the rolling average's window (review of 2026-10-15).
        spec = "the spec: Computed rolling average (e.g., 7-day, 30-day window)"
        assert describe_role(rolling) == (
            f"rolling_avg (numeric, not bound: compute it in the plot code from the bound data; {spec})"
        )
        assert describe_role(rolling, bound=True) == (
            f"rolling_avg (numeric, bound: use its column as it is, do not compute it; {spec})"
        )
        bodies = {body["name"]: body for body in _page_roles(roles)}
        assert list(bodies) == ["date", "value", "rolling_avg"]
        assert bodies["rolling_avg"]["computed"] is True and bodies["rolling_avg"]["required"] is False
        assert bodies["value"]["computed"] is False and bodies["value"]["required"] is True


class TestNewDateColumn:
    def test_make_date_fills_the_open_required_date_role(self) -> None:
        """Owner decision of 2026-10-15: the code binds the new date column, not the model."""
        roles = parse_roles(ROLLING)
        text = monthly("Year,Month,Temperature,Precipitation")
        before = profile(text)
        bindings = default_bindings(roles, before)
        operation = {"op": "make_date", "name": "Datum", "year": "Year", "month": "Month"}
        after = parse_dataset(apply_operations(parse_dataset(text), OPERATIONS.validate_python([operation])).csv)

        assert as_pairs(carry_bindings(bindings, roles, after.profile, before)) == [
            ("date", "Datum"),
            ("value", "Temperature"),
        ]

    def test_set_type_to_a_date_fills_it_too(self) -> None:
        roles = parse_roles(ROLLING)
        text = "period,value\n2024-01,1.5\n2024-02,2.5\n2024-03,3.5\n"
        before = profile(text)
        bindings = default_bindings(roles, before)
        operation = {"op": "set_type", "column": "period", "type": "datetime", "date_format": "YYYY-MM"}
        after = parse_dataset(apply_operations(parse_dataset(text), OPERATIONS.validate_python([operation])).csv)

        assert ("date", "period") in as_pairs(carry_bindings(bindings, roles, after.profile, before))

    def test_a_date_column_that_was_there_is_left_alone(self) -> None:
        """A required date role the user left open over an existing date column stays open."""
        roles = parse_roles(ROLLING)
        data = profile("when,value\n2024-01-01,1.5\n2024-01-02,2.5\n")

        assert carry_bindings(bind(("value", "value")), roles, data, data) == bind(("value", "value"))

    def test_without_the_version_before_nothing_is_filled(self) -> None:
        roles = parse_roles(ROLLING)
        data = profile("when,value\n2024-01-01,1.5\n2024-01-02,2.5\n")

        assert carry_bindings(bind(("value", "value")), roles, data) == bind(("value", "value"))


class TestNamesOverCodes:
    def test_a_series_takes_the_name_column_over_its_codes(self) -> None:
        roles = parse_roles(LINE_MULTI)

        assert ("series", "country.value") in as_pairs(default_bindings(roles, profile(INDICATOR)))

    def test_short_capital_values_count_as_codes_beside_a_related_name(self) -> None:
        roles = [role("category", "categorical"), role("value", "numeric")]
        data = profile("country,country_name,value\nAUT,Austria,1.5\nCHE,Switzerland,2.5\nDEU,Germany,3.5\n")

        assert as_pairs(default_bindings(roles, data)) == [("category", "country_name"), ("value", "value")]

    @pytest.mark.parametrize(
        "csv_text",
        [
            "Status,Line,value\nOK,North,1.5\nNOK,South,2.5\nOK,North,3.5\n",
            "Currency,Region,value\nEUR,Europe,1.5\nUSD,America,2.5\nCHF,Alps,3.5\n",
            "Team,Stadt,value\nFCB,Basel,1.5\nYB,Bern,2.5\nFCZ,Zürich,3.5\n",
        ],
    )
    def test_equal_counts_without_a_name_relation_change_nothing(self, csv_text: str) -> None:
        """Same distinct and missing counts alone are no code and name pair (review of 2026-10-15)."""
        roles = [role("category", "categorical"), role("value", "numeric")]
        first = csv_text.split(",", 1)[0]

        assert as_pairs(default_bindings(roles, profile(csv_text))) == [("category", first), ("value", "value")]

    def test_name_similarity_comes_before_the_code_rank(self) -> None:
        roles = [role("product", "categorical"), role("value", "numeric")]
        data = profile("color,product_code,value\nred,P1,1.5\nblue,P2,2.5\ngreen,P3,3.5\n")

        assert as_pairs(default_bindings(roles, data)) == [("product", "product_code"), ("value", "value")]

    def test_a_name_column_as_similar_wins_over_the_code(self) -> None:
        roles = [role("product", "categorical"), role("value", "numeric")]
        data = profile("product_code,product_name,value\nP1,Chair,1.5\nP2,Table,2.5\nP3,Lamp,3.5\n")

        assert as_pairs(default_bindings(roles, data)) == [("product", "product_name"), ("value", "value")]

    def test_a_code_column_without_a_name_twin_keeps_its_place(self) -> None:
        """A name column that partitions the rows differently (more distinct values) is no spelled-out code."""
        roles = [role("category", "categorical"), role("value", "numeric")]
        data = profile("country_code,city,value\nAT,Wien,1.5\nAT,Graz,2.5\nCH,Bern,3.5\n")

        assert as_pairs(default_bindings(roles, data)) == [("category", "country_code"), ("value", "value")]


class TestDefaultBindings:
    def test_exact_names_win(self) -> None:
        roles = [role("x", "numeric"), role("y", "numeric")]
        data = profile("weight,Y,x\n1,2,3\n")

        assert as_pairs(default_bindings(roles, data)) == [("x", "x"), ("y", "Y")]

    def test_kind_tier_before_column_order(self) -> None:
        roles = [role("group", "categorical")]
        data = profile("count,region\n1,north\n2,south\n")

        assert as_pairs(default_bindings(roles, data)) == [("group", "region")]

    def test_a_single_valued_column_ranks_after_any_with_two_values(self) -> None:
        roles = [role("group", "categorical")]
        # The constant text column outranks the integer one by tier and comes first, yet it splits nothing.
        data = profile("country,year,value\nCH,2020,1.5\nCH,2021,2.5\n")

        assert as_pairs(default_bindings(roles, data)) == [("group", "year")]

    def test_a_single_valued_column_is_still_taken_when_nothing_else_fits(self) -> None:
        roles = [role("group", "categorical"), role("value", "numeric")]
        data = profile("country,value\nCH,1.5\nCH,2.5\n")

        assert as_pairs(default_bindings(roles, data)) == [("group", "country"), ("value", "value")]

    def test_number_roles_keep_a_single_valued_column_of_a_short_table(self) -> None:
        """Two equal values in two rows say little: below `MIN_CONSTANT_ROWS` the column order stands."""
        roles = [role("x", "numeric")]
        data = profile("level,value\n1.5,2.5\n1.5,3.5\n")

        assert as_pairs(default_bindings(roles, data)) == [("x", "level")]

    def test_integer_column_is_accepted_for_a_categorical_role_when_nothing_better_exists(self) -> None:
        roles = [role("group", "categorical")]
        data = profile("year,value\n2020,1.5\n2021,2.5\n")

        assert as_pairs(default_bindings(roles, data)) == [("group", "year")]

    def test_single_roles_fall_back_in_spec_order_without_a_variadic_family(self) -> None:
        roles = [role("x", "categorical"), role("y", "categorical"), role("value", "numeric")]
        data = profile("day,hour,count\nMon,9,12\nTue,10,7\n")

        assert as_pairs(default_bindings(roles, data)) == [("x", "day"), ("y", "hour"), ("value", "count")]

    def test_name_similarity_breaks_ties_within_a_tier(self) -> None:
        roles = [role("temperature", "numeric")]
        data = profile("pressure,air_temperature\n1000.5,21.5\n")

        assert as_pairs(default_bindings(roles, data)) == [("temperature", "air_temperature")]

    def test_each_column_is_bound_once(self) -> None:
        roles = [role("a", "numeric"), role("b", "numeric")]
        data = profile("v,label\n1.5,x\n")

        assert as_pairs(default_bindings(roles, data)) == [("a", "v")]

    def test_roles_without_kinds_stay_unbound(self) -> None:
        roles = [role("nodes"), role("weight", "numeric")]
        data = profile("nodes,weight\nA,1.5\n")

        assert as_pairs(default_bindings(roles, data)) == [("weight", "weight")]

    def test_required_roles_bind_before_optional_ones(self) -> None:
        roles = [role("size", "numeric", required=False), role("x", "numeric"), role("y", "numeric", variadic=True)]
        data = profile("a,b,c\n1.5,2.5,3.5\n")

        assert as_pairs(default_bindings(roles, data)) == [("x", "a"), ("y1", "b"), ("y2", "c")]

    def test_variadic_families_stop_at_the_cap(self) -> None:
        roles = [role("y", "numeric", variadic=True)]
        header = ",".join(f"s{i}" for i in range(20))
        data = profile(f"{header}\n" + ",".join("1.5" for _ in range(20)) + "\n")
        bindings = default_bindings(roles, data)

        assert len(bindings) == MAX_VARIADIC_DEFAULT
        assert [binding.role for binding in bindings] == [f"y{n}" for n in range(1, MAX_VARIADIC_DEFAULT + 1)]

    def test_named_members_are_taken_first_then_the_rest_in_column_order(self) -> None:
        roles = [role("x", "numeric"), role("y", "numeric", variadic=True)]
        data = profile("t,extra,y1,y2\n1,2.5,3.5,4.5\n")

        assert as_pairs(default_bindings(roles, data)) == [("x", "t"), ("y1", "extra"), ("y2", "y1"), ("y3", "y2")]

    def test_variadic_families_skip_tier_two_columns(self) -> None:
        roles = [role("label", "categorical", variadic=True)]
        data = profile("a,b,n\nx,y,1\n")

        assert as_pairs(default_bindings(roles, data)) == [("label1", "a"), ("label2", "b")]

    def test_default_bindings_pass_their_own_check(self) -> None:
        roles = parse_roles(LINE_MULTI)
        data = profile("date,a,b,company\n2024-01-01,1.5,2.5,X\n")
        check = check_bindings(default_bindings(roles, data), roles, data)

        assert check.errors == []
        assert check.complete


class TestCarryBindings:
    """The bindings after `prepare_data` or undo changed the dataset under them."""

    ROLES = [role("x", "numeric"), role("y", "numeric", variadic=True), role("group", "categorical", required=False)]

    def test_nothing_changes_while_every_binding_stays_valid(self) -> None:
        data = profile("a,b,team\n1,2,red\n")
        chosen = bind(("x", "b"), ("y1", "a"))  # the user's own choice, and `group` left unbound on purpose

        assert carry_bindings(chosen, self.ROLES, data) == chosen

    def test_a_renamed_column_drops_its_binding_and_the_role_is_bound_again_by_default(self) -> None:
        data = profile("hours,b,team\n1,2,red\n")  # `a` became `hours`
        carried = carry_bindings(bind(("x", "a"), ("y1", "b")), self.ROLES, data)

        assert as_pairs(carried) == [("x", "hours"), ("y1", "b"), ("group", "team")]
        assert check_bindings(carried, self.ROLES, data).complete

    def test_a_retyped_column_drops_its_binding(self) -> None:
        data = profile("a,b\nx,2\n")  # `a` is text now
        carried = carry_bindings(bind(("x", "a"), ("y1", "b")), self.ROLES, data)

        assert as_pairs(carried) == [("y1", "b"), ("group", "a")]
        assert check_bindings(carried, self.ROLES, data).missing_roles == ["x"]

    def test_an_open_role_takes_the_next_free_column_past_a_kept_binding(self) -> None:
        """The defaults alone would give `x` the column `y1` keeps; on the free columns `x` gets `c`."""
        data = profile("a,b,c\nx,2,3\n")  # `a` is text now; `b` stays with y1
        carried = carry_bindings(bind(("x", "a"), ("y1", "b")), self.ROLES, data)

        assert as_pairs(carried) == [("x", "c"), ("y1", "b"), ("group", "a")]
        assert check_bindings(carried, self.ROLES, data).complete

    def test_a_family_keeps_its_members_and_gains_the_defaults_under_the_next_numbers(self) -> None:
        data = profile("a,b,c\n1,2,3\n")  # `gone` was dropped; y1 stays, the defaults' y1 becomes y2
        carried = carry_bindings(bind(("x", "gone"), ("y1", "b")), self.ROLES, data)

        assert as_pairs(carried) == [("x", "a"), ("y1", "b"), ("y2", "c")]
        assert check_bindings(carried, self.ROLES, data).complete

    def test_an_aggregate_replaces_every_column(self) -> None:
        data = profile("month,Umsatz\n2024-01,10\n")
        carried = carry_bindings(bind(("x", "a"), ("y1", "b"), ("y2", "c")), self.ROLES, data)

        assert as_pairs(carried) == as_pairs(default_bindings(self.ROLES, data))

    def test_the_kept_bindings_keep_their_places_in_the_spec_order(self) -> None:
        data = profile("a,b,c\n1,2,3\n")
        carried = carry_bindings(bind(("y2", "c"), ("x", "gone")), self.ROLES, data)

        assert as_pairs(carried) == [("x", "a"), ("y1", "b"), ("y2", "c")]


class TestCheckBindings:
    ROLES = [
        role("x", "datetime", "numeric"),
        role("y", "numeric", variadic=True),
        role("group", "categorical", required=False),
        role("note"),
    ]
    DATA = "when,a,b,team,flag,code,comment\n2024-01-01,1.5,2,red,true,7,hello\n"

    def check(self, *pairs: tuple[str, str]) -> tuple[bool, list[str], list[str]]:
        result = check_bindings(bind(*pairs), self.ROLES, profile(self.DATA))
        return result.complete, result.errors, result.missing_roles

    def test_complete(self) -> None:
        complete, errors, missing = self.check(("x", "when"), ("y1", "a"), ("y7", "b"), ("note", "comment"))

        assert (complete, errors, missing) == (True, [], [])

    def test_required_roles_are_missing_until_bound(self) -> None:
        complete, errors, missing = self.check(("group", "team"))

        assert not complete
        assert errors == []
        assert missing == ["x", "y", "note"]

    def test_unknown_role(self) -> None:
        _, errors, _ = self.check(("z", "a"))

        assert errors == ["unknown role 'z'"]

    @pytest.mark.parametrize("member", ["y", "y0", "y01", "y_1", "yy"])
    def test_a_family_takes_only_numbered_members(self, member: str) -> None:
        _, errors, _ = self.check((member, "a"))

        expected = "role 'y' takes numbered members such as 'y1'" if member == "y" else f"unknown role '{member}'"
        assert errors == [expected]

    def test_role_bound_twice(self) -> None:
        _, errors, _ = self.check(("x", "when"), ("x", "a"))

        assert "role 'x' is bound more than once" in errors

    def test_unknown_column(self) -> None:
        _, errors, missing = self.check(("x", "nope"))

        assert errors == ["column 'nope' is not in the dataset"]
        assert "x" in missing

    def test_column_bound_twice(self) -> None:
        _, errors, _ = self.check(("y1", "a"), ("y2", "a"))

        assert errors == ["column 'a' is bound more than once"]

    def test_incompatible_dtype(self) -> None:
        complete, errors, missing = self.check(("x", "team"), ("y1", "a"), ("note", "comment"))

        assert not complete
        assert errors == ["role 'x' needs datetime or numeric data, but column 'team' is text"]
        assert missing == ["x"]

    @pytest.mark.parametrize("column", ["team", "flag", "code"])
    def test_categorical_accepts_text_boolean_and_integer(self, column: str) -> None:
        _, errors, _ = self.check(("group", column))

        assert errors == []

    @pytest.mark.parametrize("column", ["when", "a", "team", "flag"])
    def test_an_untyped_role_accepts_any_column(self, column: str) -> None:
        _, errors, _ = self.check(("note", column))

        assert errors == []

    def test_errors_make_the_check_incomplete(self) -> None:
        complete, errors, missing = self.check(("x", "when"), ("y1", "a"), ("note", "comment"), ("z", "b"))

        assert missing == []
        assert errors
        assert not complete


@pytest.mark.parametrize(
    ("kinds", "dtype", "accepted"),
    [
        (("numeric",), "number", True),
        (("numeric",), "integer", True),
        (("numeric",), "text", False),
        (("numeric",), "datetime", False),
        (("numeric",), "boolean", False),
        (("categorical",), "text", True),
        (("categorical",), "boolean", True),
        (("categorical",), "integer", True),
        (("categorical",), "number", False),
        (("categorical",), "datetime", False),
        (("text",), "text", True),
        (("text",), "boolean", True),
        (("text",), "integer", True),
        (("text",), "number", False),
        (("boolean",), "boolean", True),
        (("boolean",), "integer", True),
        (("boolean",), "text", False),
        (("datetime",), "datetime", True),
        (("datetime",), "number", False),
        (("datetime", "numeric"), "number", True),
        ((), "number", True),
    ],
)
def test_compatibility_matrix(kinds: tuple[RoleKind, ...], dtype: ColumnDtype, accepted: bool) -> None:
    assert accepts(role("r", *kinds), dtype) is accepted


def test_resolve_role_prefers_the_longest_family() -> None:
    roles = [role("y", "numeric", variadic=True), role("y_", "numeric", variadic=True), role("y1", "numeric")]

    assert resolve_role("y1", roles) == roles[2]
    assert resolve_role("y2", roles) == roles[0]
    assert resolve_role("y_3", roles) == roles[1]
    assert resolve_role("z", roles) is None


@pytest.mark.parametrize(
    ("left", "right", "minimum", "maximum"),
    [
        ("x", "X", 1.0, 1.0),
        ("start_name", "startName", 1.0, 1.0),
        ("temperature", "air_temperature", 0.8, 1.0),
        ("value", "revenue", 0.0, 0.6),
        ("x", "weight", 0.0, 0.3),
    ],
)
def test_name_similarity(left: str, right: str, minimum: float, maximum: float) -> None:
    assert minimum <= name_similarity(left, right) <= maximum
