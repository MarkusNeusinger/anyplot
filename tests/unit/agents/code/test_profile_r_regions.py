"""Tests for agents/anyplot/code/profiles/r/regions.py: the ggplot2 conventions as spans."""

import ast
import re
from collections import Counter

import pytest

from agents.anyplot.code.profiles.r.regions import (
    PLACEHOLDER,
    SAVE_KEYWORDS,
    Regions,
    find_regions,
    is_placeholder,
    is_standard_target,
    is_theme_statement,
)
from agents.anyplot.code.treesitter import Source, Span, statements

from .conftest import R_CATALOGUE, R_CATALOGUE_FILES, REPO_ROOT, source


def text(code: str, span: Span) -> str:
    return code[span.start : span.end]


def test_theme_block_tokens_palette_and_save() -> None:
    regions = find_regions(R_CATALOGUE)

    assert regions.theme is not None
    assert text(R_CATALOGUE, regions.theme.span) == 'THEME    <- Sys.getenv("ANYPLOT_THEME", "light")\n'
    assert [token.name for token in regions.theme_tokens] == ["PAGE_BG", "INK", "ALPHA"]
    assert regions.imprint is not None and regions.imprint.name == "IMPRINT_PALETTE"
    assert len(regions.imprint.entries) == 8
    assert text(R_CATALOGUE, regions.imprint.span).count("\n") == 2
    save = regions.save
    assert save is not None and save.statement is not None
    assert save.standard_target and save.device == "ragg::agg_png"
    assert save.keywords == ("filename", "plot", "device", "width", "height", "units", "dpi")
    dpi = save.argument("dpi")
    assert dpi is not None and dpi.number == 300 and dpi.value_span is not None
    assert text(R_CATALOGUE, dpi.value_span) == "300"
    assert text(R_CATALOGUE, save.statement).startswith("ggsave(\n") and text(R_CATALOGUE, save.statement).endswith(
        ")\n"
    )


def test_protected_regions_are_whole_lines_and_exclude_the_palette() -> None:
    regions = find_regions(R_CATALOGUE)
    protected = regions.protected

    assert [region.kind for region in protected] == ["theme", "theme_token", "theme_token", "theme_token", "savefig"]
    for region in protected:
        assert region.span.start == 0 or R_CATALOGUE[region.span.start - 1] == "\n"
        assert R_CATALOGUE[region.span.end - 1] == "\n"
    assert all("IMPRINT" not in text(R_CATALOGUE, region.span) for region in protected)


def test_markers_and_column_constants() -> None:
    regions = find_regions(R_CATALOGUE)

    assert regions.data_marker is not None and regions.data_marker.text.startswith("# Data: replace")
    assert regions.plot_marker is not None
    assert [(column.name, column.role, column.values) for column in regions.columns] == [
        ("SPEND", "x", ("Spend (k USD)",)),
        ("REVENUE", "y", ("Revenue (k USD)",)),
    ]


@pytest.mark.parametrize(
    ("comment", "kind"),
    [
        ("# Data", "data"),
        ("# --- Data: sales by region", "data"),
        ("# Data — monthly sales", "data"),
        ("## ==== Plot ====", "plot"),
        ("# Plot: reads only df", "plot"),
    ],
)
def test_markers_match_the_catalogues_decorated_forms(comment: str, kind: str) -> None:
    regions = find_regions(f"{comment}\nx <- 1\n")

    assert [marker.kind for marker in regions.markers] == [kind]


@pytest.mark.parametrize("comment", ["#' Data", "# Database setup", "# Plotting helpers", "  # Data"])
def test_comments_that_are_no_markers(comment: str) -> None:
    code = f"f <- function() {{\n{comment}\n  1\n}}\n" if comment.startswith(" ") else f"{comment}\nx <- 1\n"

    assert find_regions(code).markers == ()


@pytest.mark.parametrize(
    ("statement", "token"),
    [
        ('A <- if (THEME == "light") "#FFFFFF" else "#000000"', True),
        ('A <- if (THEME != "dark") 0.4 else -0.5', True),
        ('A <- if ("light" == THEME) TRUE else NA', True),
        ('A = if (THEME == "light") "#FFF" else if (THEME == "dark") "#000" else NULL', True),
        ('A <- THEME == "light"', True),
        ('A <- if (THEME == "light") scales::alpha("#000", 0.1) else "#FFF"', False),
        ('A <- if (THEME == "light") other else "#FFF"', False),
        ('A <- if (THEME == "light") "#FFF"', False),
        ('A <- if (x == "light") "#FFF" else "#000"', False),
        ('A <<- if (THEME == "light") "#FFF" else "#000"', False),
    ],
)
def test_theme_tokens(statement: str, token: bool) -> None:
    code = f'THEME <- Sys.getenv("ANYPLOT_THEME", "light")\n{statement}\n'

    assert [region.name for region in find_regions(code).theme_tokens] == (["A"] if token else [])


def test_a_token_may_read_earlier_tokens_only() -> None:
    code = source("""
        THEME <- Sys.getenv("ANYPLOT_THEME", "light")
        LATE <- if (THEME == "light") INK else "#FFF"
        INK <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
        EDGE <- if (THEME == "light") INK else "#FFF"
    """)

    assert [region.name for region in find_regions(code).theme_tokens] == ["INK", "EDGE"]


@pytest.mark.parametrize(
    ("statement", "theme"),
    [
        ('THEME <- Sys.getenv("ANYPLOT_THEME", "light")', True),
        ('THEME = Sys.getenv("ANYPLOT_THEME", "light")', True),
        ('THEME <- Sys.getenv("ANYPLOT_THEME", "dark")', False),
        ('THEME <- Sys.getenv("ANYPLOT_THEME")', False),
        ('THEME <- Sys.getenv("HOME", "light")', False),
        ('THEME <- Sys.getenv(x = "ANYPLOT_THEME", unset = "light")', False),
        ('THEME <<- Sys.getenv("ANYPLOT_THEME", "light")', False),
        ('Sys.getenv("ANYPLOT_THEME", "light") -> THEME', False),
    ],
)
def test_the_theme_statement_is_exact(statement: str, theme: bool) -> None:
    src = Source(statement + "\n", "r")

    assert is_theme_statement(src, statements(src.root)[0]) is theme


@pytest.mark.parametrize(
    ("code", "placeholder"),
    [
        ("df <- load_user_data()", True),
        ("df = load_user_data()", True),
        ("df <- load_user_data(1)", False),
        ("data <- load_user_data()", False),
        ("df <- other()", False),
    ],
)
def test_placeholder(code: str, placeholder: bool) -> None:
    src = Source(code + "\n", "r")

    assert is_placeholder(src, statements(src.root)[0]) is placeholder


def test_placeholder_regions_are_found_anywhere() -> None:
    code = f"{PLACEHOLDER}\nf <- function() {{\n  {PLACEHOLDER}\n}}\n"

    assert [region.span.first_line for region in find_regions(code).placeholders] == [1, 3]


@pytest.mark.parametrize(
    ("target", "standard"),
    [
        ('sprintf("plot-%s.png", THEME)', True),
        ("sprintf('plot-%s.png', (THEME))", True),
        ('sprintf("plot-%s.png", THEME, 1)', False),
        ('sprintf(fmt = "plot-%s.png", THEME)', False),
        ('sprintf("plot-%s.svg", THEME)', False),
        ('paste0("plot-", THEME, ".png")', False),
        ('"plot.png"', False),
    ],
)
def test_standard_target(target: str, standard: bool) -> None:
    src = Source(target + "\n", "r")

    assert is_standard_target(src, statements(src.root)[0]) is standard


def test_the_protected_save_is_the_last_top_level_save_of_the_standard_target() -> None:
    code = source("""
        THEME <- Sys.getenv("ANYPLOT_THEME", "light")
        ggsave(filename = sprintf("plot-%s.png", THEME), plot = p)
        f <- function() ggsave(filename = sprintf("plot-%s.png", THEME), plot = q)
        ggsave(filename = "other.png", plot = p)
    """)
    regions = find_regions(code)

    assert len(regions.saves) == 3
    assert regions.save is not None and regions.save.statement is not None
    assert regions.save.statement.first_line == 2
    assert [call.literal_target for call in regions.saves] == [None, None, "other.png"]


def test_a_save_inside_a_function_is_not_protected() -> None:
    code = 'f <- function() ggsave(filename = sprintf("plot-%s.png", THEME))\n'
    regions = find_regions(code)

    assert len(regions.saves) == 1 and regions.save is None
    assert regions.protected == ()


def test_positions_are_characters_past_non_ascii_text() -> None:
    code = 'TITLE <- "Ankara · Türkei — 3 °C"\nTHEME <- Sys.getenv("ANYPLOT_THEME", "light")\n'
    regions = find_regions(code)

    assert regions.theme is not None
    assert text(code, regions.theme.span) == 'THEME <- Sys.getenv("ANYPLOT_THEME", "light")\n'


def test_code_with_syntax_problems_is_read_as_far_as_it_parses() -> None:
    regions = find_regions('THEME <- Sys.getenv("ANYPLOT_THEME", "light")\nx <- (\n')

    assert isinstance(regions, Regions)


LITERAL_TOKEN = re.compile(r'^([A-Z][A-Z0-9_]*)\s*<-\s*if \(THEME == "(?:light|dark)"\) "[^"\n]*" else "[^"\n]*"\s*$')
"""A theme token of the plainest shape, `PAGE_BG <- if (THEME == "light") "#FAF8F1" else "#1A1A17"`."""
DATA_LINE = re.compile(r"^# Data\b")
PLOT_LINE = re.compile(r"^# Plot\b")
COLUMN_LINE = re.compile(r'^([A-Z][A-Z0-9_]*)\s*<-\s*"[^"\n]*"\s*# role: \w+\s*$')
STANDARD_TARGET_TEXT = re.compile(r'sprintf\(\s*"plot-%s\.png"\s*,\s*THEME\s*\)')


def test_catalogue_corpus() -> None:
    """The conventions of every ggplot2 file (module docstring), each found where the file's text has it and only
    there: the theme statement, one protected save with `ragg::agg_png` and only the save keywords, the theme
    tokens, the markers, the column constants and the standard target. The counts of a day (325 files on
    2026-10-29: 1,322 tokens, markers in 247 files, column constants in 4, the standard target in 324 before the
    normaliser inlines logistic-regression's) move with every regeneration, so each detection is held to a plain
    reading of the text instead."""
    found: Counter[str] = Counter()
    for path in R_CATALOGUE_FILES:
        code = path.read_text(encoding="utf-8")
        lines = code.splitlines()
        name = path.parts[-4]
        regions = find_regions(code)
        assert regions.theme is not None, name
        assert regions.save is not None and regions.save.statement is not None, name
        assert len(regions.saves) == 1, name
        assert regions.save.device == "ragg::agg_png", name
        assert set(regions.save.keywords) <= set(SAVE_KEYWORDS), name
        save = text(code, regions.save.statement)
        assert regions.save.standard_target == bool(STANDARD_TARGET_TEXT.search(save)), name
        tokens = {token.name for token in regions.theme_tokens}
        assert {m.group(1) for line in lines if (m := LITERAL_TOKEN.match(line))} <= tokens, name
        for token in regions.theme_tokens:
            statement = text(code, token.span)
            assert statement.lstrip().startswith(token.name) and "THEME" in statement, (name, token.name)
        for marker, word, canonical in (
            (regions.data_marker, "Data", DATA_LINE),
            (regions.plot_marker, "Plot", PLOT_LINE),
        ):
            assert marker is not None or not any(canonical.match(line) for line in lines), (name, word)
            assert marker is None or re.match(rf"#.*\b{word}\b", lines[marker.line - 1]), (name, word)
            found[word] += marker is not None
        assert {m.group(1) for line in lines if (m := COLUMN_LINE.match(line))} <= {c.name for c in regions.columns}
        for constant in regions.columns:
            statement = text(code, constant.span)
            assert f"# role: {constant.role}" in statement and constant.name in statement, (name, constant.name)
        found["tokens"] += bool(tokens)
        found["columns"] += bool(regions.columns)
        found["standard"] += regions.save.standard_target

    assert all(found[kind] for kind in ("tokens", "Data", "Plot", "columns", "standard")), found


def test_module_imports_stay_inside_the_core_boundary() -> None:
    """The R detection is meant to move to core/ (2026-10-29): stdlib, tree-sitter, core.* and treesitter only."""
    tree = ast.parse((REPO_ROOT / "agents/anyplot/code/profiles/r/regions.py").read_text(encoding="utf-8"))
    relative = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.level}
    absolute = {
        node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and not node.level
    } | {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}

    assert relative == {"treesitter"}
    assert absolute <= {"re", "dataclasses", "typing", "tree_sitter", "core"}
