"""Tests for automation.scripts.close_issue_if_complete (shared by impl-merge and impl-review)."""

from __future__ import annotations

from automation.scripts.close_issue_if_complete import completion_comment, completion_status


LIBS = ["altair", "bokeh", "d3"]


def test_incomplete_when_a_library_is_missing():
    status = completion_status(["impl:altair:done", "impl:bokeh:done", "impl:d3:pending"], LIBS)
    assert not status.complete
    assert status.done == ["altair", "bokeh"]


def test_complete_with_done_and_failed():
    status = completion_status(["impl:altair:done", "impl:bokeh:failed", "impl:d3:done"], LIBS)
    assert status.complete
    assert status.failed == ["bokeh"]


def test_done_wins_over_failed():
    status = completion_status(["impl:altair:done", "impl:altair:failed", "impl:bokeh:done", "impl:d3:done"], LIBS)
    assert status.complete
    assert status.failed == []


def test_empty_library_list_is_never_complete():
    assert not completion_status(["impl:altair:done"], []).complete


def test_comment_all_done():
    status = completion_status([f"impl:{lib}:done" for lib in LIBS], LIBS)
    body = completion_comment(status, "scatter-basic", "https://example/run/1", "impl-merge")
    assert ":tada: All Implementations Complete!" in body
    assert "All 3 library implementations for `scatter-basic`" in body
    assert "| d3 | :white_check_mark: |" in body
    assert body.endswith(":robot: *[impl-merge](https://example/run/1)*")


def test_comment_with_failures():
    status = completion_status(["impl:altair:done", "impl:bokeh:failed", "impl:d3:done"], LIBS)
    body = completion_comment(status, "scatter-basic", "https://example/run/1", "impl-review")
    assert "2/3 implementations merged, 1 libraries could not implement" in body
    assert "| bokeh | :x: (not supported) |" in body
