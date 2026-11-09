"""Tests for agents/anyplot/data/fidelity.py: a key of the marks that the rows repeat, and rows without a value to draw.

Owner decision of 2026-11-08: the plot draws every row; a change of the rows goes only through the data step. In the
persona round of 2026-11-06 a line chart of 27 measurements over 9 lengths was averaged to 9 points in the plot code,
without a count. Every table here is invented.
"""

from dataclasses import replace
from pathlib import Path

import pytest

from agents.anyplot.data.bindings import carry_by_name, check_bindings, default_bindings, valid_bindings
from agents.anyplot.data.computed import mark_name_only
from agents.anyplot.data.fidelity import (
    COMBINED_HEAD,
    KEY_ROLES,
    LEFT_OUT_HEAD,
    SEPARATE_ROLES,
    SUM_SPECS,
    UNREDUCED_SPECS,
    KeyAggregate,
    RepeatedKey,
    combined_line,
    key_aggregate,
    left_out_line,
    mark_keys,
)
from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.data.signs import mark_non_negative
from agents.anyplot.data.warning_codes import binding_warning_codes
from agents.anyplot.schemas import MAX_CHANGE_CHARS, Binding, ColumnProfile, DatasetProfile
from core.spec_roles import DataRole, data_bullets, mark_computed, parse_roles, spec_shape


PLOTS = Path(__file__).resolve().parents[4] / "plots"

REPEATS_THE_POINT = (
    "scatter-",
    "box-",
    "violin-",
    "strip-",
    "swarm-",
    "histogram-",
    "density-",
    "hexbin-",
    "count-",
    "raincloud-",
    "ridgeline-",
    "ecdf-",
    "rug-",
    "qq-",
    "cat-box-strip",
    "bubble-",
    "contour-",
)
"""Spec families whose plot type draws every row as its own mark or summarises the rows itself: never keyed."""


def roles_of(spec_id: str) -> list[DataRole]:
    """The roles as the session reads them (`CatalogueSnapshot.roles`), from the spec file."""
    parsed = parse_roles(data_bullets((PLOTS / spec_id / "specification.md").read_text(encoding="utf-8")))
    roles = mark_computed(mark_non_negative(parsed, spec_id), spec_id)
    return mark_keys(mark_name_only(roles, spec_id), spec_id)


def profile_of(text: str) -> DatasetProfile:
    return parse_dataset(text).profile


def bind(**pairs: str) -> list[Binding]:
    return [Binding(role=role, column=column) for role, column in pairs.items()]


LENGTHS = "Length,Reading\n" + "".join(f"{10 + 5 * (i % 9)},{20 + (i * 7) % 13}.5\n" for i in range(27))
"""27 invented readings over 9 lengths, three per length: case 06 of the persona round, made up again."""


class TestKeyTable:
    @pytest.mark.parametrize("spec_id", sorted(KEY_ROLES))
    def test_every_listed_role_is_a_single_role_of_its_spec_the_plot_does_not_compute(self, spec_id: str) -> None:
        roles = {role.name: role for role in roles_of(spec_id)}
        for name in KEY_ROLES[spec_id]:
            assert name in roles, f"{spec_id} has no role {name}"
            assert roles[name].key and not roles[name].variadic and not roles[name].computed
        assert spec_shape(spec_id, list(roles.values())) == "table"

    def test_no_spec_whose_repeats_are_the_point_is_keyed(self) -> None:
        assert [spec for spec in KEY_ROLES if spec.startswith(REPEATS_THE_POINT)] == []

    @pytest.mark.parametrize("spec_id", sorted(SEPARATE_ROLES))
    def test_every_separate_role_is_a_required_number_or_date_role_of_its_spec(self, spec_id: str) -> None:
        roles = {role.name: role for role in roles_of(spec_id)}
        for name in SEPARATE_ROLES[spec_id]:
            assert name in roles and roles[name].required, f"{spec_id}.{name}"
            assert {"numeric", "datetime"} & set(roles[name].kinds), f"{spec_id}.{name}"

    def test_an_unlisted_spec_has_no_key(self) -> None:
        assert not any(role.key for role in roles_of("scatter-basic"))
        assert [role.name for role in roles_of("bar-grouped") if role.key] == ["category", "group"]


class TestRepeatedKey:
    def test_a_line_over_repeated_x_values_warns_with_the_counts(self) -> None:
        roles, profile = roles_of("line-styled"), profile_of(LENGTHS)

        check = check_bindings(bind(x="Length", y_1="Reading"), roles, profile)

        assert check.complete and check.errors == []
        assert check.repeated_key == RepeatedKey(roles=("x",), columns=("Length",), values=9, combinations=9, rows=27)
        assert check.warnings == [
            "x: column 'Length' holds 9 values in 27 rows; the plot draws one value per x, so rows with the same x "
            "need an aggregate first"
        ]
        assert check.repeated_key.fact() == "x has 9 values in 27 rows"
        assert binding_warning_codes(check.warnings) == ["repeated_key"]

    def test_a_scatter_with_repeated_x_values_never_warns(self) -> None:
        profile = profile_of(LENGTHS)

        check = check_bindings(bind(x="Length", y="Reading"), roles_of("scatter-basic"), profile)

        assert check.repeated_key is None and check.warnings == []

    @pytest.mark.parametrize("spec_id", ["box-basic", "histogram-basic", "strip-basic", "violin-basic"])
    def test_a_distribution_of_repeated_groups_never_warns(self, spec_id: str) -> None:
        roles = roles_of(spec_id)
        text = "Group,Value\n" + "".join(f"{'ABC'[i % 3]},{i * 1.5}\n" for i in range(30))
        profile = profile_of(text)

        check = check_bindings(default_bindings(roles, profile), roles, profile)

        assert check.repeated_key is None

    def test_a_bar_chart_of_unique_categories_never_warns(self) -> None:
        profile = profile_of("Fruit,Sold\nApples,12\nPears,7\nPlums,9\nCherries,15\n")

        check = check_bindings(bind(category="Fruit", value="Sold"), roles_of("bar-basic"), profile)

        assert check.repeated_key is None and check.warnings == []

    def test_a_bar_chart_of_years_per_region_warns_for_the_region(self) -> None:
        text = "Region,Year,Sales\n" + "".join(
            f"{r},{y},{10 + i}\n"
            for i, (r, y) in enumerate((r, y) for r in ("North", "South", "East", "West") for y in (2023, 2024, 2025))
        )
        profile = profile_of(text)

        check = check_bindings(bind(category="Region", value="Sales"), roles_of("bar-basic"), profile)

        assert check.repeated_key is not None
        assert check.warnings[-1].startswith("category: column 'Region' holds 4 values in 12 rows;")

    def test_a_crossed_bar_chart_is_one_value_per_category_and_group(self) -> None:
        crossed = "Subject,Grade,Score\n" + "".join(
            f"{s},{g},{60 + i}\n" for i, (s, g) in enumerate((s, g) for s in "ABCD" for g in ("G1", "G2", "G3"))
        )
        roles = roles_of("bar-grouped")
        profile = profile_of(crossed)

        assert (
            check_bindings(bind(category="Subject", group="Grade", value="Score"), roles, profile).repeated_key is None
        )

        doubled = profile_of(crossed + "".join(crossed.splitlines(keepends=True)[1:]))
        check = check_bindings(bind(category="Subject", group="Grade", value="Score"), roles, doubled)
        assert check.repeated_key is not None
        assert check.warnings[-1] == (
            "category: column 'Subject' holds 4 values in 24 rows, at most 12 combinations with group ('Grade'); "
            "the plot draws one value per category and group, so rows with the same category and group need an "
            "aggregate first"
        )
        assert check.repeated_key.fact() == "category and group have at most 12 combinations in 24 rows"

    def test_a_series_splits_the_x_of_a_long_line_table(self) -> None:
        """Three series over 9 x values each are 27 rows and one point per x of each series: no warning. The same
        rows without the series bound draw three points per x."""
        text = "Step,Sensor,Value\n" + "".join(f"{i % 9},{'S' + str(i // 9)},{i * 0.5}\n" for i in range(27))
        roles, profile = roles_of("line-multi"), profile_of(text)

        assert check_bindings(bind(x="Step", y1="Value", series="Sensor"), roles, profile).repeated_key is None
        alone = check_bindings(bind(x="Step", y1="Value"), roles, profile).repeated_key
        assert alone is not None and alone.roles == ("x",)

    def test_a_heatmap_names_both_keys(self) -> None:
        text = "Hour,Day,Visits\n" + "".join(f"{h},{d},{h + i}\n" for i, d in enumerate("MTW") for h in range(4))
        roles, profile = roles_of("heatmap-basic"), profile_of(text + "0,M,99\n")

        repeated = check_bindings(bind(x="Hour", y="Day", value="Visits"), roles, profile).repeated_key

        assert repeated is not None
        assert (repeated.roles, repeated.combinations, repeated.rows) == (("x", "y"), 12, 13)
        assert repeated.per() == "x and y"

    def test_empty_values_count_only_the_rows_that_can_draw(self) -> None:
        """27 rows over 9 lengths, but only 9 of them hold a reading: the plot draws one point per length."""
        rows = [line.split(",") for line in LENGTHS.splitlines()[1:]]
        text = "Length,Reading\n" + "".join(f"{x},{y if i < 9 else ''}\n" for i, (x, y) in enumerate(rows))
        profile = profile_of(text)

        check = check_bindings(bind(x="Length", y_1="Reading"), roles_of("line-styled"), profile)

        assert check.repeated_key is None

    def test_a_mark_that_needs_every_price_counts_the_gaps_of_each(self) -> None:
        """A candle needs open, high, low and close: a second row of a date that lacks its close draws no second
        candle, so the repeat is no certain one. With all four prices it is."""
        roles = roles_of("candlestick-basic")
        bindings = bind(date="Day", open="O", high="H", low="L", close="C")
        partial = profile_of("Day,O,H,L,C\n2026-01-01,1,3,0.5,2\n2026-01-01,1,3,0.5,\n2026-01-02,2,4,1.5,3\n")
        complete = profile_of("Day,O,H,L,C\n2026-01-01,1,3,0.5,2\n2026-01-01,1,3,0.5,2.5\n2026-01-02,2,4,1.5,3\n")

        assert check_bindings(bindings, roles, partial).repeated_key is None
        assert check_bindings(bindings, roles, complete).repeated_key is not None

    def test_each_series_of_a_wide_table_needs_only_its_own_column(self) -> None:
        """Two series that take turns down the rows (A on one, B on the next, the same x) draw one point per x
        each; the same rows with both filled draw two."""
        roles = roles_of("line-styled")
        bindings = bind(x="Step", y_1="A", y_2="B")
        turns = profile_of("Step,A,B\n1,3,\n1,,4\n2,5,\n2,,6\n")
        filled = profile_of("Step,A,B\n1,3,7\n1,2,4\n2,5,8\n2,1,6\n")

        assert check_bindings(bindings, roles, turns).repeated_key is None
        assert check_bindings(bindings, roles, filled).repeated_key is not None

    def test_an_optional_measure_never_hides_a_repeat(self) -> None:
        roles = roles_of("bar-feature-importance")
        profile = profile_of("Feature,Importance,Std\nage,0.4,\nage,0.3,\nzip,0.2,0.1\n")

        check = check_bindings(bind(feature="Feature", importance="Importance", std="Std"), roles, profile)

        assert check.repeated_key is not None and check.repeated_key.roles == ("feature",)

    def test_a_column_on_two_roles_counts_once(self) -> None:
        """One column may serve several roles (owner decision of 2026-11-04): the key's column as a label as well
        never doubles the keys it can make."""
        roles = roles_of("bar-basic") + [DataRole("label", ("text",), False, False, "a label for each bar")]
        profile = profile_of("Fruit,Sold\nApples,12\nPears,7\nApples,9\n")

        check = check_bindings(bind(category="Fruit", value="Sold", label="Fruit"), roles, profile)

        assert check.repeated_key is not None and check.repeated_key.columns == ("Fruit",)


class TestExistingRulesStillWin:
    @pytest.mark.parametrize(
        ("spec_id", "text"),
        [
            ("line-styled", LENGTHS),
            ("bar-basic", "Region,Year,Sales\nNorth,2024,3\nNorth,2025,4\nSouth,2024,5\nSouth,2025,6\n"),
            (
                "line-timeseries-rolling",
                "Date,Close,7-day avg\n"
                + "".join(f"2026-01-{1 + i % 5:02d},{10 + i},{'' if i < 6 else 11 + i}\n" for i in range(10)),
            ),
            ("indicator-macd", "Date,MACD,Open\n2026-01-01,0.4,10\n2026-01-01,0.5,11\n2026-01-02,0.2,12\n"),
            ("heatmap-basic", "Hour,Day,Visits\n1,M,3\n1,M,4\n2,T,5\n"),
        ],
    )
    def test_the_key_marks_change_no_default_binding(self, spec_id: str, text: str) -> None:
        roles, profile = roles_of(spec_id), profile_of(text)
        unkeyed = [replace(role, key=False) for role in roles]

        assert default_bindings(roles, profile) == default_bindings(unkeyed, profile)
        keyed, plain = (
            check_bindings(default_bindings(roles, profile), roles, profile),
            check_bindings(default_bindings(unkeyed, profile), unkeyed, profile),
        )
        assert (keyed.complete, keyed.missing_roles, keyed.errors) == (
            plain.complete,
            plain.missing_roles,
            plain.errors,
        )
        assert keyed.fit_warnings == plain.warnings

    def test_a_computed_role_bound_to_its_column_is_no_part_of_the_key(self) -> None:
        """B1: `rolling_avg` binds to a column that holds it; its empty first rows split nothing and leave no row out."""
        text = "Date,Close,7-day avg\n" + "".join(
            f"2026-01-{1 + i:02d},{10 + i},{'' if i < 6 else 11 + i}\n" for i in range(10)
        )
        roles, profile = roles_of("line-timeseries-rolling"), profile_of(text)
        bindings = default_bindings(roles, profile)
        assert {binding.role: binding.column for binding in bindings} == {
            "date": "Date",
            "value": "Close",
            "rolling_avg": "7-day avg",
        }

        check = check_bindings(bindings, roles, profile)

        assert check.repeated_key is None
        assert left_out_line(valid_bindings(bindings, roles, profile), "line-timeseries-rolling", roles, 10) is None

    def test_a_name_only_role_stays_missing_and_the_key_waits_for_it(self) -> None:
        """B1b: the MACD line binds only to a column named so. While it is missing no mark is drawn, so a repeated
        date warns only once a MACD column is bound."""
        roles = roles_of("indicator-macd")
        prices = profile_of("Date,Open\n2026-01-01,10\n2026-01-01,11\n2026-01-02,12\n")

        check = check_bindings(default_bindings(roles, prices), roles, prices)

        assert "macd" in check.missing_roles and check.repeated_key is None
        named = profile_of("Date,MACD\n2026-01-01,0.4\n2026-01-01,0.5\n2026-01-02,0.2\n")
        bindings = default_bindings(roles, named)
        assert {binding.role: binding.column for binding in bindings} == {"date": "Date", "macd": "MACD"}
        repeated = check_bindings(bindings, roles, named).repeated_key
        assert repeated is not None and repeated.roles == ("date",)

    def test_incomplete_or_invalid_bindings_never_warn(self) -> None:
        roles, profile = roles_of("line-styled"), profile_of(LENGTHS)

        assert check_bindings(bind(x="Length"), roles, profile).repeated_key is None
        invalid = check_bindings(bind(x="Length", y_1="Reading", z="Reading"), roles, profile)
        assert invalid.errors and invalid.repeated_key is None

    def test_a_spec_of_name_only_summaries_is_never_keyed(self) -> None:
        roles = roles_of("spc-xbar-r")
        assert not any(role.key for role in roles)

    def test_new_data_with_a_repeated_key_carries_the_binding_and_keeps_the_warning(self) -> None:
        """`carry_by_name` refuses a carry that adds a warning; a key the new rows repeat is no fault of the column."""
        roles = roles_of("line-styled")
        old = profile_of("Length,Reading\n10,1\n15,2\n20,3\n")
        new = profile_of(LENGTHS)
        assert check_bindings(bind(x="Length", y_1="Reading"), roles, old).repeated_key is None

        carried = carry_by_name(bind(x="Length", y_1="Reading"), roles, new)

        assert {binding.role: binding.column for binding in carried} == {"x": "Length", "y_1": "Reading"}
        assert check_bindings(carried, roles, new).repeated_key is not None


class TestLeftOutLine:
    def test_empty_values_of_a_bound_mark_are_counted_per_role_in_spec_order(self) -> None:
        text = "Region,Sales,Cost\nNorth,3,1\nSouth,,2\nEast,5,\nWest,,4\n"
        roles, profile = roles_of("scatter-basic"), profile_of(text)
        bindings = bind(y="Sales", x="Cost")

        line = left_out_line(valid_bindings(bindings, roles, profile), "scatter-basic", roles, profile.rows)

        assert line == f"{LEFT_OUT_HEAD}1 row without x ('Cost'), 2 without y ('Sales')"

    def test_one_row_reads_in_the_singular(self) -> None:
        roles, profile = roles_of("bar-basic"), profile_of("Fruit,Sold\nApples,12\nPears,\nPlums,9\n")

        line = left_out_line(
            valid_bindings(bind(category="Fruit", value="Sold"), roles, profile), "bar-basic", roles, 3
        )

        assert line == f"{LEFT_OUT_HEAD}1 row without value ('Sold')"

    def test_an_empty_key_label_leaves_its_bar_out(self) -> None:
        roles, profile = roles_of("bar-basic"), profile_of("Fruit,Sold\nApples,12\n,7\nPlums,9\n")

        line = left_out_line(
            valid_bindings(bind(category="Fruit", value="Sold"), roles, profile), "bar-basic", roles, 3
        )

        assert line == f"{LEFT_OUT_HEAD}1 row without category ('Fruit')"

    def test_an_optional_role_and_a_text_label_leave_no_row_out(self) -> None:
        roles = roles_of("bar-feature-importance")
        profile = profile_of("Feature,Importance,Std\nage,0.4,0.1\nincome,0.3,\nzip,0.2,\n")
        bindings = bind(feature="Feature", importance="Importance", std="Std")

        assert left_out_line(valid_bindings(bindings, roles, profile), "bar-feature-importance", roles, 3) is None

    def test_a_shorter_list_beside_the_rows_is_the_layout(self) -> None:
        """`line-annotated-events` holds a few event dates beside the daily rows, by the spec's own words."""
        text = "Day,Price,Event day,Event\n" + "".join(
            f"2026-01-{1 + i:02d},{10 + i},{'2026-01-03' if i == 0 else ''},{'Launch' if i == 0 else ''}\n"
            for i in range(8)
        )
        roles, profile = roles_of("line-annotated-events"), profile_of(text)
        bindings = bind(date="Day", value="Price", event_date="Event day", event_label="Event")

        held = valid_bindings(bindings, roles, profile)
        assert len(held) == 4
        assert left_out_line(held, "line-annotated-events", roles, profile.rows) is None

    def test_a_value_written_once_is_no_row_left_out(self) -> None:
        """A limit written in one row only is a single value, whether or not `SEPARATE_ROLES` lists its spec."""
        roles = roles_of("histogram-capability")
        text = "Part,Width,LSL\n" + "".join(f"P{i},{10 + i * 0.1:.1f},{'9.5' if i == 0 else ''}\n" for i in range(6))
        profile = profile_of(text)
        held = valid_bindings(bind(measurement="Width", lsl="LSL"), roles, profile)

        assert left_out_line(held, "unlisted-spec", roles, profile.rows) is None

    def test_a_spec_of_parameters_has_no_rows_to_leave_out(self) -> None:
        roles = roles_of("heatmap-mandelbrot")
        assert spec_shape("heatmap-mandelbrot", roles) == "generated"
        profile = profile_of("x_min,x_max,y_min,y_max,max_iterations\n-2,1,-1.5,1.5,\n-2,1,-1.5,1.5,100\n")
        held = valid_bindings(default_bindings(roles, profile), roles, profile)

        assert left_out_line(held, "heatmap-mandelbrot", roles, profile.rows) is None

    def test_a_family_member_counts_by_its_family(self) -> None:
        text = "Step,A,B\n1,3,4\n2,,5\n3,4,\n4,,6\n"
        roles, profile = roles_of("line-styled"), profile_of(text)

        line = left_out_line(valid_bindings(bind(x="Step", y_1="A", y_2="B"), roles, profile), "line-styled", roles, 4)

        assert line == f"{LEFT_OUT_HEAD}2 rows without y_1 ('A'), 1 without y_2 ('B')"

    def test_the_line_fits_a_change_note_whatever_the_names(self) -> None:
        names = [f"Measurement {'x' * 50} {index}" for index in range(6)]
        header = ",".join(["Step", *names])
        rows = "".join(
            f"{step}," + ",".join("" if (step + index) % 3 == 0 else "1" for index in range(6)) + "\n"
            for step in range(9)
        )
        roles, profile = roles_of("line-styled"), profile_of(f"{header}\n{rows}")
        bindings = [Binding(role="x", column="Step")] + [
            Binding(role=f"y_{index + 1}", column=name) for index, name in enumerate(names)
        ]

        line = left_out_line(valid_bindings(bindings, roles, profile), "line-styled", roles, profile.rows)

        assert line is not None and len(line) <= MAX_CHANGE_CHARS
        assert line.startswith(LEFT_OUT_HEAD) and line.endswith("more roles")

    def test_the_longest_role_and_column_names_still_fit_with_the_rest_counted(self) -> None:
        names = ["N" * 63 + str(index) for index in range(3)]
        roles = [DataRole(f"{'y' * 31}{index}", ("numeric",), True, False, "a measure") for index in range(3)]
        rows = "".join(",".join("" if step == index else "1" for index in range(3)) + "\n" for step in range(4))
        profile = profile_of(",".join(names) + "\n" + rows)
        bindings = [Binding(role=role.name, column=name) for role, name in zip(roles, names, strict=True)]

        line = left_out_line(valid_bindings(bindings, roles, profile), "unlisted-spec", roles, profile.rows)

        assert line == f"{LEFT_OUT_HEAD}1 row without {roles[0].name} ('{names[0]}'), and 2 more roles"
        assert len(line) <= MAX_CHANGE_CHARS


class TestKeyAggregate:
    """Owner decision of 2026-11-09: a repeated key that reaches a plot run is combined by the server first, as a
    data step; which function, and when nothing is combined (`key_aggregate`)."""

    @staticmethod
    def aggregate_of(spec_id: str, text: str, **pairs: str) -> KeyAggregate | None:
        roles, profile = roles_of(spec_id), profile_of(text)
        bindings = bind(**pairs)
        repeated = check_bindings(bindings, roles, profile).repeated_key
        assert repeated is not None, spec_id
        return key_aggregate(valid_bindings(bindings, roles, profile), repeated, spec_id)

    def test_a_measurement_per_key_is_averaged(self) -> None:
        aggregate = self.aggregate_of("line-styled", LENGTHS, x="Length", y_1="Reading")

        assert aggregate == KeyAggregate(by=("Length",), values=("Reading",), how="mean")
        assert aggregate.operation == {"op": "aggregate", "by": ["Length"], "column": "Reading", "how": "mean"}

    def test_parts_of_a_whole_are_summed(self) -> None:
        text = "Category,Amount\n" + "".join(f"{c},{1 + i}\n" for i, c in enumerate("ABCABCAB"))

        aggregate = self.aggregate_of("pie-basic", text, category="Category", value="Amount")

        assert aggregate is not None and aggregate.how == "sum"

    def test_two_keys_and_several_values_take_one_aggregate(self) -> None:
        text = "Hour,Day,Visits\n" + "".join(f"{h},{d},{h + i}\n" for i, d in enumerate("MTW") for h in range(4))
        aggregate = self.aggregate_of("heatmap-basic", text + "0,M,99\n", x="Hour", y="Day", value="Visits")
        assert aggregate is not None and (aggregate.by, aggregate.values) == (("Hour", "Day"), ("Visits",))

        wide = "Step,A,B\n" + "".join(f"{i % 3},{i},{2 * i}\n" for i in range(9))
        both = self.aggregate_of("line-multi", wide, x="Step", y1="A", y2="B")
        assert both is not None and both.operation["columns"] == ["A", "B"] and "column" not in both.operation

    def test_measures_that_need_several_functions_are_left_to_the_user(self) -> None:
        text = "Date,Open,High,Low,Close\n" + "".join(
            f"2024-01-0{1 + i % 3},{10 + i},{12 + i},{9 + i},{11 + i}\n" for i in range(6)
        )

        assert (
            self.aggregate_of(
                "candlestick-basic", text, date="Date", open="Open", high="High", low="Low", close="Close"
            )
            is None
        )

    def test_a_text_column_beside_the_key_is_left_to_the_user(self) -> None:
        text = "Category,Amount,Note\n" + "".join(f"{c},{1 + i},n{i}\n" for i, c in enumerate("ABCABC"))
        roles, profile = roles_of("bar-basic"), profile_of(text)
        bindings = bind(category="Category", value="Amount")
        repeated = check_bindings(bindings, roles, profile).repeated_key
        assert repeated is not None
        held = valid_bindings(bindings, roles, profile)
        label = profile.columns[2]
        assert label.dtype == "text"

        assert (
            key_aggregate(
                [*held, ("label", DataRole("label", ("text",), False, False, "a note"), label)], repeated, "bar-basic"
            )
            is None
        )
        # An unbound text column leaves with the aggregate instead (its change line counts it).
        assert key_aggregate(held, repeated, "bar-basic") == KeyAggregate(("Category",), ("Amount",), "mean")

    def test_a_key_of_more_columns_than_an_aggregate_takes_is_left_to_the_user(self) -> None:
        repeated = RepeatedKey(roles=("a", "b", "c"), columns=("A", "B", "C"), values=2, combinations=8, rows=20)

        assert key_aggregate([], repeated, "sunburst-basic") is None

    def test_a_list_beside_the_rows_is_left_to_the_user(self) -> None:
        repeated = RepeatedKey(roles=("feature",), columns=("Feature",), values=3, combinations=3, rows=6)
        base = ColumnProfile(name="Base", dtype="number", missing=5, unique=1)
        held = [("base_value", DataRole("base_value", ("numeric",), True, False, "the base"), base)]

        assert key_aggregate(held, repeated, "shap-waterfall") is None

    def test_the_tables_name_keyed_specs_only_and_never_both(self) -> None:
        assert SUM_SPECS <= set(KEY_ROLES) and UNREDUCED_SPECS <= set(KEY_ROLES)
        assert not SUM_SPECS & UNREDUCED_SPECS

    def test_the_line_counts_the_rows_before_and_after_and_fits_a_change_note(self) -> None:
        aggregate = KeyAggregate(by=("Length",), values=("Reading",), how="mean")
        assert combined_line(aggregate, 27, 9, 2) == (
            f"{COMBINED_HEAD}2: averaged 'Reading' over 27 rows into 9, one per 'Length'"
        )

        summed = KeyAggregate(by=("Region", "Year"), values=tuple("ABC"), how="sum")
        assert combined_line(summed, 5_000, 12, 3) == (
            f"{COMBINED_HEAD}3: summed 3 columns over 5,000 rows into 12, one per 'Region' and 'Year'"
        )
        # Long value names are counted instead; key names too long to fit end in an ellipsis, the counts stand.
        wide = KeyAggregate(by=("Region",), values=("V" * 64, "W" * 64), how="mean")
        assert (
            combined_line(wide, 50, 5, 2)
            == f"{COMBINED_HEAD}2: averaged 2 columns over 50 rows into 5, one per 'Region'"
        )
        long = KeyAggregate(by=("K" * 64, "L" * 64), values=("V" * 64, "W" * 64), how="mean")
        clipped = combined_line(long, 20_000, 19_999, 6)
        assert len(clipped) == MAX_CHANGE_CHARS and clipped.endswith("…")
        assert "averaged 2 columns over 20,000 rows into 19,999, one per 'KKK" in clipped

    def test_a_column_bound_twice_is_one_value_and_more_than_ten_take_no_aggregate(self) -> None:
        repeated = RepeatedKey(roles=("x",), columns=("Step",), values=3, combinations=3, rows=9)
        step = ColumnProfile(name="Step", dtype="integer", missing=0, unique=3)
        value = ColumnProfile(name="Value", dtype="number", missing=0, unique=9)
        y, size = (DataRole(name, ("numeric",), True, False, name) for name in ("y", "size"))
        held = [
            ("x", DataRole("x", ("numeric",), True, False, "x", key=True), step),
            ("y", y, value),
            ("size", size, value),
        ]

        assert key_aggregate(held, repeated, "line-basic") == KeyAggregate(("Step",), ("Value",), "mean")

        many = [held[0], *((f"y{i}", y, value.model_copy(update={"name": f"V{i}"})) for i in range(11))]
        assert key_aggregate(many, repeated, "line-multi") is None

    def test_an_estimate_beside_its_interval_is_left_to_the_user(self) -> None:
        text = "X,Mean,Low,High\n" + "".join(f"{i % 3},{10 + i},{8 + i},{12 + i}\n" for i in range(6))

        assert self.aggregate_of("line-confidence", text, x="X", y="Mean", y_lower="Low", y_upper="High") is None


def test_the_key_table_marks_only_listed_roles() -> None:
    roles = [DataRole("x", ("numeric",), True, False, "x"), DataRole("y", ("numeric",), True, False, "y")]
    assert [role.key for role in mark_keys(roles, "line-basic")] == [True, False]
    assert [role.key for role in mark_keys(roles, "scatter-basic")] == [False, False]
