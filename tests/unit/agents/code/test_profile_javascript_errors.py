"""Tests for agents/anyplot/code/profiles/javascript/errors.py: the harness's final error line, read without its message.

The samples are the last lines on stderr of real failed renders, through the harness's sandbox mode
(`automation/js-render/render.mjs`, Node 24, the lock's packages and Playwright's headless shell) on 2026-10-30.
"""

import pytest

from agents.anyplot.code.profiles.javascript.errors import NO_ERROR_OUTPUT, NO_FINAL_LINE, error_summary, working_line
from agents.anyplot.code.profiles.javascript.loader import loader_span, to_run_form

from .conftest import JS_WORKING


SAMPLES = {
    "undefined data": (
        "render: error: page TypeError plot.js:4: Cannot read properties of undefined (reading 'map')",
        "TypeError at line 4",
    ),
    "unbound name": (
        "render: error: page ReferenceError plot.js:5: missingLabels is not defined",
        "ReferenceError at line 5",
    ),
    "a script that does not parse": (
        "render: error: page SyntaxError plot.js:3: Unexpected token ';'",
        "SyntaxError at line 3",
    ),
    "a class of the snippet's own": ("render: error: page Berlin4711 plot.js:3: Berlin 4711", "an error at line 3"),
    "nothing drawn": (
        "render: error: draw NoOutput -: snippet did not draw into #container (no <canvas>/<svg> mounted).",
        "nothing drawn: the page has no canvas, svg or img in #container",
    ),
    "an import off the allowlist": (
        'render: error: import ImportRefused plot.tsx:2: import "@mui/x-charts/ChartContainer" refused: it is not '
        "on the image's import allowlist",
        "an import the image refuses (only the allowlisted React and MUI modules) at line 2",
    ),
    "a name MUI X 9 does not export": (
        'render: error: import ImportNotFound plot.tsx:2: No matching export in "node_modules/@mui/x-charts/'
        'index.mjs" for import "ChartContainer"',
        "an import the image's MUI X does not export at line 2",
    ),
    "a TSX syntax error": ('render: error: build SyntaxError plot.tsx:4: Unexpected ";"', "a syntax error at line 4"),
    "a MUI X error through the source map": (
        "render: error: page TypeError plot.tsx:7: Cannot read properties of undefined (reading 'map')",
        "TypeError at line 7",
    ),
    "a broken data file": (
        "render: error: data DataError -: the data file /work/data.json is unreadable: Unexpected token 'o'",
        "the data file could not be read (a pipeline fault, not the code)",
    ),
    "a page that never settles": (
        "render: error: timeout TimeoutError -: the page did not settle within 15 s",
        "the page did not settle within 15 s (a loop that does not end, or a ready signal never set)",
    ),
}


@pytest.mark.parametrize(("stderr", "summary"), SAMPLES.values(), ids=SAMPLES.keys())
def test_real_final_lines(stderr: str, summary: str) -> None:
    assert error_summary(stderr) == summary


def test_only_the_last_line_counts() -> None:
    """The console summary above the final line holds what the snippet printed, which can mimic a final line."""
    stderr = (
        "render: 7 console error(s) during render, the first 5:\n"
        "  render: error: page RangeError plot.js:1: Hamburg 0\n"
        "  render: error: page RangeError plot.js:1: Hamburg 1\n"
        "render: error: page RangeError plot.js:4: Invalid array length\n"
    )

    assert error_summary(stderr) == "RangeError at line 4"
    assert error_summary(stderr.rsplit("render: error: page RangeError plot.js:4", 1)[0]) == NO_FINAL_LINE


def test_a_thrown_value_without_a_frame_drops_the_wrappers_line() -> None:
    """`throw "a plain string"` in a three-line snippet: the harness names its own wrapper's line 7."""
    stderr = "render: error: page Error plot.js:7: a plain string\n"

    assert error_summary(stderr) == "Error at line 7"
    assert error_summary(stderr, line_count=3) == "Error"


@pytest.mark.parametrize(
    ("line_count", "summary"), [(6, "TypeError"), (7, "TypeError at line 7"), (40, "TypeError at line 7")]
)
def test_line_count_drops_only_a_line_past_the_codes_end(line_count: int, summary: str) -> None:
    assert error_summary("render: error: page TypeError plot.js:7: x\n", line_count=line_count) == summary


@pytest.mark.parametrize(
    ("stderr", "summary"),
    [
        ("", NO_ERROR_OUTPUT),
        ("\n  \n", NO_ERROR_OUTPUT),
        ("Killed\n", NO_FINAL_LINE),
        (
            "render: error: harness UsageError -: implementation file not found",
            "a harness error (a toolchain fault, not the code)",
        ),
        (
            "render: error: harness AllowlistError -: the import allowlist is unreadable",
            "a harness error (a toolchain fault, not the code)",
        ),
        (
            "render: error: build BuildError -: esbuild failed",
            "a build error outside the plot's code (a toolchain fault, not the code)",
        ),
        ("render: error: crash PageCrashed -: the page crashed", "the page crashed (out of memory, most likely)"),
        ("render: error: page TypeError other.js:3: x", "TypeError"),
        ("render: error: novel Thing plot.js:3: x", "an error at line 3"),
    ],
)
def test_fixed_texts(stderr: str, summary: str) -> None:
    assert error_summary(stderr) == summary


def test_the_message_never_reaches_the_summary() -> None:
    stderr = "render: error: page TypeError plot.js:9: Cannot read properties of 'Patient Müller, 1962-04-01'\n"

    assert "Müller" not in error_summary(stderr) and "1962" not in error_summary(stderr)


@pytest.mark.parametrize(
    ("line", "expected"), [(5, (5, False)), (13, (13, True)), (14, (14, False)), (40, (40, False))]
)
def test_run_form_lines_map_to_the_working_form(line: int, expected: tuple[int, bool]) -> None:
    """The loader is one line for one line, so a line maps to itself, and the loader's own is the data loader."""
    assert working_line(line, loader_span(to_run_form(JS_WORKING))) == expected


def test_the_summary_names_the_data_loader() -> None:
    loader = loader_span(to_run_form(JS_WORKING))

    assert error_summary("render: error: page TypeError plot.js:13: x", loader=loader) == (
        "TypeError at line 13 (the data loader)"
    )
    assert error_summary("render: error: page TypeError plot.js:20: x", loader=loader) == "TypeError at line 20"
