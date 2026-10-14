"""Tests for agents/anyplot/data/bindings.py: default bindings and their validation."""

import pytest

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
from agents.anyplot.data.roles import DataRole, RoleKind, parse_roles
from agents.anyplot.schemas import Binding, ColumnDtype, DatasetProfile
from tests.unit.agents.data.test_roles import AREA_STACKED, LINE_MULTI


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

    def test_a_time_axis_prefers_the_year_among_numbers(self) -> None:
        roles = [role("x", "datetime", "numeric"), role("y", "numeric")]
        data = profile("population,year\n7.5,2020\n7.6,2021\n")

        assert as_pairs(default_bindings(roles, data)) == [("x", "year"), ("y", "population")]

    def test_a_year_column_is_the_category_of_a_wide_table(self) -> None:
        roles = [role("category", "categorical"), role("y", "numeric", variadic=True)]
        data = profile("Jahr,Shoes,Hats\n2020,1,2\n2021,3,4\n")

        assert as_pairs(default_bindings(roles, data)) == [("category", "Jahr"), ("y1", "Shoes"), ("y2", "Hats")]


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

    def test_number_roles_keep_a_single_valued_column(self) -> None:
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
