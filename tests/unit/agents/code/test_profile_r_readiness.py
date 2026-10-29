"""Tests for agents/anyplot/code/profiles/r/readiness.py and coupling.py: blocked, coupled or clean."""

import ast
from collections import Counter

import pytest

from agents.anyplot.code.profiles.r.coupling import coupling, structure_reasons
from agents.anyplot.code.profiles.r.normalise import normalise
from agents.anyplot.code.profiles.r.readiness import scan

from .conftest import R_CATALOGUE_FILES, R_CATALOGUE_NORMALISED, REPO_ROOT, source


ENABLED = ["ggplot2"]
PLOT_MARKER = "# Plot: reads only df and the constants above\n"
SAVE = (
    'ggsave(filename = sprintf("plot-%s.png", THEME), plot = p, device = ragg::agg_png, '
    'width = 8, height = 4.5, units = "in", dpi = 400)\n'
)


def program(body: str) -> str:
    return f'library(ggplot2)\nTHEME <- Sys.getenv("ANYPLOT_THEME", "light")\n{body}\n{SAVE}'


def test_the_catalogue_file_in_miniature_is_clean() -> None:
    readiness = scan(R_CATALOGUE_NORMALISED, spec_id="scatter-demo", enabled_libraries=ENABLED)

    assert (readiness.status, readiness.reasons, readiness.hints) == ("clean", [], [])


@pytest.mark.parametrize(
    ("spec_id", "enabled", "reason"),
    [
        ("choropleth-basic", ENABLED, "map-spec: choropleth-basic"),
        ("scatter-demo", ["matplotlib"], "library-disabled: ggplot2"),
    ],
)
def test_blocked_by_spec_or_library(spec_id: str, enabled: list[str], reason: str) -> None:
    readiness = scan(R_CATALOGUE_NORMALISED, spec_id=spec_id, enabled_libraries=enabled)

    assert readiness.status == "blocked" and readiness.reasons[0].startswith(reason) and readiness.hints == []


@pytest.mark.parametrize(
    ("code", "reason"),
    [
        ("x <- (\n", "syntax: "),
        (program('x <- system("id")'), "security: banned-name at line 3"),
        (SAVE, "no-theme: "),
        (program('ggsave("other.png", p)'), "savefig-target: ggsave at line 3 is not the final"),
        ('THEME <- Sys.getenv("ANYPLOT_THEME", "light")\n', "savefig-target: no top-level ggsave"),
    ],
)
def test_blocked_for_real_reasons(code: str, reason: str) -> None:
    readiness = scan(code, spec_id="scatter-demo", enabled_libraries=ENABLED)

    assert readiness.status == "blocked"
    assert any(line.startswith(reason) for line in readiness.reasons), readiness.reasons


def test_security_reasons_are_capped() -> None:
    body = "\n".join(f'x{number} <- system("id")' for number in range(8))
    readiness = scan(program(body), spec_id="scatter-demo", enabled_libraries=ENABLED)
    security = [reason for reason in readiness.reasons if reason.startswith("security:")]

    assert len(security) == 6 and security[-1].endswith("more findings")


def test_a_missing_marker_never_blocks() -> None:
    readiness = scan(program("p <- ggplot(df, aes(x, y)) + geom_point()"), spec_id="s", enabled_libraries=ENABLED)

    assert readiness.status == "coupled"
    assert readiness.reasons == ["data-block: no # Data and # Plot markers, so the sample is built among the plot code"]


@pytest.mark.parametrize(
    ("line", "category", "snippet"),
    [
        ("p <- p + xlim(0, 100)", "limits", "xlim(0, 100)"),
        ("p <- p + coord_cartesian(ylim = c(0, 50))", "limits", "ylim = c(0, 50)"),
        ("p <- p + scale_y_continuous(limits = c(0, 125), breaks = seq(0, 125, 25))", "limits", "limits ="),
        ('p <- p + scale_x_discrete(limits = c("Q1", "Q2"))', "limits", "limits ="),
        ('p <- p + scale_x_date(limits = as.Date(c("2024-01-01", "2024-12-31")))', "limits", "limits ="),
        ("p <- p + scale_fill_gradient2(midpoint = 50)", "color-scale", "midpoint = 50"),
        ("p <- p + scale_color_gradient(limits = c(10, 90))", "color-scale", "limits ="),
        ('p <- p + annotate("text", x = 12, y = 40, label = "Peak")', "annotations", "annotate("),
        ("p <- p + geom_hline(yintercept = 35)", "annotations", "geom_hline"),
        ('label <- "r = 0.87"', "statistics", '"r = 0.87"'),
        ("z <- 1.96", "statistics", "1.96"),
        ('IMPRINT_PALETTE <- c("#009E73", "#C475FD")', "palette", "IMPRINT_PALETTE (2 entries)"),
        ("noise <- rnorm(10)", "synthetic-data", "rnorm(10)"),
        ("d <- iris", "synthetic-data", "iris"),
    ],
)
def test_coupling_categories(line: str, category: str, snippet: str) -> None:
    code = R_CATALOGUE_NORMALISED.replace(PLOT_MARKER, f"{PLOT_MARKER}{line}\n")
    found = coupling(code)

    assert found.categories == [category]
    assert any(snippet in text for _, text in found.findings[category])


@pytest.mark.parametrize(
    "line",
    [
        "p <- p + geom_hline(yintercept = 0)",
        "p <- p + scale_y_continuous(limits = c(0, NA))",
        "p <- p + annotate('text', x = Inf, y = -Inf, label = 'note')",
        'label <- sprintf("r = %.2f", r)',
        "p <- p + scale_y_continuous(limits = range(df$y))",
    ],
)
def test_computed_or_baseline_values_are_not_coupling(line: str) -> None:
    code = R_CATALOGUE_NORMALISED.replace(PLOT_MARKER, f"{PLOT_MARKER}{line}\n")

    assert coupling(code).categories == []


def test_synthetic_data_in_a_block_without_constants_is_named_by_the_block() -> None:
    code = (
        R_CATALOGUE_NORMALISED.replace('SPEND   <- "Spend (k USD)"    # role: x\n', "")
        .replace('REVENUE <- "Revenue (k USD)"  # role: y\n', "")
        .replace("!!SPEND := runif(50, 5, 150), !!REVENUE := rnorm(50, 300, 40)", "x = runif(50), y = rnorm(50)")
        .replace("aes(x = .data[[SPEND]], y = .data[[REVENUE]])", "aes(x = x, y = y)")
        .replace("x = SPEND, y = REVENUE", 'x = "x", y = "y"')
    )
    readiness = scan(code, spec_id="scatter-demo", enabled_libraries=ENABLED)

    assert readiness.status == "coupled"
    assert readiness.reasons[0].startswith("data-block: the # Data block at lines")
    assert readiness.hints[1].startswith("Synthetic data generation in the # Data block at lines")


def test_a_seed_above_a_complete_block_does_not_couple() -> None:
    code = R_CATALOGUE_NORMALISED.replace("set.seed(42)\n", "").replace(
        "library(ragg)\n", "library(ragg)\nset.seed(42)\n"
    )

    assert scan(code, spec_id="scatter-demo", enabled_libraries=ENABLED).status == "clean"


def test_a_canvas_off_target_gets_a_canvas_reason() -> None:
    code = R_CATALOGUE_NORMALISED.replace("dpi      = 200", "dpi      = 400")
    readiness = scan(code, spec_id="scatter-demo", enabled_libraries=ENABLED)

    assert readiness.status == "clean"
    assert readiness.reasons == [
        "canvas: the save renders 6400x3600 (over R2's pixel cap), not 3200x1800; R2 refuses a PNG over its pixel cap"
    ]


def test_structure_reasons_of_a_good_file_are_empty() -> None:
    assert structure_reasons(R_CATALOGUE_NORMALISED) == []


def test_catalogue_corpus() -> None:
    """The split over the 325 normalised ggplot2 files (2026-10-29, owner rule: a missing marker never blocks):
    4 clean (area-basic, box-basic, line-basic, line-timeseries: both markers and role-commented column
    constants), 297 coupled, 24 blocked. Blocked: the 13 map specs; qrcode-basic (the qrcode package and a URL);
    7 files that name a flow's origin `source`, a denied name (area-stacked-confidence, chord-basic, circos-basic,
    heatmap-adjacency, network-bipartite, network-weighted, sankey-basic); the dataset packages gapminder
    (dendrogram-basic) and palmerpenguins (scatter-categorical), which the allowlist leaves out; and
    maze-circular's `<<-`. Hints: data-block 297, synthetic-data 271, limits 130, annotations 71, palette 38,
    statistics 18, color-scale 10; no canvas reason, because the normaliser puts every canvas on target."""
    status: Counter[str] = Counter()
    blocked: list[str] = []
    clean: list[str] = []
    categories: Counter[str] = Counter()
    for path in R_CATALOGUE_FILES:
        spec_id = path.parts[-4]
        readiness = scan(normalise(path.read_text(encoding="utf-8")), spec_id=spec_id, enabled_libraries=ENABLED)
        status[readiness.status] += 1
        if readiness.status == "blocked":
            blocked.append(spec_id)
        elif readiness.status == "clean":
            clean.append(spec_id)
        categories.update(reason.split(":")[0] for reason in readiness.reasons if readiness.status != "blocked")

    assert status == Counter({"coupled": 297, "blocked": 24, "clean": 4})
    assert clean == ["area-basic", "box-basic", "line-basic", "line-timeseries"]
    assert sorted(blocked) == sorted(
        [
            *(
                "bubble-map-geographic",
                "cartogram-area-distortion",
                "choropleth-basic",
                "contour-map-geographic",
                "flowmap-origin-destination",
                "heatmap-geographic",
                "map-connection-lines",
                "map-marker-clustered",
                "map-projections",
                "map-route-path",
                "map-tile-background",
                "map-tilegrid",
                "scatter-map-geographic",
            ),
            "qrcode-basic",
            "area-stacked-confidence",
            "chord-basic",
            "circos-basic",
            "heatmap-adjacency",
            "network-bipartite",
            "network-weighted",
            "sankey-basic",
            "dendrogram-basic",
            "scatter-categorical",
            "maze-circular",
        ]
    )
    assert categories == Counter(
        {
            "data-block": 297,
            "synthetic-data": 271,
            "limits": 130,
            "annotations": 71,
            "palette": 38,
            "statistics": 18,
            "color-scale": 10,
        }
    )


def test_the_detection_stays_inside_the_core_boundary() -> None:
    """coupling.py (the clean or coupled decision) imports only stdlib, tree-sitter, core.*, treesitter and the R
    regions, so it can move to core/ for the regen gate's adapt route (2026-10-29)."""
    tree = ast.parse((REPO_ROOT / "agents/anyplot/code/profiles/r/coupling.py").read_text(encoding="utf-8"))
    relative = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.level}
    absolute = {
        node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and not node.level
    } | {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}

    assert relative == {"treesitter", "regions"}
    assert absolute <= {"re", "collections", "dataclasses", "tree_sitter", "core"}


def test_hints_are_short_and_name_lines() -> None:
    code = (
        source("""
        library(ggplot2)
        THEME <- Sys.getenv("ANYPLOT_THEME", "light")
        p <- ggplot(df, aes(x, y)) + xlim(0, 10) + ylim(0, 20)
        p <- p + annotate("text", x = 3, y = 4, label = "a") + geom_vline(xintercept = 5)
    """)
        + SAVE
    )
    readiness = scan(code, spec_id="scatter-demo", enabled_libraries=ENABLED)

    assert all(len(hint) <= 300 for hint in readiness.hints)
    assert "line 3" in readiness.hints[1] and "line 4" in readiness.hints[2]
