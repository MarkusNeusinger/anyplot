"""Tests for agents/anyplot/data/bounds.py: the lower and upper bound pairs of the specs, and the inverted check."""

from pathlib import Path

import pytest

from agents.anyplot.data.bounds import BoundPair, bound_pairs, inverted, inverted_line, ordered
from agents.anyplot.schemas import ColumnDtype, ColumnProfile
from core.spec_roles import DataRole, data_bullets, parse_roles


PLOTS = Path(__file__).resolve().parents[4] / "plots"


def roles_of(spec_id: str) -> list[DataRole]:
    return parse_roles(data_bullets((PLOTS / spec_id / "specification.md").read_text(encoding="utf-8")))


def number(name: str, low: float, high: float, dtype: ColumnDtype = "number") -> ColumnProfile:
    return ColumnProfile(name=name, dtype=dtype, missing=0, unique=3, min=low, max=high)


@pytest.mark.parametrize(
    ("spec_id", "pairs"),
    [
        ("range-interval", [("min_value", "max_value")]),
        ("gauge-basic", [("min_value", "max_value")]),
        ("forest-basic", [("ci_lower", "ci_upper")]),
        ("line-confidence", [("y_lower", "y_upper")]),
        ("point-basic", [("lower_bound", "upper_bound")]),
        ("candlestick-basic", [("low", "high")]),
        ("timeseries-forecast-uncertainty", [("lower_80", "upper_80"), ("lower_95", "upper_95")]),
        ("indicator-bollinger", [("lower_band", "upper_band")]),
        ("spc-xbar-r", [("lcl", "ucl"), ("lower_warning", "upper_warning")]),
        ("heatmap-mandelbrot", [("x_min", "x_max"), ("y_min", "y_max")]),
        ("bar-heart-rate-zones", [("hr_low", "hr_high")]),
    ],
)
def test_the_pairs_come_from_the_specs_role_names(spec_id: str, pairs: list[tuple[str, str]]) -> None:
    assert sorted((pair.lower, pair.upper) for pair in bound_pairs(roles_of(spec_id))) == sorted(pairs)


@pytest.mark.parametrize(
    "spec_id",
    [
        "errorbar-asymmetric",  # error magnitudes below and above a point, each of any size
        "bar-tornado-sensitivity",  # outcomes of a low and a high scenario: the low one may be the larger
        "area-stacked-confidence",  # families take their members in column order
        "gantt-basic",  # a start and an end are no bound words
        "dumbbell-basic",
    ],
)
def test_no_pair_where_the_values_are_no_bounds(spec_id: str) -> None:
    assert bound_pairs(roles_of(spec_id)) == []


def test_every_pair_of_the_catalogue_is_two_single_number_roles() -> None:
    for specification in sorted(PLOTS.glob("*/specification.md")):
        roles = {role.name: role for role in roles_of(specification.parent.name)}
        for pair in bound_pairs(list(roles.values())):
            for name in (pair.lower, pair.upper):
                assert not roles[name].variadic and "numeric" in roles[name].kinds, (specification, name)


class TestInverted:
    def test_a_count_above_an_average_is_inverted(self) -> None:
        assert inverted(number("games", 140, 146, "integer"), number("mean", 61.5, 67.2))

    @pytest.mark.parametrize(
        ("lower", "upper"),
        [
            (number("lo", 1, 50), number("hi", 40, 90)),  # overlapping ranges: some rows may still be right
            (number("lo", 5, 5), number("hi", 5, 5)),  # equal ends are a range of one value
        ],
    )
    def test_ranges_that_can_hold_are_not(self, lower: ColumnProfile, upper: ColumnProfile) -> None:
        assert not inverted(lower, upper)

    def test_the_parts_of_one_split_must_be_ordered_at_both_ends(self) -> None:
        assert ordered(number("lo", 12, 17), number("hi", 18, 22))
        assert ordered(number("lo", 5, 5), number("hi", 5, 5))
        assert not ordered(number("hi", 17, 22), number("lo", 12, 18))  # overlapping, yet high before low
        assert not inverted(number("hi", 17, 22), number("lo", 12, 18))  # which the default rule lets pass

    def test_only_number_columns_are_compared(self) -> None:
        text = ColumnProfile(name="t", dtype="text", missing=0, unique=3, top=["b", "c"])
        assert not inverted(text, number("hi", 1, 2))

    def test_the_warning_is_one_neutral_line(self) -> None:
        """It says what the plot will show and asks for nothing: a range bound high to low may be meant."""
        line = inverted_line(
            BoundPair("min_value", "max_value"), number("games", 140.0, 146.0), number("mean", 61.5, 67.2)
        )

        assert line == (
            "min_value and max_value: every value of 'games' (from 140) lies above every value of 'mean' (up to "
            "67.2), so each row's lower bound is above its upper bound"
        )
        assert "bind" not in line and ";" not in line
