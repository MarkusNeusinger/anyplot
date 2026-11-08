"""The version rule of the plot votes (`core/plot_votes.py`)."""

from datetime import UTC, datetime, timedelta, timezone

from core.plot_votes import PLOT_VOTE_REACTIONS, naive_utc, on_current_version


START = datetime(2026, 11, 8, 4, 54, 13)  # naive UTC, as `impls.updated` stores it


def test_the_plot_vote_reactions_are_the_two_thumbs() -> None:
    assert PLOT_VOTE_REACTIONS == ("thumbs_up", "thumbs_down")


def test_naive_utc_keeps_a_naive_value_and_converts_an_aware_one() -> None:
    assert naive_utc(START) == START
    assert naive_utc(START.replace(tzinfo=UTC)) == START
    vienna = timezone(timedelta(hours=1))
    assert naive_utc(datetime(2026, 11, 8, 5, 54, 13, tzinfo=vienna)) == START


def test_a_vote_from_the_start_on_is_on_the_current_version() -> None:
    assert on_current_version(START, START)  # in the second the version began
    assert on_current_version(START + timedelta(days=1), START)
    assert not on_current_version(START - timedelta(seconds=1), START)
    # naive and aware sides compare as the same UTC moment
    assert on_current_version(START, START.replace(tzinfo=UTC))
    assert not on_current_version((START - timedelta(seconds=1)).replace(tzinfo=UTC), START)


def test_without_a_start_every_vote_is_on_the_one_version() -> None:
    assert on_current_version(datetime(2020, 1, 1), None)
