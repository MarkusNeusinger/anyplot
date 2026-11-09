"""Tests for agents/anyplot/code/profiles/julia/readiness.py and coupling.py: blocked, coupled or clean."""

import ast
import re
from collections import Counter

import pytest

from agents.anyplot.code.profiles.julia.coupling import coupling, is_layout_complete, structure_reasons
from agents.anyplot.code.profiles.julia.normalise import measure_canvas, normalise
from agents.anyplot.code.profiles.julia.readiness import scan
from agents.anyplot.code.profiles.julia.regions import find_regions
from agents.anyplot.code.profiles.julia.validate import validate_security
from agents.anyplot.schemas import MAX_NOTE_CHARS as MAX_REASON_CHARS
from core.spec_roles import MAP_SPECS

from .conftest import JULIA_CATALOGUE_FILES, JULIA_CATALOGUE_NORMALISED, REPO_ROOT, source


HEAD = 'using CairoMakie\nconst THEME = get(ENV, "ANYPLOT_THEME", "light")\nfig = Figure(size = (1600, 900))\n'
SAVE = 'save("plot-$(THEME).png", fig; px_per_unit = 2)\n'
ENABLED = ["makie"]


def test_the_catalogue_file_in_miniature_is_clean() -> None:
    readiness = scan(JULIA_CATALOGUE_NORMALISED, spec_id="scatter-demo", enabled_libraries=ENABLED)

    assert (readiness.status, readiness.reasons, readiness.hints) == ("clean", [], [])


@pytest.mark.parametrize(
    ("spec_id", "enabled", "reason"),
    [
        ("choropleth-basic", ENABLED, "map-spec: choropleth-basic"),
        ("scatter-demo", ["ggplot2"], "library-disabled: makie"),
    ],
)
def test_blocked_by_spec_or_library(spec_id: str, enabled: list[str], reason: str) -> None:
    readiness = scan(JULIA_CATALOGUE_NORMALISED, spec_id=spec_id, enabled_libraries=enabled)

    assert readiness.status == "blocked"
    assert readiness.reasons[0].startswith(reason)


@pytest.mark.parametrize(
    ("code", "reason"),
    [
        ("x = (1 +\n", "syntax: "),
        ("using CairoMakie\nfig = Figure()\n" + SAVE, "no-theme: "),
        (HEAD + "with_theme(T) do\n    " + SAVE + "end\n", "savefig-target: "),
        (HEAD + 'save("plot.png", fig; px_per_unit = 2)\n', "savefig-target: "),
        (HEAD + "using QRCoders\n" + SAVE, "security: banned-import"),
    ],
)
def test_blocked_for_real_reasons(code: str, reason: str) -> None:
    readiness = scan(code, spec_id="scatter-demo", enabled_libraries=ENABLED)

    assert readiness.status == "blocked"
    assert any(text.startswith(reason) for text in readiness.reasons), readiness.reasons


def test_security_reasons_are_capped() -> None:
    body = "".join(f"run(`ls {index}`)\n" for index in range(10))
    readiness = scan(HEAD + body + SAVE, spec_id="scatter-demo", enabled_libraries=ENABLED)

    assert readiness.status == "blocked"
    assert readiness.reasons[5].startswith("security: ") and readiness.reasons[5].endswith("more findings")


def test_a_missing_marker_never_blocks() -> None:
    readiness = scan(
        HEAD + "scatter!(Axis(fig[1, 1]), [1, 2], [3, 4])\n" + SAVE, spec_id="s", enabled_libraries=ENABLED
    )

    assert readiness.status == "coupled"
    assert readiness.reasons == ["data-block: no # Data and # Plot markers, so the sample is built among the plot code"]


@pytest.mark.parametrize(
    ("line", "category", "snippet"),
    [
        ("x = randn(50)", "synthetic-data", "randn(50)"),
        ("Random.seed!(1)", "synthetic-data", "Random.seed!(1)"),
        ("using RDatasets", "synthetic-data", "using RDatasets"),
        ('d = RDatasets.dataset("datasets", "iris")', "synthetic-data", "RDatasets.dataset"),
        ("v = [" + ", ".join(str(index) for index in range(25)) + "]", "synthetic-data", "[0, 1, 2"),
        ("xlims!(ax, 0, 23.5)", "limits", "xlims!(ax, 0, 23.5)"),
        ("ax = Axis(fig[1, 1]; xticks = 0:4:24)", "limits", "xticks = 0:4:24"),
        ("ax = Axis(fig[1, 1]; limits = (0, 10, 0, 5))", "limits", "limits = (0, 10, 0, 5)"),
        ("heatmap!(ax, z; colorrange = (-2, 2))", "color-scale", "colorrange = (-2, 2)"),
        ('text!(ax, 3.5, 4; text = "peak")', "annotations", "text!(ax, 3.5, 4"),
        ("hlines!(ax, 42)", "annotations", "hlines!(ax, 42)"),
        ("vspan!(ax, 10.5, 15.5)", "annotations", "vspan!(ax, 10.5, 15.5)"),
        ('label = "r = 0.87"', "statistics", '"r = 0.87"'),
        ("crit = 1.96", "statistics", "1.96"),
        ('const IMPRINT_PALETTE = [colorant"#009E73", colorant"#C475FD"]', "palette", "IMPRINT_PALETTE (2 entries)"),
        ("arrows!(ax, x, y, u, v)", "deprecated-api", "arrows!(ax, x, y, u, v)"),
    ],
)
def test_coupling_categories(line: str, category: str, snippet: str) -> None:
    found = coupling(HEAD + line + "\n" + SAVE)

    assert category in found.categories
    assert any(snippet in text for _, text in found.findings[category]), found.findings[category]


@pytest.mark.parametrize(
    "line",
    [
        "ylims!(ax, 0, nothing)",
        "hlines!(ax, 0)",
        'label = "r = $(round(r; digits = 2))"',
        "ylims!(ax, 0, maximum(df[!, Y]) * 1.1)",
        'text!(ax, "label"; position = Point2f(x, y))',
    ],
)
def test_computed_or_baseline_values_are_not_coupling(line: str) -> None:
    found = coupling(HEAD + line + "\n" + SAVE)

    assert set(found.findings) == set(), found.findings


def test_synthetic_data_in_a_block_without_constants_is_named_by_the_block() -> None:
    code = HEAD + "# Data\nx = randn(50)\n\n# Plot\nscatter!(Axis(fig[1, 1]), x, x)\n" + SAVE
    readiness = scan(code, spec_id="s", enabled_libraries=ENABLED)

    assert "synthetic-data: 1 line" in readiness.reasons
    assert any(
        hint.startswith("Synthetic data generation in the # Data block at lines 4-6") for hint in readiness.hints
    )


def test_a_seed_above_a_complete_block_does_not_couple() -> None:
    code = JULIA_CATALOGUE_NORMALISED.replace("using Random\n", "using Random\nRandom.seed!(7)\n")

    assert scan(code, spec_id="s", enabled_libraries=ENABLED).status == "clean"


def test_a_canvas_off_target_gets_a_canvas_reason() -> None:
    code = HEAD.replace("(1600, 900)", "(1600, 1100)") + "# Data\n# Plot\n" + SAVE
    readiness = scan(code, spec_id="s", enabled_libraries=ENABLED)

    assert readiness.status == "coupled"
    assert any(reason.startswith("canvas: the save renders 3200x2200") for reason in readiness.reasons)


def test_structure_reasons_of_a_good_file_are_empty() -> None:
    assert structure_reasons(JULIA_CATALOGUE_NORMALISED) == []


BLOCKING = frozenset({"map-spec", "library-disabled", "syntax", "security", "no-theme", "savefig-target"})
"""The reason categories of `blocked` (`readiness.scan`); a clean or coupled file carries none of them."""
STRING = re.compile(r'"(?:[^"\\\n]|\\.)*"')
COMMENT = re.compile(r"#.*$", re.MULTILINE)
"""A comment, once the strings are blanked: no `#` of a string (`colorant"#009E73"`) is left to start one."""
ARROWS_CALL = re.compile(r"(?<![\w!.])(?:[A-Za-z]\w*\.)?arrows!?\s*\(")
"""A call of `arrows!` or `arrows`, also qualified (`Makie.arrows!`), the Makie 0.24 calls that render with a
deprecation warning (not `arrows2d!`)."""
COMMON_HINTS = ("synthetic-data", "limits")
"""Hint categories the catalogue always has somewhere, so a detection that stops firing fails the corpus test."""


def code_only(text: str) -> str:
    """`text` with its strings blanked and its comments dropped, for a plain reading of the calls."""
    return COMMENT.sub("", STRING.sub('""', text))


def test_catalogue_corpus() -> None:
    """Every normalised Makie file is classified, and each class keeps its meaning while the catalogue changes. The
    counts of a day (325 files on 2026-10-29: none clean, since no file has column constants; 308 coupled, 17 blocked;
    data-block in 308, deprecated-api in 16) move with every regeneration, so the test holds rules: a file is blocked
    exactly when its spec is a map spec, the SECURITY profile flags it or its structure fails; a clean file has no
    reason; a coupled file has no blocking reason and one hint per reason but the `canvas:` one, which appears
    exactly where the normaliser could not measure the canvas, the `data-block` hint exactly when its layout is
    incomplete, and the `deprecated-api` hint exactly when its code calls `arrows!` or `arrows`; coupled and blocked
    files both occur, and so do the `COMMON_HINTS`."""
    statuses: Counter[str] = Counter()
    hinted: Counter[str] = Counter()
    for path in JULIA_CATALOGUE_FILES:
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
        assert ("data-block" in categories) == (not is_layout_complete(find_regions(normalised))), spec
        assert ("deprecated-api" in categories) == bool(ARROWS_CALL.search(code_only(normalised))), spec
        hinted.update(categories)

    assert sum(statuses.values()) == len(JULIA_CATALOGUE_FILES) and {"coupled", "blocked"} <= set(statuses)
    assert all(hinted[category] for category in COMMON_HINTS), hinted


@pytest.mark.parametrize("spec_id", ["biplot-pca", "contour-decision-boundary"])
def test_a_dataset_package_is_a_synthetic_data_hint(spec_id: str) -> None:
    code = normalise((REPO_ROOT / f"plots/{spec_id}/implementations/julia/makie.jl").read_text(encoding="utf-8"))
    readiness = scan(code, spec_id=spec_id, enabled_libraries=ENABLED)

    assert readiness.status == "coupled"
    assert any("RDatasets" in hint for hint in readiness.hints)


def test_the_detection_stays_inside_the_core_boundary() -> None:
    """coupling.py (the clean or coupled decision) imports only stdlib, tree-sitter, core.*, treesitter and the Julia
    regions, so it can move to core/ for the regen gate's adapt route (2026-10-29)."""
    tree = ast.parse((REPO_ROOT / "agents/anyplot/code/profiles/julia/coupling.py").read_text(encoding="utf-8"))
    relative = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.level}
    absolute = {
        node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and not node.level
    } | {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}

    assert relative == {"treesitter", "regions"}
    assert absolute <= {"re", "collections", "dataclasses", "tree_sitter", "core"}


def test_hints_are_short_and_name_lines() -> None:
    code = (
        source("""
        using CairoMakie
        const THEME = get(ENV, "ANYPLOT_THEME", "light")
        fig = Figure(size = (1600, 900))
        ax = Axis(fig[1, 1])
        xlims!(ax, 0, 10)
        ylims!(ax, 0, 20)
        text!(ax, 3, 4; text = "a")
        vlines!(ax, 5)
    """)
        + SAVE
    )
    readiness = scan(code, spec_id="s", enabled_libraries=ENABLED)

    assert readiness.status == "coupled"
    limits = next(hint for hint in readiness.hints if hint.startswith("Literal axis limits or ticks at"))
    assert "line 5" in limits and "line 6" in limits
    assert all(len(hint) <= MAX_REASON_CHARS for hint in readiness.hints)
