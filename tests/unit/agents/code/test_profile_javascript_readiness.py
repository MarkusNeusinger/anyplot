"""Tests for agents/anyplot/code/profiles/javascript/readiness.py and coupling.py: blocked, coupled or clean."""

import ast
from collections import Counter

import pytest

from agents.anyplot.code.profiles.javascript.coupling import coupling, structure_reasons
from agents.anyplot.code.profiles.javascript.normalise import normalise
from agents.anyplot.code.profiles.javascript.readiness import scan
from agents.anyplot.code.profiles.javascript.regions import LIBRARIES
from agents.anyplot.schemas import MAX_NOTE_CHARS as MAX_REASON_CHARS

from .conftest import JS_CATALOGUE_FILES, JS_CATALOGUE_NORMALISED, MUIX_WORKING, REPO_ROOT, js_library, source


HEAD = (
    "//# anyplot-orientation: landscape\n"
    "const t = window.ANYPLOT_TOKENS;\n"
    'const canvas = document.createElement("canvas");\n'
)
ENABLED = list(LIBRARIES)


def ready(body: str, library: str = "chartjs", spec_id: str = "s"):
    return scan(HEAD + body + "\n", spec_id=spec_id, enabled_libraries=ENABLED, library=library)


def test_the_catalogue_file_in_miniature_is_clean() -> None:
    readiness = scan(JS_CATALOGUE_NORMALISED, spec_id="scatter-demo", enabled_libraries=ENABLED, library="chartjs")

    assert (readiness.status, readiness.reasons, readiness.hints) == ("clean", [], [])


@pytest.mark.parametrize(
    ("spec_id", "enabled", "reason"),
    [
        ("choropleth-basic", ENABLED, "map-spec: choropleth-basic"),
        ("scatter-demo", ["d3"], "library-disabled: chartjs"),
    ],
)
def test_blocked_by_spec_or_library(spec_id: str, enabled: list[str], reason: str) -> None:
    readiness = scan(JS_CATALOGUE_NORMALISED, spec_id=spec_id, enabled_libraries=enabled, library="chartjs")

    assert readiness.status == "blocked"
    assert readiness.reasons[0].startswith(reason)


@pytest.mark.parametrize(
    ("code", "reason"),
    [
        ("const a = (;\n", "syntax: "),
        ("//# anyplot-orientation: landscape\nconst a = 1;\n", "no-theme: "),
        (HEAD + "const s = `\n//# anyplot-orientation: square\n`;\n", "savefig-target: "),
        (HEAD + "//# anyplot-orientation: square\n", "savefig-target: "),
        (HEAD + 'fetch("/data.json");\n', "security: banned-name"),
        (HEAD + 'const u = "https://anyplot.ai";\n', "security: url-literal"),
    ],
)
def test_blocked_for_real_reasons(code: str, reason: str) -> None:
    readiness = scan(code, spec_id="s", enabled_libraries=ENABLED, library="chartjs")

    assert readiness.status == "blocked"
    assert any(text.startswith(reason) for text in readiness.reasons), readiness.reasons


def test_security_reasons_are_capped() -> None:
    readiness = ready("".join(f'fetch("/{index}");\n' for index in range(10)))

    assert readiness.status == "blocked"
    assert readiness.reasons[5].startswith("security: ") and readiness.reasons[5].endswith("more findings")


def test_a_missing_marker_never_blocks() -> None:
    readiness = ready("new Chart(canvas, { data: { datasets: [] } });")

    assert readiness.status == "coupled"
    assert readiness.reasons == [
        "data-block: no // Data and // Plot markers, so the sample is built among the plot code"
    ]


@pytest.mark.parametrize(
    ("line", "category", "snippet"),
    [
        ("const y = Math.random() * 40;", "synthetic-data", "Math.random()"),
        ("const n = d3.randomNormal(0, 1);", "synthetic-data", "d3.randomNormal"),
        ("let seed = 42; seed = (seed * 1664525 + 1013904223) >>> 0;", "synthetic-data", "1664525"),
        ("const v = [" + ", ".join(str(index) for index in range(25)) + "];", "synthetic-data", "[0, 1, 2"),
        ("const opts = { scales: { y: { min: 0, max: 100 } } };", "limits", "max: 100"),
        ("const opts = { yAxis: { softMax: 12 } };", "limits", "softMax: 12"),
        ("const x = d3.scaleLinear().domain([0, 23.5]);", "limits", "d3.scaleLinear().domain([0, 23.5])"),
        ("const ax = d3.axisBottom(x).tickValues([1, 2, 3]);", "limits", "tickValues([1, 2, 3])"),
        ("const c = d3.scaleSequential().domain([-2, 2]);", "color-scale", "domain([-2, 2])"),
        ("const opts = { visualMap: { min: -5, max: 5 } };", "color-scale", "max: 5"),
        ("const opts = { colorAxis: { max: 40 } };", "color-scale", "max: 40"),
        ("const opts = { series: [{ markLine: { data: [{ yAxis: 42 }] } }] };", "annotations", "yAxis: 42"),
        ("const opts = { yAxis: { plotLines: [{ value: 50 }] } };", "annotations", "value: 50"),
        ("const x = d3.scaleLinear(); const px = x(2015);", "annotations", "x(2015)"),
        ("const px = yScale(new Date(2024, 0, 1));", "annotations", "yScale(new Date(2024, 0, 1))"),
        ("const p = chart.scales.y.getPixelForValue(50);", "annotations", "getPixelForValue(50)"),
        ('const label = "r = 0.87";', "statistics", '"r = 0.87"'),
        ("const crit = 1.96;", "statistics", "1.96"),
        ('const IMPRINT_PALETTE = ["#009E73", "#C475FD"];', "palette", "IMPRINT_PALETTE (2 entries)"),
    ],
)
def test_coupling_categories(line: str, category: str, snippet: str) -> None:
    found = coupling(HEAD + line + "\n")

    assert category in found.categories
    assert any(snippet in text for _, text in found.findings[category]), found.findings[category]


def test_a_reference_line_at_a_literal_in_muix() -> None:
    code = MUIX_WORKING.replace(
        "skipAnimation\n", "skipAnimation\n          />\n          <ChartsReferenceLine y={20}\n"
    )
    found = coupling(code, library="muix")

    assert any("y={20}" in text for _, text in found.findings["annotations"])


@pytest.mark.parametrize(
    "line",
    [
        "const opts = { scales: { y: { min: 0 } } };",
        "const x = d3.scaleLinear().domain([0, d3.max(data, (d) => d.v)]);",
        "const label = `r = ${r.toFixed(2)}`;",
        "const opts = { yAxis: { plotLines: [{ value: 0 }] } };",
        "const px = x(d.value);",
        "const point = { x: 10, y: 20 };",
    ],
)
def test_computed_or_baseline_values_are_not_coupling(line: str) -> None:
    found = coupling(HEAD + line + "\n")

    assert set(found.findings) == set(), found.findings


def test_synthetic_data_in_a_block_without_constants_is_named_by_the_block() -> None:
    readiness = ready("// Data\nconst y = Math.random();\n\n// Plot\nnew Chart(canvas, {});")

    assert "synthetic-data: 1 line" in readiness.reasons
    assert any(
        hint.startswith("Synthetic data generation in the // Data block at lines 4-6") for hint in readiness.hints
    )


def test_muix_7_imports_are_a_coupled_hint_never_a_block() -> None:
    """Owner decision of 2026-10-30 (question 13): a MUI X file written for 7.29 is served, coupled with a note that
    names each import the image's MUI X does not export."""
    code = MUIX_WORKING.replace("const data = loadUserData();", "const data = [];").replace(
        'import Typography from "@mui/material/Typography";',
        'import Typography from "@mui/material/Typography";\n'
        'import { ChartContainer } from "@mui/x-charts/ChartContainer";\n'
        'import { ChartContainer as Root } from "@mui/x-charts";',
    )
    readiness = scan(code, spec_id="s", enabled_libraries=ENABLED, library="muix")

    assert readiness.status == "coupled"
    assert "deprecated-api: 2 lines" in readiness.reasons
    hint = next(hint for hint in readiness.hints if hint.startswith("MUI X 7 imports"))
    assert hint == (
        'MUI X 7 imports the image\'s MUI X 9.16.0 lacks at line 4 `"@mui/x-charts/ChartContainer"`; '
        'line 5 `ChartContainer from "@mui/x-charts"`: use MUI X 9\'s (ChartContainer is ChartsContainer from '
        "@mui/x-charts/ChartsContainer)."
    )


def test_structure_reasons_of_a_good_file_are_empty() -> None:
    assert structure_reasons(JS_CATALOGUE_NORMALISED) == []


def test_catalogue_corpus() -> None:
    """The split over the 1,617 normalised files on 2026-10-30, per library: no file of the four classic-script
    libraries is clean (none carries column constants), 93 MUI X files regenerated for 9.16 are; 68 are blocked, the
    13 map specs a library has, qrcode-basic in all five (the encoded URL, `url-literal`) and line-parametric's
    Chart.js legend (a 683-character HTML string, `string-length`). The 51 MUI X 7.29 files that import
    `@mui/x-charts/ChartContainer` are coupled with the `deprecated-api` hint (owner decision of 2026-10-30)."""
    statuses: dict[str, Counter[str]] = {library: Counter() for library in LIBRARIES}
    blocked: dict[str, str] = {}
    categories: Counter[str] = Counter()
    for path in JS_CATALOGUE_FILES:
        library, spec = js_library(path), path.parts[-4]
        normalised = normalise(path.read_text(encoding="utf-8"), library=library)
        readiness = scan(normalised, spec_id=spec, enabled_libraries=ENABLED, library=library)
        statuses[library][readiness.status] += 1
        if readiness.status == "blocked":
            blocked[f"{spec}/{library}"] = readiness.reasons[0].split(":", 1)[0]
        categories.update(reason.split(":", 1)[0] for reason in readiness.reasons)
        assert all(len(hint) <= MAX_REASON_CHARS for hint in readiness.hints)

    assert statuses == {
        "chartjs": {"coupled": 306, "blocked": 15},
        "d3": {"coupled": 311, "blocked": 14},
        "echarts": {"coupled": 311, "blocked": 14},
        "highcharts": {"coupled": 310, "blocked": 13},
        "muix": {"clean": 93, "coupled": 218, "blocked": 12},
    }
    assert Counter(blocked.values()) == {"map-spec": 62, "security": 6}
    assert {name for name, reason in blocked.items() if reason == "security"} == {
        *(f"qrcode-basic/{library}" for library in LIBRARIES),
        "line-parametric/chartjs",
    }
    assert categories["deprecated-api"] == 51
    assert categories["data-block"] == 1434  # every coupled file but 22 regenerated MUI X files with the layout


def test_the_detection_stays_inside_the_core_boundary() -> None:
    """coupling.py imports only stdlib, tree-sitter, core.*, treesitter, the regions and the allowlist copy, so it can
    move to core/ for the regen gate's adapt route (2026-10-30)."""
    tree = ast.parse((REPO_ROOT / "agents/anyplot/code/profiles/javascript/coupling.py").read_text(encoding="utf-8"))
    relative = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.level}
    absolute = {
        node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and not node.level
    } | {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}

    assert relative == {"treesitter", "regions", "allowlist"}
    assert absolute <= {"re", "collections", "dataclasses", "tree_sitter", "core"}


def test_hints_are_short_and_name_lines() -> None:
    code = HEAD + source("""
        const opts = {
          scales: {
            x: { min: 0, max: 10 },
            y: { min: 0, max: 20 },
          },
        };
        const x = (v) => v;
        const px = x(5);
    """)
    readiness = scan(code, spec_id="s", enabled_libraries=ENABLED, library="chartjs")

    assert readiness.status == "coupled"
    limits = next(hint for hint in readiness.hints if hint.startswith("Literal axis limits or ticks at"))
    assert "line 6" in limits and "line 7" in limits
    assert all(len(hint) <= MAX_REASON_CHARS for hint in readiness.hints)
