"""Tests for agents/anyplot/code/profiles/javascript/regions.py: the conventions of the JavaScript catalogue."""

import re
from collections import Counter

import pytest

from agents.anyplot.code.profiles.javascript.regions import LIBRARIES, find_directives, find_regions, grammar_for
from agents.anyplot.code.treesitter import Source

from .conftest import JS_CATALOGUE_FILES, JS_CATALOGUE_NORMALISED, JS_WORKING, MUIX_WORKING, js_library


def test_the_miniature_regions() -> None:
    regions = find_regions(JS_CATALOGUE_NORMALISED)

    assert [region.name for region in regions.theme_tokens] == ["t", "width, height", "isDark", "MUTED"]
    assert regions.orientation == "square"
    assert regions.save is not None and regions.save.span.first_line == 1
    assert [(column.name, column.role) for column in regions.columns] == [("SPEND", "x"), ("REVENUE", "y")]
    assert regions.data_marker is not None and regions.plot_marker is not None
    assert regions.reads_theme and regions.imprint is None and regions.placeholders == ()


def test_the_working_form_holds_the_placeholder_and_protects_it() -> None:
    regions = find_regions(JS_WORKING)

    assert [region.statement.lines() for region in regions.placeholders if region.statement] == ["line 13"]
    assert [region.kind for region in regions.protected] == ["savefig", *["theme_token"] * 4, "placeholder"]


def test_muix_imports_and_typed_constants() -> None:
    regions = find_regions(MUIX_WORKING, library="muix")

    assert [(module.specifier, module.names) for module in regions.imports] == [
        ("@mui/x-charts/ScatterChart", ("ScatterChart",)),
        ("@mui/material/Typography", ("default",)),
    ]
    assert [column.name for column in regions.columns] == ["X", "Y"]
    assert regions.orientation == "landscape"


@pytest.mark.parametrize(
    "line",
    [
        "const t = window.ANYPLOT_TOKENS;",
        "const tokens = window.ANYPLOT_TOKENS;",
        "const { width, height } = window.ANYPLOT_SIZE;",
        "const { width: W, height: H } = window.ANYPLOT_SIZE;",
        "const W = window.ANYPLOT_SIZE.width;",
        "const HALF = window.ANYPLOT_SIZE.width / 2;",
        'const THEME = window.ANYPLOT_THEME || "light";',
        'const isDark = window.ANYPLOT_THEME === "dark";',
        'const MUTED = window.ANYPLOT_THEME === "dark" ? "#A8A79F" : "#6B6A63";',
        "const size = window.ANYPLOT_SIZE || { width: 1600, height: 900 };",
        'let theme = window["ANYPLOT_THEME"];',
    ],
)
def test_token_lines(line: str) -> None:
    regions = find_regions(line + "\n")

    assert len(regions.theme_tokens) == 1, regions.theme_tokens


@pytest.mark.parametrize(
    "line",
    [
        "const p = t.palette;",
        "const C = [t.palette[0], t.palette[1]];",
        "const chartHeight = window.ANYPLOT_SIZE.height - TITLE_HEIGHT;",
        "const data = window.ANYPLOT_DATA;",
        "const opened = window.open;",
        "const lower = window.ANYPLOT_THEME.toLowerCase();",
        "const copy = [...window.ANYPLOT_TOKENS.palette];",
        "const { width = 1 } = window.ANYPLOT_SIZE;",
        "const a = window.ANYPLOT_SIZE.width, b = 2;",
    ],
)
def test_lines_that_are_plot_code(line: str) -> None:
    code = "const t = window.ANYPLOT_TOKENS;\nconst TITLE_HEIGHT = 40;\n" + line + "\n"

    assert [region.name for region in find_regions(code).theme_tokens] == ["t"]


def test_a_theme_test_through_an_earlier_token_is_a_token() -> None:
    code = 'const isDark = window.ANYPLOT_THEME === "dark";\nconst MUTED = isDark ? "#A8A79F" : "#6B6A63";\n'

    assert [region.name for region in find_regions(code).theme_tokens] == ["isDark", "MUTED"]


def test_a_token_inside_a_function_is_plot_code() -> None:
    code = "function Chart() {\n  const { width, height } = window.ANYPLOT_SIZE;\n  return width;\n}\n"

    assert find_regions(code).theme_tokens == ()


@pytest.mark.parametrize(
    ("code", "found"),
    [
        ("//# anyplot-orientation: square\n", [("square", 1, True)]),
        ("// anyplot-orientation: square\n", [("square", 1, True)]),
        ("x = 1;\n  //#  anyplot-orientation:   Landscape  (16:9)\n", [("landscape", 2, True)]),
        ('const s = "x\\n";\nconst t = `\n//# anyplot-orientation: square\n`;\n', [("square", 3, False)]),
        ("/*\n//# anyplot-orientation: square\n*/\n", [("square", 2, False)]),
        ("x = 1; //# anyplot-orientation: square\n", []),
        ("//# anyplot-orientation: squares\n", []),
        (
            "//# anyplot-orientation: square\n//# anyplot-orientation: landscape\n",
            [("square", 1, True), ("landscape", 2, True)],
        ),
    ],
)
def test_directives_as_the_harness_reads_them(code: str, found: list[tuple[str, int, bool]]) -> None:
    directives = find_directives(Source(code, "javascript"))

    assert [(directive.orientation, directive.line, directive.comment) for directive in directives] == found


@pytest.mark.parametrize("separator", ["\r", chr(0x2028), chr(0x2029)])
def test_a_directive_spans_its_javascript_line_alone(separator: str) -> None:
    """A lone `\\r`, U+2028 or U+2029 ends a JavaScript line but no `Source` line: the directive's span is its own
    JavaScript line, so the code before and after it on the same `Source` line stays (Copilot review of #12473)."""
    code = f"const a = 1;{separator}//# anyplot-orientation: square{separator}const b = 2;\n"
    source = Source(code, "javascript")
    (directive,) = find_directives(source)

    assert directive.comment and directive.orientation == "square" and directive.line == 1
    assert code[directive.span.start : directive.span.end] == f"//# anyplot-orientation: square{separator}"
    regions = find_regions(source)
    assert regions.save is not None and regions.save.span == directive.span


def test_a_directive_after_a_line_separator_is_read_as_the_harness_does() -> None:
    """JavaScript's multi-line `^` matches after U+2028 too, so a directive there counts."""
    code = 'const s = "a' + chr(0x2028) + '//# anyplot-orientation: square";\n'

    assert [directive.comment for directive in find_directives(Source(code, "javascript"))] == [False]


def test_grammar_for_each_library() -> None:
    assert {library: grammar_for(library) for library in LIBRARIES} == {
        "chartjs": "javascript",
        "d3": "javascript",
        "echarts": "javascript",
        "highcharts": "javascript",
        "muix": "tsx",
    }
    with pytest.raises(ValueError, match="no JavaScript library"):
        grammar_for("plotly")


HARNESS_ORIENTATION = re.compile(
    r"^\s*//#?\s*anyplot-orientation:\s*(square|landscape)\b", re.IGNORECASE | re.MULTILINE
)
"""The harness's own reading of the directive (`orientationFromSource` in `automation/js-render/render.mjs`)."""
TOKEN_LINE = re.compile(r"^const t = window\.ANYPLOT_TOKENS;", re.MULTILINE)
DATA_LINE = re.compile(r"^// Data\b", re.MULTILINE)
PLOT_LINE = re.compile(r"^// Plot\b", re.MULTILINE)
COLUMN_LINE = re.compile(r'^const ([A-Z][A-Z0-9_]*)(?::\s*string)? = "[^"\n]*";\s*// role: \w+\s*$', re.MULTILINE)
IMPRINT_LINE = re.compile(r"^(?:const|let|var) (?:IMPRINT|IMPRINT_PALETTE)\b", re.MULTILINE)


def test_catalogue_corpus() -> None:
    """The conventions of every catalogue file (module docstring), each found where the file's text has it and only
    there. The counts of a day (1,617 files on 2026-10-30: the `t` token in 1,602, a directive in 724, the markers in
    1,344 and 134, column constants in 121, no palette written out) move with every regeneration, so each detection
    is held to a plain reading of the text instead, and to the harness's own pattern for the directive."""
    found: Counter[str] = Counter()
    for path in JS_CATALOGUE_FILES:
        text = path.read_text(encoding="utf-8")
        regions = find_regions(text, library=js_library(path))
        lines = text.splitlines()
        name = path.parts[-4] + "/" + js_library(path)
        assert regions.reads_theme, name  # the harness themes every file through its globals
        assert ("t" in [region.name for region in regions.theme_tokens]) == bool(TOKEN_LINE.search(text)), name
        assert len(regions.directives) == len(HARNESS_ORIENTATION.findall(text)) <= 1, name
        assert all(directive.comment for directive in regions.directives), name
        for marker, word, canonical in (
            (regions.data_marker, "Data", DATA_LINE),
            (regions.plot_marker, "Plot", PLOT_LINE),
        ):
            assert marker is not None or not canonical.search(text), (name, word)
            assert marker is None or re.match(rf"//.*\b{word}\b", lines[marker.line - 1]), (name, word)
            found[word] += marker is not None
        assert set(COLUMN_LINE.findall(text)) <= {column.name for column in regions.columns}, name
        for column in regions.columns:
            statement = "\n".join(lines[column.span.first_line - 1 : column.span.last_line])
            assert f"// role: {column.role}" in statement and column.name in statement, (name, column.name)
        found["columns"] += bool(regions.columns)
        assert (regions.imprint is not None) == bool(IMPRINT_LINE.search(text)), name

    assert all(found[kind] for kind in ("Data", "Plot", "columns")), found  # the conventions are in use at all
