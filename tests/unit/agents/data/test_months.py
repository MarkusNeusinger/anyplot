"""Tests for agents/anyplot/data/months.py: a month and a year in one cell."""

import time

import pytest

from agents.anyplot.data.months import month_order, month_year


@pytest.mark.parametrize(
    ("cell", "expected"),
    [
        ("Nov 2026", (2026, 11)),
        ("November 2026", (2026, 11)),
        ("Okt. 2026", (2026, 10)),
        ("Nov-2026", (2026, 11)),
        ("Nov/2026", (2026, 11)),
        ("März 2026", (2026, 3)),
        ("Tháng 4/2026", (2026, 4)),
        ("tháng 3 năm 2026", (2026, 3)),
        ("2026年3月", (2026, 3)),
        ("2026 Nov", (2026, 11)),
        ("2026-Dez", (2026, 12)),
        ("  Nov 2026  ", (2026, 11)),
    ],
)
def test_a_month_and_a_year(cell: str, expected: tuple[int, int]) -> None:
    assert month_year(cell) == expected


@pytest.mark.parametrize(
    "cell",
    [
        "Nov2026",  # no separator before the year
        "Nov 12026",  # five digits
        "Nov 26",  # the century would be a guess
        "26 Nov 2026",  # a date, not a month
        "03/2026",  # a numeric format, read by its own rule
        "2026-03",
        "2026 2026",
        "Total 2026",
        "nam 2026",  # the Vietnamese word for a year alone names no month
        "- 2026",  # only a separator before the year
        "-2026",
        "2026",
        "",
    ],
)
def test_no_month_and_year(cell: str) -> None:
    assert month_year(cell) is None


@pytest.mark.parametrize(
    "cell",
    ["a" + "\t" * 200_000 + "x", "2026" + " " * 200_000, " -" * 200_000 + "2026"],
    ids=["tabs-inside", "spaces-after-a-year", "separators-before-a-year"],
)
def test_a_run_of_separators_costs_linear_time(cell: str) -> None:
    """CodeQL `py/polynomial-redos`: a lazy name before a run of separators took quadratic time in the regex it replaced."""
    started = time.monotonic()

    assert month_year(cell) is None
    assert time.monotonic() - started < 1


@pytest.mark.parametrize(
    ("months", "expected"),
    [
        ([1, 2, 3, 4], None),  # from January on
        ([1, 2, 11, 12], None),  # from January on, with a gap of more than half a year
        ([7, 8, 9, 10, 11, 12, 1, 2, 3, 4, 5, 6], None),  # a fiscal year
        ([11, 12, 1, 2], None),  # a winter, over the turn of the year
        ([10, 11, 12, 1, 2, 10, 11, 12, 1, 2], None),  # two winters: the second starts with the column's first month
        ([1, 2, 3, 1, 2, 3], None),  # two series, one after the other
        ([1, 1, 2, 2, 3, 3], None),  # two series, month by month
        ([1, None, 2, 3], None),  # an empty cell is no step
        ([1, 7, 8], None),  # half a year on is still forward
        ([12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1], "calendar"),  # a year backward: from January is its reverse
        ([4, 8, 12, 2, 1, 7, 6, 3, 5, 11, 10, 9], "calendar"),  # German month names by the alphabet
        ([6, 5, 4], "calendar"),  # backward within the year
        ([3, 2, 1, 3, 2, 1], "calendar"),  # two series, each backward
        ([2, 3, 1, 2, 3], "calendar"),  # the second series starts before the first did
        ([1, 2, 11, 12, 1, 2, 11, 12], None),  # two series with the same gap
        ([11, 12, 1, 2, 12, 1, 2], None),  # a second winter that starts a month later than the first
        ([3, 4, 5, 4, 5], None),  # a second series that starts a month later
        ([1, 2, 3, 2, 1, 3], None),  # passes that each leave months out
        ([4, 4, 8, 8, 12, 12, 2, 2, 1, 1], "calendar"),  # two series, month by month, by the alphabet
        ([4, 8, 12, 2], None),  # every fourth month, over the turn of the year
        ([3, 3, 2, 2, 1, 1], "calendar"),  # two series, month by month, backward within the year
        ([3, 2, 1, 12, 11, 10], "reversed"),  # the newest first, over the turn of the year
        ([2, 1, 12, 2, 1, 12], "reversed"),  # two winters, each the newest first
        ([2, 2, 1, 1, 12, 12], "reversed"),  # two series, month by month, the newest first
        ([2, None, 1, 12], "reversed"),
        ([3, 1, 2], "calendar"),  # back and forth
        ([3, 2, 8], "calendar"),  # half a year apart is forward, never a turn of the year gone back over
        ([1, 12, 2, 11], "calendar"),  # a zigzag is neither a run from January nor one over the turn of the year
        ([], None),
        ([None, None], None),
        ([5], None),
    ],
)
def test_the_order_a_plot_draws_month_names_in(months: list[int | None], expected: str | None) -> None:
    """Months that run along the calendar stand, a run that goes backward over the turn of the year is turned
    round, and anything else is ordered from January (`month_order`)."""
    assert month_order(months) == expected
