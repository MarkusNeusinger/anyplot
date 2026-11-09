"""Tests for agents/anyplot/code/profiles/r/readiness.py and coupling.py: blocked, coupled or clean."""

import ast
import re
from collections import Counter

import pytest

from agents.anyplot.code.profiles.r.coupling import coupling, is_layout_complete, structure_reasons
from agents.anyplot.code.profiles.r.normalise import measure_canvas, normalise
from agents.anyplot.code.profiles.r.readiness import scan
from agents.anyplot.code.profiles.r.regions import find_regions
from agents.anyplot.code.profiles.r.validate import validate_security
from agents.anyplot.schemas import MAX_NOTE_CHARS as MAX_REASON_CHARS
from core.spec_roles import MAP_SPECS

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
        "iris <- df[df$y > 0, ]\nn <- nrow(iris)",  # a local variable named like a dataset, as the validator reads it
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


BLOCKING = frozenset({"map-spec", "library-disabled", "syntax", "security", "no-theme", "savefig-target"})
"""The reason categories of `blocked` (`readiness.scan`); a clean or coupled file carries none of them."""
DATA_LINE = re.compile(r"^# (?:--- )?Data\b", re.MULTILINE)
PLOT_LINE = re.compile(r"^# (?:--- )?Plot\b", re.MULTILINE)
COLUMN_LINE = re.compile(r'^[A-Z][A-Z0-9_]*\s*<-\s*"[^"\n]*"\s*# role: \w+\s*$', re.MULTILINE)
ANY_DATA_MARKER = re.compile(r"^#.*\bData\b", re.MULTILINE)


def layout_in_text(text: str) -> bool | None:
    """The adaptable-code layout read from the text alone: True for a `# Data` line, a later `# Plot` line and a
    canonical column constant, False with no `# ... Data ...` comment at column 0, else None."""
    data, plot = DATA_LINE.search(text), PLOT_LINE.search(text)
    if data and plot and data.start() < plot.start() and COLUMN_LINE.search(text):
        return True
    return False if not ANY_DATA_MARKER.search(text) else None


def test_catalogue_corpus() -> None:
    """Every normalised ggplot2 file is classified, and each class keeps its meaning while the catalogue changes
    (owner rule of 2026-10-29: a missing marker never blocks). The counts of a day (325 files on 2026-10-29: 4
    clean, 306 coupled, 15 blocked; hints data-block 306, synthetic-data 279, limits 134, ...) move with every
    regeneration, so the test holds rules: a file is blocked exactly when its spec is a map spec, the SECURITY
    profile flags it or its structure fails; a clean file has no reason; a coupled file has no blocking reason and
    one hint per reason but the `canvas:` one, which appears exactly where the normaliser could not put the canvas
    on target, and the `data-block` hint exactly when its layout is incomplete, which a plain reading of the text
    confirms where it can; all three classes occur."""
    statuses: Counter[str] = Counter()
    for path in R_CATALOGUE_FILES:
        spec = path.parts[-4]
        normalised = normalise(path.read_text(encoding="utf-8"))
        readiness = scan(normalised, spec_id=spec, enabled_libraries=ENABLED)
        categories = [reason.split(":", 1)[0] for reason in readiness.reasons]
        statuses[readiness.status] += 1
        must_block = spec in MAP_SPECS or bool(validate_security(normalised)) or bool(structure_reasons(normalised))
        assert (readiness.status == "blocked") == must_block, (spec, readiness.reasons)
        assert all(len(hint) <= MAX_REASON_CHARS for hint in readiness.hints), spec
        if readiness.status == "blocked":
            continue
        assert not set(categories) & BLOCKING, (spec, readiness.reasons)
        assert len(readiness.hints) == len([category for category in categories if category != "canvas"]), spec
        assert ("canvas" in categories) == (measure_canvas(normalised).note is not None), spec
        assert (readiness.status == "clean") == (not readiness.reasons), spec
        complete = is_layout_complete(find_regions(normalised))
        assert ("data-block" in categories) == (not complete), spec
        assert layout_in_text(normalised) in (None, complete), spec  # the same answer from the text alone

    assert sum(statuses.values()) == len(R_CATALOGUE_FILES) and set(statuses) == {"clean", "coupled", "blocked"}


@pytest.mark.parametrize("spec_id", ["dendrogram-basic", "scatter-categorical"])
def test_a_dataset_package_is_a_synthetic_data_hint(spec_id: str) -> None:
    path = next(path for path in R_CATALOGUE_FILES if path.parts[-4] == spec_id)
    readiness = scan(normalise(path.read_text(encoding="utf-8")), spec_id=spec_id, enabled_libraries=ENABLED)

    assert readiness.status == "coupled"
    assert any("library(" in hint for hint in readiness.hints if hint.startswith("Synthetic data"))


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
