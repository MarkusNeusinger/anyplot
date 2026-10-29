"""Tests for agents/anyplot/code/profiles/julia/regions.py: the catalogue conventions in Makie code."""

import ast

import pytest

from agents.anyplot.code.profiles.julia.normalise import normalise
from agents.anyplot.code.profiles.julia.regions import PLACEHOLDER, STANDARD_TARGET, THEME_STATEMENT, find_regions

from .conftest import JULIA_CATALOGUE_FILES, JULIA_CATALOGUE_NORMALISED, JULIA_WORKING, REPO_ROOT, source


SAVE = 'save("plot-$(THEME).png", fig; px_per_unit = 2)\n'


def test_theme_block_tokens_palette_and_save() -> None:
    regions = find_regions(JULIA_CATALOGUE_NORMALISED)

    assert regions.theme is not None and regions.theme.span.first_line == 6
    assert [token.name for token in regions.theme_tokens] == ["PAGE_BG", "INK", "ALPHA"]
    assert regions.imprint is not None and regions.imprint.name == "IMPRINT_PALETTE"
    assert regions.imprint.entries[:2] == ("#009E73", "#C475FD") and len(regions.imprint.entries) == 8
    assert regions.save is not None and regions.save.standard_target
    assert (regions.save.figure, regions.save.keywords, regions.save.px_per_unit_number) == ("fig", ("px_per_unit",), 2)


def test_protected_regions_are_whole_lines_and_exclude_the_palette() -> None:
    regions = find_regions(JULIA_WORKING)
    kinds = [region.kind for region in regions.protected]

    assert kinds == ["theme", "theme_token", "theme_token", "theme_token", "placeholder", "savefig"]
    for region in regions.protected:
        assert JULIA_WORKING[region.span.start : region.span.end].endswith("\n")


def test_markers_and_column_constants() -> None:
    regions = find_regions(JULIA_CATALOGUE_NORMALISED)

    assert regions.data_marker is not None and regions.plot_marker is not None
    assert [(column.name, column.role, column.values) for column in regions.columns] == [
        ("SPEND", "x", ("Spend (k USD)",)),
        ("REVENUE", "y", ("Revenue (k USD)",)),
    ]


def test_column_constants_decode_julia_escapes_and_take_vectors() -> None:
    code = 'const PRICE = "Preis \\$ (€)"  # role: y\nSERIES = ["a", "b"]  # role: y\nNOTE = "x"\n'

    assert [(column.name, column.values) for column in find_regions(code).columns] == [
        ("PRICE", ("Preis $ (€)",)),
        ("SERIES", ("a", "b")),
    ]


@pytest.mark.parametrize(
    ("comment", "kind"),
    [("# Data", "data"), ("# --- Data ---", "data"), ("# Data — simulated", "data"), ("# ==== Plot", "plot")],
)
def test_markers_match_the_catalogues_decorated_forms(comment: str, kind: str) -> None:
    markers = find_regions(f"x = 1\n{comment}\ny = 2\n").markers

    assert [marker.kind for marker in markers] == [kind]


@pytest.mark.parametrize("comment", ["#= Data =#", "# Database setup", "# Plotting helpers", "  # Data"])
def test_comments_that_are_no_markers(comment: str) -> None:
    assert find_regions(f"x = 1\n{comment}\ny = 2\n").markers == ()


@pytest.mark.parametrize(
    ("statement", "token"),
    [
        ('const PAGE_BG = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"', True),
        ('INK = THEME == "dark" ? "#F0EFE8" : "#1A1A17"', True),
        ('const ALPHA = THEME == "light" ? 0.4 : -0.6', True),
        ('const ALIGN = THEME == "light" ? (:left, :top) : (:right, :top)', True),
        ('const FILL = THEME == "light" ? RGBAf(0, 0, 0, 0.1) : RGBAf(1, 1, 1, 0.1)', False),
        ('const ODD = THEME == "light" ? other : "#000000"', False),
        ('const PLAIN = "#FAF8F1"', False),
        ('global G = THEME == "light" ? 1 : 2', True),
    ],
)
def test_theme_tokens(statement: str, token: bool) -> None:
    code = f'const THEME = get(ENV, "ANYPLOT_THEME", "light")\n{statement}\n'

    assert bool(find_regions(code).theme_tokens) is token


def test_a_token_may_read_earlier_tokens_only() -> None:
    code = source("""
        THEME = get(ENV, "ANYPLOT_THEME", "light")
        const BEFORE = THEME == "light" ? LATER : "#000000"
        const INK = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
        const LABEL = THEME == "light" ? INK : colorant"#FFFFFF"
        const LATER = THEME == "light" ? "#1" : "#2"
    """)

    assert [token.name for token in find_regions(code).theme_tokens] == ["INK", "LABEL", "LATER"]


@pytest.mark.parametrize(
    ("statement", "theme"),
    [
        ('const THEME = get(ENV, "ANYPLOT_THEME", "light")', True),
        ('THEME    = get(ENV, "ANYPLOT_THEME", "light")', True),
        ('THEME = get(ENV, "ANYPLOT_THEME", "dark")', False),
        ('THEME = get(ENV, "OTHER", "light")', False),
        ('THEME = get(ENV, "ANYPLOT_THEME")', False),
        ('THEME = Base.get(ENV, "ANYPLOT_THEME", "light")', False),
        ('THEME = get(ENV, "ANYPLOT_THEME", "light"; k = 1)', False),
        ('THEME::String = get(ENV, "ANYPLOT_THEME", "light")', False),
    ],
)
def test_the_theme_statement_is_exact(statement: str, theme: bool) -> None:
    assert (find_regions(statement + "\n").theme is not None) is theme
    assert THEME_STATEMENT == 'const THEME = get(ENV, "ANYPLOT_THEME", "light")'


@pytest.mark.parametrize(
    ("code", "placeholder"),
    [
        ("df = load_user_data()", True),
        ("df=load_user_data()  # the user's table", True),
        ("const df = load_user_data()", False),
        ("df = load_user_data(1)", False),
        ("data = load_user_data()", False),
        ("df = load_user_data() do x\n    x\nend", False),
    ],
)
def test_placeholder(code: str, placeholder: bool) -> None:
    assert bool(find_regions(code + "\n").placeholders) is placeholder


def test_a_placeholder_counts_only_at_the_top_level() -> None:
    """The loader that replaces it imports packages, which Julia allows only at the top level."""
    code = "function f()\n    df = load_user_data()\nend\ndf = load_user_data()\n"

    assert [region.span.first_line for region in find_regions(code).placeholders] == [4]
    assert PLACEHOLDER == "df = load_user_data()"


@pytest.mark.parametrize(
    ("save", "standard"),
    [
        (SAVE, True),
        ('save("plot-$THEME.png", fig)\n', False),
        ('save("plot.png", fig; px_per_unit = 2)\n', False),
        ('save(joinpath(@__DIR__, "plot-$(THEME).png"), fig; px_per_unit = 2)\n', False),
    ],
)
def test_the_standard_target(save: str, standard: bool) -> None:
    regions = find_regions(save)

    assert regions.save is not None and regions.save.standard_target is standard
    assert STANDARD_TARGET == '"plot-$(THEME).png"'


def test_the_protected_save_is_the_last_top_level_standard_save() -> None:
    code = (
        'save("other.png", fig)\nsave("plot-$(THEME).png", fig; px_per_unit = 2)\nwith_theme(T) do\n    '
        + SAVE
        + "end\n"
    )
    regions = find_regions(code)

    assert len(regions.saves) == 3
    assert regions.save is not None and regions.save.span.first_line == 2


def test_a_save_inside_a_block_is_no_protected_save() -> None:
    """Three catalogue files save inside `with_theme(...) do`: their save is not a statement of its own."""
    code = "with_theme(T) do\n    fig = Figure()\n    " + SAVE + "end\n"

    assert find_regions(code).save is None


def test_catalogue_corpus() -> None:
    """Every catalogue file has the theme statement; all but three save at the top level (with_theme)."""
    counts = {"theme": 0, "save": 0, "imprint": 0, "both markers": 0, "columns": 0, "tokens": 0}
    for path in JULIA_CATALOGUE_FILES:
        regions = find_regions(normalise(path.read_text(encoding="utf-8")))
        counts["theme"] += regions.theme is not None
        counts["save"] += regions.save is not None and regions.save.standard_target
        counts["imprint"] += regions.imprint is not None
        counts["both markers"] += regions.data_marker is not None and regions.plot_marker is not None
        counts["columns"] += bool(regions.columns)
        counts["tokens"] += len(regions.theme_tokens)

    assert counts == {"theme": 325, "save": 322, "imprint": 196, "both markers": 218, "columns": 0, "tokens": 1213}


def test_module_imports_stay_inside_the_core_boundary() -> None:
    """regions.py imports only stdlib, tree-sitter, core.* and treesitter, so it can move to core/ (2026-10-29)."""
    tree = ast.parse((REPO_ROOT / "agents/anyplot/code/profiles/julia/regions.py").read_text(encoding="utf-8"))
    relative = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.level}
    absolute = {
        node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and not node.level
    } | {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}

    assert relative == {"treesitter"}
    assert absolute <= {"re", "dataclasses", "typing", "tree_sitter", "core"}
