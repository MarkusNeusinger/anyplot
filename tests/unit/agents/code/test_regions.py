"""Tests for agents/anyplot/code/regions.py: spans of the catalogue conventions."""

import ast

import pytest

from agents.anyplot.code.regions import (
    HTML_SUFFIX,
    SAVE_NAMES,
    SAVE_RULES,
    SourceIndex,
    Span,
    dotted_name,
    find_regions,
    is_standard_target,
    is_theme_assignment,
    is_theme_target,
    save_rule,
)
from agents.anyplot.code.regions import tests_theme as value_tests_theme  # not named test* for pytest

from .conftest import CATALOGUE, CATALOGUE_FILES, source


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


def test_a_theme_token_picks_fixed_values_and_a_data_dependent_conditional_is_not_one() -> None:
    """The catalogue's shapes: literals, lists, earlier tokens; box-basic's `_tight_text_color` reads the data."""
    code = source("""
        THEME = os.getenv("ANYPLOT_THEME", "light")
        INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
        BANDS = [0.30, 0.22] if THEME == "light" else [0.45, 0.32]
        EDGE = INK if THEME == "light" else "#999999"
        IS_DARK = THEME == "dark"
        LATER = LATE if THEME == "light" else "#000"
        LATE = "#FFF" if THEME == "light" else "#000"
        _tight = INK if THEME == "dark" else IMPRINT[best]
        ALPHA = 0.3 if THEME == "light" else min(0.5, 0.4)
    """)

    assert [token.name for token in find_regions(code).theme_tokens] == ["INK", "BANDS", "EDGE", "IS_DARK", "LATE"]


@pytest.mark.skipif(not CATALOGUE_FILES, reason="plots/ is not checked out")
def test_every_catalogue_theme_conditional_but_five_is_a_token() -> None:
    """Measured on 2026-10-10: 2,745 theme-testing assignments in the 650 matplotlib and seaborn files, one of them
    data-dependent; on 2026-10-25, 5,438 in the 1,296 files of the four libraries, five of them (a colour taken from
    a palette index or another plot colour, a tuple of channel arithmetic, a list of layers)."""
    narrowed = []
    for path in CATALOGUE_FILES:
        code = path.read_text(encoding="utf-8")
        tree = ast.parse(code)
        tokens = {token.name for token in find_regions(code, tree, library=path.stem).theme_tokens}
        for stmt in tree.body:
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                name = stmt.targets[0].id
                if name != "THEME" and value_tests_theme(stmt.value) and name not in tokens:
                    narrowed.append(f"{path.parts[-4]}/{path.name}:{name}")

    assert narrowed == [
        "box-basic/matplotlib.py:_tight_text_color",
        "energy-level-atomic/plotnine.py:BALMER_LABEL_COLOR",
        "heatmap-cohort-retention/plotnine.py:RULE",
        "slope-basic/altair.py:layers",
        "span-basic/altair.py:WARNING_LABEL_COLOR",
    ]


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
    assert regions.savefig is first  # the last module-level save of the PNG; the nested one writes elsewhere

    nested = find_regions(
        source("""
        if True:
            plt.savefig(f"plot-{THEME}.png")
        plt.savefig("draft.png")
    """)
    )
    assert [call.standard_target for call in nested.savefig_calls] == [True, False]
    assert nested.savefig is None  # no module-level save of the PNG


PLOTNINE = source("""
    import os

    import pandas as pd
    from plotnine import aes, geom_point, ggplot, ggsave

    THEME = os.getenv("ANYPLOT_THEME", "light")
    PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
    df = load_user_data()
    plot = ggplot(df, aes(x="x", y="y")) + geom_point()
    ggsave(plot, filename=f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
""")
ALTAIR = source("""
    import os

    import altair as alt
    from PIL import Image

    THEME = os.getenv("ANYPLOT_THEME", "light")
    PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
    df = load_user_data()
    chart = alt.Chart(df).mark_point().encode(x="x:Q", y="y:Q").properties(width=740, height=400, background=PAGE_BG)
    chart.save(f"plot-{THEME}.png", scale_factor=4.0)
    _img = Image.open(f"plot-{THEME}.png").convert("RGB")
    if _img.size != (3200, 1800):
        _canvas = Image.new("RGB", (3200, 1800), PAGE_BG)
        _canvas.paste(_img, (0, 0))
        _canvas.save(f"plot-{THEME}.png")
    chart.save(f"plot-{THEME}.html")
""")


class TestSaveRules:
    """One save rule per library (`SAVE_RULES`): which calls save, where the file is, what is protected."""

    def test_every_rule_names_its_save_calls(self) -> None:
        assert set(SAVE_RULES) == {"matplotlib", "seaborn", "plotnine", "altair"}
        assert SAVE_NAMES == {"savefig", "save", "ggsave"}
        assert save_rule("matplotlib").verb == "savefig" and save_rule("plotnine").verb == "save"
        assert save_rule("altair").html and save_rule("altair").reopens and not save_rule("altair").canvas
        assert save_rule("seaborn").canvas and not save_rule("plotnine").canvas
        with pytest.raises(ValueError, match="no save rule"):
            save_rule("plotly")

    def test_plotnine_ggsave_takes_the_file_second(self) -> None:
        regions = find_regions(PLOTNINE, library="plotnine")

        (call,) = regions.savefig_calls
        assert call.name == "ggsave" and call.standard_target and call.statement is not None
        assert regions.savefig is call and call.dpi is not None and call.dpi.value == 400
        positional = PLOTNINE.replace('filename=f"plot-{THEME}.png"', 'f"plot-{THEME}.png"')
        assert find_regions(positional, library="plotnine").savefig_calls[0].standard_target
        wrong_slot = PLOTNINE.replace('ggsave(plot, filename=f"plot-{THEME}.png"', 'ggsave(f"plot-{THEME}.png", plot')
        assert not find_regions(wrong_slot, library="plotnine").savefig_calls[0].standard_target
        # Read with matplotlib's rule the same code has no save call at all.
        assert find_regions(PLOTNINE).savefig_calls == ()

    def test_altair_protects_the_module_level_png_save(self) -> None:
        regions = find_regions(ALTAIR, library="altair")

        shapes = [(c.name, c.standard_target, c.html_target, c.statement is not None) for c in regions.savefig_calls]
        assert shapes == [("save", True, False, True), ("save", True, False, False), ("save", False, True, True)]
        assert regions.savefig is regions.savefig_calls[0]
        assert [region.kind for region in regions.protected] == ["theme", "theme_token", "placeholder", "savefig"]
        assert text(ALTAIR, regions.protected[-1].span) == 'chart.save(f"plot-{THEME}.png", scale_factor=4.0)\n'

    def test_the_html_target_predicate(self) -> None:
        html = ast.parse('f"plot-{THEME}.html"', mode="eval").body
        assert is_theme_target(html, HTML_SUFFIX) and not is_theme_target(html) and not is_standard_target(html)
        assert is_theme_target(ast.parse('f"plot-{THEME}.png"', mode="eval").body)


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
