"""Tests for agents/anyplot/code/profiles/javascript/normalise.py: header, one orientation directive, the title."""

from collections import Counter

import pytest

from agents.anyplot.code.profiles.javascript.normalise import measure_canvas, normalise, normalise_report
from agents.anyplot.code.treesitter import Source, syntax_problems

from .conftest import JS_CATALOGUE, JS_CATALOGUE_FILES, JS_CATALOGUE_NORMALISED, js_library


HEADER = "// anyplot.ai\n// demo-basic: Demo\n// Library: d3 7.9.0 | JavaScript 22.22.3\n// Quality: 90/100 | Created: 2026-06-02\n"
BODY = 'const t = window.ANYPLOT_TOKENS;\nd3.select("#container").append("svg");\n'


def test_the_catalogue_file_in_miniature() -> None:
    report = normalise_report(JS_CATALOGUE)

    assert report.code == JS_CATALOGUE_NORMALISED
    assert report.changes == (
        "removed the catalogue header at lines 1-4",
        "emptied the catalogue title at line 23",  # each step counts the lines of the code it reads
    )
    assert report.notes == ()


def test_normalising_twice_changes_nothing() -> None:
    assert normalise(JS_CATALOGUE_NORMALISED) == JS_CATALOGUE_NORMALISED


def test_only_header_lines_go() -> None:
    code = HEADER + "\n// Data: kept\n" + BODY

    assert normalise(code, library="d3") == "//# anyplot-orientation: landscape\n// Data: kept\n" + BODY


def test_a_file_without_a_directive_gets_the_harness_default_written_out() -> None:
    report = normalise_report(HEADER + "\n" + BODY, library="d3")

    assert report.code == "//# anyplot-orientation: landscape\n" + BODY
    assert report.changes[-1] == (
        "wrote the harness's default orientation out as //# anyplot-orientation: landscape on line 1"
    )


@pytest.mark.parametrize(
    ("directive", "orientation"),
    [
        ("//# anyplot-orientation: square", "square"),
        ("// anyplot-orientation: square", "square"),
        ("//#   anyplot-orientation:  SQUARE", "square"),
        ("//# anyplot-orientation: landscape", "landscape"),
    ],
)
def test_the_directive_moves_to_the_first_line_in_its_canonical_form(directive: str, orientation: str) -> None:
    code = HEADER + "\n" + BODY + "\n" + directive + "\nconst after = 1;\n"
    normalised = normalise(code, library="d3")

    assert normalised.startswith(f"//# anyplot-orientation: {orientation}\n")
    assert normalised.count("anyplot-orientation") == 1
    assert measure_canvas(normalised, library="d3").pixels == (
        (2400, 2400) if orientation == "square" else (3200, 1800)
    )


def test_the_first_directive_decides_and_the_others_go() -> None:
    code = "//# anyplot-orientation: square\nconst a = 1;\n//# anyplot-orientation: landscape\n"

    assert normalise(code) == "//# anyplot-orientation: square\nconst a = 1;\n"


@pytest.mark.parametrize("separator", ["\r", "\r\n", chr(0x2028)])
def test_moving_a_directive_keeps_the_code_on_its_source_line(separator: str) -> None:
    """The directive after a lone `\\r` or U+2028 moves alone; the code that shares its `Source` line stays (Copilot
    review of #12473: the span was the whole `\\n` line)."""
    code = f"const a = 1;{separator}//# anyplot-orientation: square{separator}const b = 2;\n"
    newline = "\r\n" if separator == "\r\n" else "\n"  # the file's own line ending, where it uses `\r\n`

    assert normalise(code) == f"//# anyplot-orientation: square{newline}const a = 1;{separator}const b = 2;\n"
    assert normalise(normalise(code)) == normalise(code)


def test_a_directive_in_a_string_is_left_alone_with_a_note() -> None:
    code = "const s = `\n//# anyplot-orientation: square\n`;\n"
    report = normalise_report(code)

    assert report.code == code
    assert report.notes == (
        "orientation: the directive the harness reads stands at line 2 outside a comment of its own; left alone",
    )


@pytest.mark.parametrize(
    ("title", "blank"),
    [
        ('"bar-basic · javascript · chartjs · anyplot.ai"', '""'),
        ("'bar-basic · javascript · chartjs · anyplot.ai'", '""'),
        ("`Revenue by quarter · bar-basic · javascript · d3 · anyplot.ai`", '""'),
        ("`${SYMBOL} · bar-basic · javascript · muix · anyplot.ai`", None),
        ('"Revenue by quarter"', None),
    ],
)
def test_catalogue_titles_become_empty(title: str, blank: str | None) -> None:
    code = f"const SYMBOL = 1;\nconst TITLE = {title};\n"
    normalised = normalise(code)

    assert normalised.endswith(f"const TITLE = {blank or title};\n")


def test_a_jsx_title_becomes_an_empty_expression() -> None:
    code = (
        "export default function Chart() {\n"
        "  return (\n"
        "    <Typography sx={{ fontSize: 22 }}>\n"
        "      bar-basic · javascript · muix · anyplot.ai\n"
        "    </Typography>\n"
        "  );\n"
        "}\n"
    )
    normalised = normalise(code, library="muix")

    assert '      {""}\n' in normalised
    assert "anyplot.ai" not in normalised
    assert not syntax_problems(Source(normalised, "tsx").tree)


def test_code_that_does_not_parse_is_returned_unchanged() -> None:
    code = "const a = (;\n"
    report = normalise_report(code)

    assert report.code == code and report.notes == ("syntax: unexpected code at line 1; nothing was normalised",)


@pytest.mark.parametrize(
    "body",
    [
        "",
        "\n\n",
        "// anyplot.ai\n",
        "x = 1\r\ny = 2\r\n",
        "//# anyplot-orientation: square",
        "const x = 1" + "0" * 5000 + ";\n",
        "const s = '" + "a" * 20_000 + "';\n",
        "/* //# anyplot-orientation: square */\n",
        "const d = { 'anyplot-orientation': 1 };\n",
    ],
)
def test_the_normaliser_never_raises(body: str) -> None:
    for library in ("chartjs", "muix"):
        once = normalise(body, library=library)
        assert normalise(once, library=library) == once


def test_catalogue_corpus() -> None:
    """All 1,617 files: every result parses, is idempotent and starts with its directive; 3 titles in a template with
    a substitution stay (indicator-bollinger and indicator-sma in MUI X, map-marker-clustered in D3)."""
    changes: Counter[str] = Counter()
    kept_titles: list[str] = []
    for path in JS_CATALOGUE_FILES:
        library = js_library(path)
        report = normalise_report(path.read_text(encoding="utf-8"), library=library)
        grammar = "tsx" if library == "muix" else "javascript"
        assert not syntax_problems(Source(report.code, grammar).tree), path
        assert normalise(report.code, library=library) == report.code, path
        assert report.code.startswith("//# anyplot-orientation: "), path
        assert report.notes == (), path
        changes.update(change.split(" at ")[0].split(" from ")[0] for change in report.changes)
        if not any(change.startswith("emptied the catalogue title") for change in report.changes):
            kept_titles.append(f"{path.parts[-4]}/{library}")

    assert changes == {
        "removed the catalogue header": 1617,
        "emptied the catalogue title": 1614,
        "wrote the harness's default orientation out as //# anyplot-orientation: landscape on line 1": 893,
        "moved the orientation directive (landscape)": 1,
    }
    assert sorted(kept_titles) == ["indicator-bollinger/muix", "indicator-sma/muix", "map-marker-clustered/d3"]
