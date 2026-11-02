"""Tests for agents/anyplot/data/months.py: a month and a year in one cell."""

import time

import pytest

from agents.anyplot.data.months import month_year


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
