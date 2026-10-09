"""Tests for agents/anyplot/code/regions.py: spans of the catalogue conventions."""

import ast

import pytest

from agents.anyplot.code.regions import (
    SourceIndex,
    Span,
    dotted_name,
    find_regions,
    is_standard_target,
    is_theme_assignment,
)
from agents.anyplot.code.regions import tests_theme as value_tests_theme  # not named test* for pytest

from .conftest import CATALOGUE, source


def text(code: str, span: Span) -> str:
    return code[span.start : span.end]


def test_theme_block_tokens_palette_and_savefig() -> None:
    regions = find_regions(CATALOGUE)

    assert regions.theme is not None
    assert text(CATALOGUE, regions.theme.span) == 'THEME = os.getenv("ANYPLOT_THEME", "light")\n'
    assert [token.name for token in regions.theme_tokens] == ["PAGE_BG", "INK"]
    assert regions.theme_tokens[0].span.first_line == regions.theme.span.first_line + 1
    assert regions.imprint is not None
    assert regions.imprint.name == "IMPRINT"
    assert regions.imprint.entries == ("#009E73", "#C475FD", "#4467A3")
    assert regions.savefig is not None
    assert regions.savefig.standard_target
    assert regions.savefig.literal_target is None
    assert text(CATALOGUE, regions.savefig.statement or regions.savefig.span).startswith("plt.savefig(")
    assert regions.savefig.dpi is not None and regions.savefig.dpi.value == 300
    assert [kw.name for kw in regions.savefig.keywords] == ["dpi", "bbox_inches", "facecolor"]


def test_protected_regions_are_whole_lines_and_exclude_the_palette() -> None:
    regions = find_regions(CATALOGUE)
    protected = regions.protected

    assert [region.kind for region in protected] == ["theme", "theme_token", "theme_token", "savefig"]
    for region in protected:
        assert region.span.start == 0 or CATALOGUE[region.span.start - 1] == "\n"
        assert CATALOGUE[region.span.end - 1] == "\n"
    assert all("IMPRINT" not in text(CATALOGUE, region.span) for region in protected)


def test_figure_call_canvas_keywords() -> None:
    code = "fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=BG)\nplt.figure(dpi=DPI)\n"
    regions = find_regions(code)

    first, second = regions.figure_calls
    assert first.func == "plt.subplots"
    assert first.figsize is not None and first.figsize.value == (8, 4.5) and first.figsize.literal
    assert first.dpi is not None and text(code, first.dpi.value_span) == "400"
    assert second.figsize is None
    assert second.dpi is not None and not second.dpi.literal and second.dpi.value is None


def test_size_calls_read_literal_sizes_and_dpi() -> None:
    code = source("""
        g.figure.set_size_inches(8, 4.5)
        g.fig.set_size_inches((6, 6), forward=True)
        g.figure.set_dpi(400)
        g.figure.set_size_inches(width, 4.5)
    """)
    calls = find_regions(code).size_calls

    assert [(call.method, call.value) for call in calls] == [
        ("set_size_inches", (8, 4.5)),
        ("set_size_inches", (6, 6)),
        ("set_dpi", 400),
        ("set_size_inches", None),
    ]
    assert calls[2].value_span is not None and text(code, calls[2].value_span) == "400"


def test_placeholder_found_anywhere_but_not_in_strings() -> None:
    code = source("""
        df = load_user_data()
        note = "df = load_user_data()"
        if True:
            df = load_user_data()
        df = load_user_data(1)
    """)
    placeholders = find_regions(code).placeholders

    assert [region.span.first_line for region in placeholders] == [1, 4]
    assert text(code, placeholders[1].span) == "    df = load_user_data()\n"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ('"#FFF" if THEME == "light" else "#000"', True),
        ('"#FFF" if "dark" != THEME else "#000"', True),
        ('THEME == "dark"', True),
        ('"#FFF" if THEME in ("light",) else "#000"', False),
        ('"#FFF" if mode == "light" else "#000"', False),
        ('{"light": 1}[THEME]', False),
    ],
)
def test_tests_theme(value: str, expected: bool) -> None:
    assert value_tests_theme(ast.parse(value, mode="eval").body) is expected


@pytest.mark.parametrize(
    ("statement", "expected"),
    [
        ('THEME = os.getenv("ANYPLOT_THEME", "light")', True),
        ('THEME: str = os.getenv("ANYPLOT_THEME", "light")', True),
        ('THEME = os.getenv("ANYPLOT_THEME")', True),
        ('THEME = os.environ.get("ANYPLOT_THEME", "light")', False),
        ('THEME = os.getenv("THEME", "light")', False),
        ('THEME = "light"', False),
        ('MODE = os.getenv("ANYPLOT_THEME", "light")', False),
    ],
)
def test_theme_assignment_form(statement: str, expected: bool) -> None:
    assert is_theme_assignment(ast.parse(statement).body[0]) is expected


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        ('f"plot-{THEME}.png"', True),
        ("f'plot-{THEME}.png'", True),
        ('f"plot-{THEME!s}.png"', False),
        ('f"plot-{THEME:>5}.png"', False),
        ('f"plot-{theme}.png"', False),
        ('"plot.png"', False),
        ('os.path.join(d, f"plot-{THEME}.png")', False),
    ],
)
def test_standard_target(target: str, expected: bool) -> None:
    assert is_standard_target(ast.parse(target, mode="eval").body) is expected


def test_savefig_targets_fname_keyword_literal_and_nesting() -> None:
    code = source("""
        fig.savefig(fname=f"plot-{THEME}.png", dpi=400)
        if True:
            plt.savefig("plot.png")
    """)
    regions = find_regions(code)

    first, second = regions.savefig_calls
    assert first.standard_target and first.statement is not None
    assert second.literal_target == "plot.png" and second.statement is None
    assert regions.savefig is None  # the last savefig is not a module-level statement


def test_imprint_palette_name_and_palettes() -> None:
    code = source("""
        IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]
        COLORS = ("#009E73", "#AE3030")
        LABELS = ["a", "b"]
        ONE = ["#009E73"]
    """)
    regions = find_regions(code)

    assert regions.imprint is not None and regions.imprint.name == "IMPRINT_PALETTE"
    assert [palette.name for palette in regions.palettes] == ["IMPRINT_PALETTE", "COLORS"]


def test_offsets_count_characters_not_utf8_bytes() -> None:
    code = 'label = "a · b → c ≈ d"; THEME = os.getenv("ANYPLOT_THEME", "light")\n'
    call = ast.parse(code).body[1]
    span = SourceIndex(code).node_span(call)

    assert text(code, span) == 'THEME = os.getenv("ANYPLOT_THEME", "light")'


def test_line_index_handles_crlf_and_lone_cr() -> None:
    index = SourceIndex("a = 1\r\nb = 2\rc = 3\n")

    assert index.line_count == 4
    assert [index.line_text(line) for line in (1, 2, 3)] == ["a = 1\r\n", "b = 2\r", "c = 3\n"]
    assert index.line_of(index.line_start(3)) == 3


def test_span_overlap_and_lines() -> None:
    span = Span(3, 4, 10, 20)

    assert span.overlaps(19, 25) and span.overlaps(5, 11) and span.overlaps(12, 12 + 1)
    assert not span.overlaps(20, 30) and not span.overlaps(0, 10)
    assert span.lines() == "lines 3-4" and Span(5, 5, 0, 1).lines() == "line 5"


def test_dotted_name() -> None:
    assert dotted_name(ast.parse("a.b.c", mode="eval").body) == "a.b.c"
    assert dotted_name(ast.parse("a().b", mode="eval").body) is None


def test_syntax_error_propagates() -> None:
    with pytest.raises(SyntaxError):
        find_regions("def broken(:\n")
