"""Tests for automation.scripts.impl_header — the JavaScript header writer.

impl-review.yml's "Update metadata and implementation header" step calls
``replace_js_header``; tests/unit/workflows/test_impl_header_step.py runs the
step's script end to end. The fixtures follow the shapes found in the
catalogue on 2026-10-24.
"""

from __future__ import annotations

import pytest

from automation.scripts.impl_header import is_directive, replace_js_header


HEADER = (
    "// anyplot.ai\n"
    "// gauge-basic: Basic Gauge Chart\n"
    "// Library: d3 7.9.0 | JavaScript 22.23.3\n"
    "// Quality: 93/100 | Updated: 2026-10-24"
)
OLD = "// anyplot.ai\n// gauge-basic: Basic Gauge Chart\n// Library: d3 7.9.0 | JavaScript 22.23.1\n// Quality: 90/100 | Created: 2026-06-30\n"
GENERATED = (
    "// anyplot.ai\n"
    "// gauge-basic: Basic Gauge Chart\n"
    "// Library: MUI X Charts | React | Node 22\n"
    "// License: @mui/x-charts - MIT (community). Pro/Premium are out of scope.\n"
    "// Quality: pending | Created: 2026-06-30\n"
)
SQUARE = "//# anyplot-orientation: square\n"
CODE = "const t = window.ANYPLOT_TOKENS;\nconst value = 68;\n"


def _out(*parts: str) -> str:
    return HEADER + "\n" + "".join(parts)


def _header_count(text: str) -> int:
    return sum(1 for line in text.splitlines()[:20] if line == "// anyplot.ai")


SHAPES = {
    # (a) The prompts' old advice: the directive on line 1, the header below it.
    "directive_first": (SQUARE + GENERATED + "\n" + CODE, _out(SQUARE, "\n", CODE)),
    "directive_first_blank_before_header": (SQUARE + "\n" + GENERATED + "\n" + CODE, _out(SQUARE, "\n", CODE)),
    "two_directives_first": (
        SQUARE + "//# anyplot-other: x\n" + GENERATED + CODE,
        _out(SQUARE, "//# anyplot-other: x\n", CODE),
    ),
    # (b) The canonical shape: the header first, the directive directly below.
    "header_then_directive": (OLD + SQUARE + "\n" + CODE, _out(SQUARE, "\n", CODE)),
    "generated_header_then_directive": (GENERATED + SQUARE + CODE, _out(SQUARE, CODE)),
    # (c) What the old prepend fallback left: a stale block below the directive.
    "stale_block": (OLD + SQUARE + GENERATED + "\n" + CODE, _out(SQUARE, "\n", CODE)),
    "stale_block_no_blank": (OLD + SQUARE + GENERATED + CODE, _out(SQUARE, CODE)),
    "stale_block_after_blank": (OLD + SQUARE + "\n" + GENERATED + "\n" + CODE, _out(SQUARE, "\n", CODE)),
    "two_stale_blocks": (OLD + SQUARE + OLD + GENERATED + "\n" + CODE, _out(SQUARE, "\n", CODE)),
    "directive_first_with_stale_block": (SQUARE + OLD + GENERATED + "\n" + CODE, _out(SQUARE, "\n", CODE)),
    # Neither: no directive, or no header at all.
    "header_only": (OLD + "\n" + CODE, _out("\n", CODE)),
    "no_header": (CODE, _out(CODE)),
    "directive_only": (SQUARE + CODE, _out(SQUARE, CODE)),
}


class TestShapes:
    @pytest.mark.parametrize(("before", "after"), SHAPES.values(), ids=SHAPES.keys())
    def test_one_header_on_line_1(self, before, after):
        out = replace_js_header(before, HEADER)
        assert out == after
        assert out.startswith(HEADER + "\n")
        assert _header_count(out) == 1

    @pytest.mark.parametrize("before", [before for before, _ in SHAPES.values()], ids=SHAPES.keys())
    def test_idempotent(self, before):
        once = replace_js_header(before, HEADER)
        assert replace_js_header(once, HEADER) == once

    @pytest.mark.parametrize("before", [before for before, _ in SHAPES.values()], ids=SHAPES.keys())
    def test_directives_survive_in_order(self, before):
        out = replace_js_header(before, HEADER)
        assert [line for line in out.splitlines() if is_directive(line)] == [
            line for line in before.splitlines() if is_directive(line)
        ]


class TestWhatStays:
    def test_comments_after_the_stale_quality_line_stay(self):
        notes = "//\n// MUI X community has no chord primitive, so the diagram is drawn by hand.\n"
        before = OLD + SQUARE + GENERATED + notes + "\n" + CODE
        assert replace_js_header(before, HEADER) == _out(SQUARE, notes, "\n", CODE)

    def test_comments_after_the_header_quality_line_stay(self):
        notes = "// Data: a fixed 68 % completion.\n"
        assert replace_js_header(SQUARE + GENERATED + notes + CODE, HEADER) == _out(SQUARE, notes, CODE)

    def test_a_directive_below_a_blank_line_keeps_its_place(self):
        before = OLD + "\n" + SQUARE + "\n" + CODE
        assert replace_js_header(before, HEADER) == _out("\n", SQUARE, "\n", CODE)

    def test_comments_below_the_directive_stay(self):
        notes = "//\n// ECharts has no native maze primitive.\n"
        before = OLD + SQUARE + notes + "\n" + CODE
        assert replace_js_header(before, HEADER) == _out(SQUARE, notes, "\n", CODE)

    def test_an_anyplot_header_below_code_is_not_touched(self):
        later = "\n// anyplot.ai\n// Quality: pending | Created: 2026-06-30\n"
        before = OLD + SQUARE + CODE + later
        assert replace_js_header(before, HEADER) == _out(SQUARE, CODE, later)

    def test_a_comment_mentioning_anyplot_is_no_header(self):
        note = "// anyplot.ai renders this in two themes\n"
        before = OLD + SQUARE + note + CODE
        assert replace_js_header(before, HEADER) == _out(SQUARE, note, CODE)

    def test_a_leading_comment_without_quality_line_is_replaced_whole(self):
        # The writer's behaviour before 2026-10-24: the whole leading run.
        before = "// Basic gauge\n// drawn with d3\n" + CODE
        assert replace_js_header(before, HEADER) == _out(CODE)

    def test_crlf_directive_and_code_stay(self):
        before = "//# anyplot-orientation: square\r\n// anyplot.ai\r\n// Quality: pending\r\nconst a = 1;\r\n"
        assert replace_js_header(before, HEADER) == HEADER + "\n//# anyplot-orientation: square\r\nconst a = 1;\r\n"

    def test_a_file_of_only_header_and_directive(self):
        assert replace_js_header(OLD + "//# anyplot-orientation: square", HEADER) == _out(SQUARE.rstrip("\n"))


@pytest.mark.parametrize(
    ("line", "expected"),
    [("//# anyplot-orientation: square", True), ("// # not a directive", False), ("// anyplot.ai", False)],
)
def test_is_directive(line, expected):
    assert is_directive(line) is expected
