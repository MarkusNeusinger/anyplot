"""Tests for agents/anyplot/code/readiness.py: blocked, coupled and clean, against the real validator."""

from pathlib import Path

import pytest

from agents.anyplot.code import readiness
from agents.anyplot.code.normalise import normalise
from agents.anyplot.code.readiness import Readiness, scan
from agents.anyplot.code.validate import Finding, validate_security
from agents.anyplot.schemas import MAX_NOTE_CHARS
from core.spec_roles import MAP_SPECS

from .conftest import CATALOGUE_FILES, CATALOGUE_NORMALISED, source


ENABLED = ("matplotlib", "seaborn")
HEAD = source("""
    import os

    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd

    THEME = os.getenv("ANYPLOT_THEME", "light")
    PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
    df = load_user_data()
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
""")
SAVE = 'plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)\n'


@pytest.fixture
def validator_calls(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Wrap the real `validate_security` and record the library of every call."""
    calls: list[str] = []

    def spy(code: str, *, library: str) -> list[Finding]:
        calls.append(library)
        return validate_security(code, library=library)

    monkeypatch.setattr(readiness, "validate_security", spy)
    return calls


def check(body: str, *, spec_id: str = "scatter-basic", library: str = "matplotlib") -> Readiness:
    code = HEAD + source(body).rstrip("\n") + "\n" + SAVE
    result = scan(code, spec_id=spec_id, library=library, enabled_libraries=ENABLED)
    assert all(len(hint) <= MAX_NOTE_CHARS for hint in result.hints)
    assert all(len(reason) <= MAX_NOTE_CHARS for reason in result.reasons)
    return result


def categories(result: Readiness) -> list[str]:
    return [reason.split(":")[0] for reason in result.reasons]


ALL_ENABLED = ("matplotlib", "seaborn", "plotnine", "altair")
PLOTNINE_HEAD = source("""
    import os

    import pandas as pd
    from plotnine import aes, geom_point, ggplot

    THEME = os.getenv("ANYPLOT_THEME", "light")
    PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
    df = load_user_data()
    plot = ggplot(df, aes(x="x", y="y")) + geom_point(color=PAGE_BG)
""")
PLOTNINE_SAVE = 'plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)\n'
PLOTNINE_CANVAS = (
    "canvas: plotnine sizes its canvas on the save, not through a matplotlib figure; "
    "the render relies on the R3 canvas gate and padding"
)
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


class TestOtherPythonLibraries:
    """plotnine and altair go through the same scan with their own save rule (`regions.SAVE_RULES`)."""

    @pytest.mark.parametrize(
        "save",
        [PLOTNINE_SAVE, 'fig = plot.draw()\nfig.savefig(f"plot-{THEME}.png", dpi=300)\n'],
        ids=["plot.save", "fig.savefig after draw"],
    )
    def test_plotnine_save_forms_are_clean(self, save: str) -> None:
        result = scan(PLOTNINE_HEAD + save, spec_id="scatter-basic", library="plotnine", enabled_libraries=ALL_ENABLED)

        assert result.status == "clean" and result.hints == []
        assert result.reasons == [PLOTNINE_CANVAS]

    def test_plotnine_blocks_like_matplotlib(self) -> None:
        single = scan(
            PLOTNINE_HEAD + 'plot.save("plot.png", dpi=300)\n',
            spec_id="s",
            library="plotnine",
            enabled_libraries=ALL_ENABLED,
        )
        assert single.status == "blocked"
        assert any(r.startswith("savefig-target: single-theme save target 'plot.png'") for r in single.reasons)
        assert any(reason.startswith("security: savefig-target") for reason in single.reasons)

        path = scan(
            PLOTNINE_HEAD + 'plot.save(f"plot-{THEME}.png", path="out")\n',
            spec_id="s",
            library="plotnine",
            enabled_libraries=ALL_ENABLED,
        )
        assert path.status == "blocked"
        assert any(reason.endswith("save does not take 'path=' here") for reason in path.reasons), path.reasons

        nested = scan(
            PLOTNINE_HEAD + "if True:\n    " + PLOTNINE_SAVE,
            spec_id="s",
            library="plotnine",
            enabled_libraries=ALL_ENABLED,
        )
        assert "savefig-target: the last save is not a module-level statement" in nested.reasons

        disabled = scan(PLOTNINE_HEAD + PLOTNINE_SAVE, spec_id="s", library="plotnine", enabled_libraries=ENABLED)
        assert disabled.status == "blocked" and disabled.reasons == ["library-disabled: plotnine is not enabled"]

    def test_altair_file_with_the_pil_block_is_eligible(self) -> None:
        result = scan(ALTAIR, spec_id="scatter-basic", library="altair", enabled_libraries=ALL_ENABLED)

        assert result.status == "clean", result.reasons
        assert result.reasons == [PLOTNINE_CANVAS.replace("plotnine", "altair")]

        # Without the module-level PNG save the padding block's nested `_canvas.save` is the only writer of the PNG.
        nested_only = ALTAIR.replace('chart.save(f"plot-{THEME}.png", scale_factor=4.0)\n', "")
        blocked = scan(nested_only, spec_id="scatter-basic", library="altair", enabled_libraries=ALL_ENABLED)
        assert blocked.status == "blocked"
        assert blocked.reasons == ["savefig-target: the last save is not a module-level statement"]

        html_only = ALTAIR.split("chart.save(")[0] + 'chart.save(f"plot-{THEME}.html")\n'
        blocked = scan(html_only, spec_id="scatter-basic", library="altair", enabled_libraries=ALL_ENABLED)
        assert blocked.status == "blocked"
        assert blocked.reasons == ['security: savefig-target: no save of f"plot-{THEME}.png" found']

    def test_an_unsupported_library_is_blocked_before_its_save_rule(self) -> None:
        result = scan(PLOTNINE_HEAD + PLOTNINE_SAVE, spec_id="s", library="ggplot2", enabled_libraries=ALL_ENABLED)

        assert result.status == "blocked"
        assert result.reasons[:2] == [
            "library-disabled: ggplot2 is not enabled",
            "unsupported-library: no normaliser for ggplot2",
        ]


SIX_ENABLED = (*ALL_ENABLED, "pygal", "letsplot")
PYGAL = source("""
    import os

    import pygal
    from pygal.style import Style

    THEME = os.getenv("ANYPLOT_THEME", "light")
    PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
    df = load_user_data()
    chart = pygal.XY(width=4800, height=2700, style=Style(background=PAGE_BG), js=[])
    chart.add("a", list(zip(df["x"], df["y"])))
    chart.render_to_png(f"plot-{THEME}.png")
    with open(f"plot-{THEME}.html", "wb") as f:
        f.write(chart.render())
""")
LETSPLOT = source("""
    import os

    from lets_plot import *

    LetsPlot.setup_html()
    THEME = os.getenv("ANYPLOT_THEME", "light")
    PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
    df = load_user_data()
    plot = ggplot(df, aes(x="x", y="y")) + geom_point(color=PAGE_BG) + ggsize(1600, 900)
    ggsave(plot, f"plot-{THEME}.png", scale=3)
    ggsave(plot, f"plot-{THEME}.html")
""")


def scan_normalised(code: str, library: str) -> Readiness:
    return scan(
        normalise(code, library=library), spec_id="scatter-basic", library=library, enabled_libraries=SIX_ENABLED
    )


class TestPygalAndLetsPlot:
    """The catalogue shapes of pygal and lets-plot, normalised, and what the scan says where the normaliser stops."""

    @pytest.mark.parametrize(("code", "library"), [(PYGAL, "pygal"), (LETSPLOT, "letsplot")])
    def test_normalised_file_is_clean_and_on_the_canvas(self, code: str, library: str) -> None:
        assert scan_normalised(code, library) == Readiness("clean", [], [])

    @pytest.mark.parametrize(
        ("code", "library", "reason"),
        [
            # an unknown size can land over R2's pixel cap: no padding is promised
            (
                PYGAL.replace("width=4800, height=2700", "width=W, height=H"),
                "pygal",
                "canvas: pygal canvas unknown: the chart's width= at line 9 is not a positive number or a module-level "
                "name bound once to one; the PNG size shows only in the render, and R2 refuses one over its pixel cap",
            ),
            (
                LETSPLOT.replace("ggsize(1600, 900)", "ggsize(800, 853)"),
                "letsplot",
                "canvas: lets-plot renders 2400x2559 from 800x853 (ggsize at line 16) at scale 3, target 2400x2400; the "
                "render relies on the R3 canvas gate and padding",
            ),
            # a known size over the cap: R2 refuses it before R3 sees it
            (
                PYGAL.replace("width=4800, height=2700", "width=4800, height=3000"),
                "pygal",
                "canvas: pygal renders 4800x3000 (the saved chart at line 9), target 3200x1800; R2 refuses a PNG over "
                "its pixel cap",
            ),
        ],
    )
    def test_a_canvas_the_normaliser_cannot_set_is_a_note(self, code: str, library: str, reason: str) -> None:
        result = scan_normalised(code, library)

        assert result.status == "clean" and result.reasons == [reason]

    def test_a_hand_built_svg_gets_the_canvas(self) -> None:
        """dendrogram-radial and three more pygal files draw their SVG at 4800x2700 or 3600x3600 by hand."""
        code = source("""
            import os

            import cairosvg

            THEME = os.getenv("ANYPLOT_THEME", "light")
            PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
            df = load_user_data()
            W, H = 4800, 2700
            svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"><rect fill="{PAGE_BG}"/></svg>'
            cairosvg.svg2png(bytestring=svg.encode(), write_to=f"plot-{THEME}.png")
        """)
        before = scan(code, spec_id="scatter-basic", library="pygal", enabled_libraries=SIX_ENABLED)

        assert before.reasons == [
            "canvas: pygal renders 4800x2700 (the <svg> root at line 9), target 3200x1800; R2 refuses a PNG over its "
            "pixel cap"
        ]
        assert scan_normalised(code, "pygal") == Readiness("clean", [], [])

    @pytest.mark.parametrize(
        ("save", "reason"),
        [
            (
                'chart.render_to_file(f"plot-{THEME}.png")',  # SVG text in the PNG
                "savefig-target: render_to_file writes only .html files, not f'plot-{THEME}.png' at line 11",
            ),
            (
                'chart.render_to_png(f"plot-{THEME}.html")',  # a PNG in the HTML
                "savefig-target: render_to_png writes only .png files, not f'plot-{THEME}.html' at line 11",
            ),
        ],
    )
    def test_a_save_name_that_writes_another_kind_of_file_is_blocked(self, save: str, reason: str) -> None:
        code = PYGAL.replace('chart.render_to_png(f"plot-{THEME}.png")', save)
        result = scan_normalised(code, "pygal")

        assert result.status == "blocked" and reason in result.reasons, result.reasons

    def test_a_letsplot_save_without_the_directory_is_blocked(self) -> None:
        """Unnormalised: lets-plot would write into ./lets-plot-images, which the plot sandbox refuses."""
        result = scan(LETSPLOT, spec_id="scatter-basic", library="letsplot", enabled_libraries=SIX_ENABLED)

        assert result.status == "blocked"
        assert 'savefig-target: ggsave at line 10 does not save with path="."' in result.reasons
        assert 'savefig-target: ggsave at line 11 does not save with path="."' in result.reasons

    @pytest.mark.parametrize(
        ("code", "library", "reason"),
        [
            # a second star import: the normaliser keeps the lets-plot one, the validator refuses both
            (
                LETSPLOT.replace("from lets_plot import *", "from lets_plot import *\nfrom math import *"),
                "letsplot",
                "security: star-import at line 3: ",
            ),
            # the alias rename stops where the file binds `ggsave` itself
            (
                LETSPLOT.replace(
                    "from lets_plot import *",
                    "from lets_plot import *\nfrom lets_plot.export import ggsave as keep\nggsave = keep",
                ),
                "letsplot",
                "security: banned-call at line ",
            ),
            # an epilogue statement that does more than move files
            (LETSPLOT + 'print(os.listdir("lets-plot-images"))\n', "letsplot", "security: os-use at line 19: "),
            # an SVG save whose file the code reads again
            (
                PYGAL.replace(
                    'with open(f"plot-{THEME}.html", "wb") as f:\n    f.write(chart.render())',
                    'chart.render_to_file(f"plot-{THEME}.svg")\nprint(f"plot-{THEME}.svg")',
                ),
                "pygal",
                "savefig-target: render_to_file saves to f'plot-{THEME}.svg' at line 13",
            ),
            # a hand-built page whose file the code names again: the `open()` write stays
            (
                PYGAL.replace(
                    'with open(f"plot-{THEME}.html", "wb") as f:\n    f.write(chart.render())',
                    'with open(f"plot-{THEME}.html", "w") as f:\n    f.write("<html/>")\nprint(f"plot-{THEME}.html")',
                ),
                "pygal",
                "security: banned-name at line 13: 'open'",
            ),
        ],
    )
    def test_what_the_normaliser_leaves_is_blocked(self, code: str, library: str, reason: str) -> None:
        result = scan_normalised(code, library)

        assert result.status == "blocked" and result.hints == []
        assert any(r.startswith(reason) for r in result.reasons), result.reasons


def test_clean(validator_calls: list[str]) -> None:
    result = check('ax.plot(df["x"], df["y"], color=PAGE_BG)\nax.set_ylim(bottom=0)\nax.axhline(0)\n')

    assert result == Readiness("clean", [], [])
    assert validator_calls == ["matplotlib"]


def test_normalised_catalogue_file_is_coupled() -> None:
    result = scan(CATALOGUE_NORMALISED, spec_id="scatter-demo", library="matplotlib", enabled_libraries=ENABLED)

    assert result.status == "coupled"
    assert categories(result) == ["limits", "palette", "synthetic-data"]
    assert result.hints[0].startswith("Literal axis limits or ticks at line 20 `ax.set_ylim(0, 25)`")
    assert "IMPRINT (3 entries)" in result.hints[1]
    assert "line 14 `np.random.seed(42)`" in result.hints[2]


@pytest.mark.parametrize(
    ("body", "category"),
    [
        ("ax.set_xlim(0, 100)", "limits"),
        ("ax.set_xticks([0, 5, 10])", "limits"),
        ("ax.set_yticks(np.arange(0, 101, 20))", "limits"),
        ('ax.set_xlim(pd.Timestamp("2024-01-01"), df["d"].max())', "limits"),
        ("plt.ylim(-1.05, 1.05)", "limits"),
        ('ax.imshow(df[["a", "b"]], vmin=0, vmax=100)', "color-scale"),
        ('sns.heatmap(df[["a", "b"]], center=50)', "color-scale"),
        ('sns.heatmap(df[["a", "b"]], cbar_kws={"ticks": [0, 25, 50, 75, 100]})', "color-scale"),
        ('sns.heatmap(df[["a", "b"]], cbar_kws=dict(ticks=[0, 50, 100]))', "color-scale"),
        ('ax.contourf(df[["a", "b"]], levels=[0, 10, 20])', "color-scale"),
        ('ax.contourf(df[["a", "b"]], levels=np.linspace(0, 100, 11))', "color-scale"),
        ("fig.colorbar(mesh, ticks=[0, 50, 100])", "color-scale"),
        ("cbar.set_ticks([0, 50, 100])", "color-scale"),
        ("mesh.set_clim(10, 90)", "color-scale"),
        ("from matplotlib.colors import TwoSlopeNorm\nnorm = TwoSlopeNorm(vcenter=50)", "color-scale"),
        ("from matplotlib.colors import PowerNorm\nnorm = PowerNorm(0.5, 10, 90)", "color-scale"),
        ("from matplotlib.colors import BoundaryNorm\nnorm = BoundaryNorm([0, 10, 20], 256)", "color-scale"),
        ('g = sns.clustermap(df[["a", "b"]], cbar_pos=(0.05, 0.15, 0.04, 0.6))', "colorbar-position"),
        ('ax.annotate("Peak", xy=(5, 92.3))', "annotations"),
        ('ax.annotate("Peak", (df["x"][3], 92.3), xytext=(10, 10), textcoords="offset points")', "annotations"),
        ('ax.text(2.5, 40, "label")', "annotations"),
        ("ax.axvline(x=1990)", "annotations"),
        ("ax.axhspan(10, 20, xmin=0, xmax=1)", "annotations"),
        ("ax.hlines(50, 0, df['x'].max())", "annotations"),
        ('ax.legend(title="r = 0.87")', "statistics"),
        ('ax.text(0.5, 0.5, "p < 0.001", transform=ax.transAxes)', "statistics"),
        ('label = "n = 180 students"', "statistics"),
        ("upper = mean + 1.96 * se", "statistics"),
        ('IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]', "palette"),
        ('COLORS = ["#009E73", "#AE3030"]', "palette"),
        ("ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))", "date-locators"),
        ('ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))', "date-locators"),
        ("x = np.random.default_rng(1).normal(size=10)", "synthetic-data"),
        ("rng = np.random.default_rng(1)\ny = rng.normal(size=10)", "synthetic-data"),
        ("from scipy import stats\nsample = stats.norm.rvs(size=50)", "synthetic-data"),
    ],
)
def test_each_coupling_rule(body: str, category: str) -> None:
    result = check(body)

    assert result.status == "coupled"
    assert categories(result) == [category]
    assert len(result.hints) == 1 and "line " in result.hints[0]


@pytest.mark.parametrize(
    "body",
    [
        "ax.set_ylim(0, None)",
        'ax.set_xlim(df["x"].min(), df["x"].max() * 1.15)',
        "ax.set_xticks([])",
        'ax.text(0.02, 0.95, "note", transform=ax.transAxes)',
        'fig.text(0.98, 0.02, "source", ha="right")',
        'ax.annotate("top", xy=(0.5, 1.02), xycoords="axes fraction")',
        'r = 0.5\nax.set_title(f"r = {r:.2f}")',
        "ax.xaxis.set_major_locator(mdates.AutoDateLocator())",
        'IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]',
        'GRAYS = ["#111111", "#222222"]',
        'ax.imshow(df[["a", "b"]], vmin=0, vmax=df["a"].max())',
        'sns.heatmap(df[["a", "b"]], center=0)',
        'ax.contourf(df[["a", "b"]], levels=10)',
        'ax.hist2d(df["a"], df["b"], cmin=1)',
        # A norm's encoding parameter is no range (review of #12206: scatter-constellation-diagram's PowerNorm).
        'from matplotlib.colors import PowerNorm\nnorm = PowerNorm(gamma=0.7, vmin=df["a"].min(), vmax=df["a"].max())',
        "from matplotlib.colors import PowerNorm\nnorm = PowerNorm(0.5)",
        'from matplotlib.colors import SymLogNorm\nnorm = SymLogNorm(linthresh=1.0, vmin=df["a"].min())',
        "ax.set_ticks([1, 2, 3])",
        # `center` that places marks and `levels` that are density proportions map no color (review of #12206).
        'ax.pie(df["a"], center=(0.5, 0.5))',
        "pos = nx.spring_layout(G, center=(1, 1))",
        'label = "abc".center(10)',
        'sns.kdeplot(data=df, x="a", y="b", levels=[0.2, 0.5, 0.8])',
    ],
)
def test_not_coupled(body: str) -> None:
    assert check(body).status == "clean"


def test_every_literal_of_a_line_reaches_the_hint_once() -> None:
    """Review of #12206: only the first literal of a line reached the hint, and a norm counted twice."""
    result = check('sns.heatmap(df[["a", "b"]], vmin=0, vmax=100, center=50, cbar_kws={"ticks": [0, 50, 100]})')

    (hint,) = result.hints
    assert "vmax=100" in hint and "center=50" in hint and '"ticks": [0, 50, 100]' in hint
    norm = check("from matplotlib.colors import Normalize\nnorm = Normalize(vmin=10, vmax=90)").hints[0]
    assert norm.count("vmin=10") == 1 and "Normalize(vmin=10, vmax=90)" in norm


@pytest.mark.skipif(not CATALOGUE_FILES, reason="plots/ is not checked out")
def test_the_seaborn_heatmap_names_its_color_scale_and_colorbar_place() -> None:
    """Live test round 8 of 2026-10-16: the adapter kept `vmin=0, vmax=100, center=50` and the colorbar ticks for
    data of 32 to 93, and the top-left `cbar_pos` after it dropped the dendrogram; the scan named neither."""
    path = next(path for path in CATALOGUE_FILES if path.parts[-4] == "heatmap-basic" and path.stem == "seaborn")
    code = normalise(path.read_text(encoding="utf-8"), library="seaborn")

    result = scan(code, spec_id="heatmap-basic", library="seaborn", enabled_libraries=ENABLED)

    assert categories(result)[:2] == ["color-scale", "colorbar-position"]
    color, place = result.hints[:2]
    assert "`center=50`" in color and "`vmax=100`" in color and '"ticks": [0, 25, 50, 75, 100]' in color
    assert "`cbar_pos=(0.05, 0.15, 0.04, 0.6)`" in place


def test_one_hint_per_category_names_lines_and_counts() -> None:
    body = "\n".join(
        f"ax.axvline({year}, color=PAGE_BG, linestyle='--', linewidth=0.8, alpha=0.5)" for year in range(1990, 2020)
    )
    result = check(body)

    assert result.reasons == ["annotations: 30 lines"]
    hint = result.hints[0]
    assert hint.startswith("Annotations at literal data coordinates at line 12 `ax.axvline(1990")
    assert " more: place them from df values or drop them." in hint
    assert len(hint) <= MAX_NOTE_CHARS


def test_canvas_note_does_not_change_status() -> None:
    code = HEAD.replace("figsize=(8, 4.5), dpi=400", "figsize=(16, 12)") + SAVE.replace("dpi=400", "dpi=200")
    result = scan(normalise(code, library="matplotlib"), spec_id="x", library="matplotlib", enabled_libraries=ENABLED)

    assert result.status == "clean"
    assert result.reasons[0].startswith("canvas: figsize (16, 12) at dpi 200 renders 3200x2400")


# --- blocked -------------------------------------------------------------------------------


@pytest.mark.parametrize("spec_id", sorted(MAP_SPECS))
def test_map_specs_are_blocked(spec_id: str) -> None:
    result = check("", spec_id=spec_id)

    assert result.status == "blocked" and categories(result) == ["map-spec"] and result.hints == []


def test_thirteen_map_specs() -> None:
    assert len(MAP_SPECS) == 13
    assert "scatter-pitch-events" not in MAP_SPECS and "hexbin-map-geographic" not in MAP_SPECS


def test_library_not_enabled_or_unsupported(validator_calls: list[str]) -> None:
    code = HEAD + SAVE

    disabled = scan(code, spec_id="scatter-basic", library="seaborn", enabled_libraries=["matplotlib"])
    assert disabled.status == "blocked" and categories(disabled) == ["library-disabled"]
    assert validator_calls == ["seaborn"]
    # No normaliser means no validator profile either: the validator is not asked. Every Python library has both since
    # PB-2a, so the Python scan's unsupported library is another language's.
    unsupported = scan(code, spec_id="scatter-basic", library="ggplot2", enabled_libraries=["ggplot2"])
    assert categories(unsupported) == ["unsupported-library"]
    assert validator_calls == ["seaborn"]


def test_security_findings_block() -> None:
    result = check('import subprocess\nsubprocess.run(["ls"])\nax.set_title(df.__class__.__name__)\n')

    assert result.status == "blocked" and result.hints == []
    assert result.reasons[0].startswith("security: banned-import at line 12: ")
    assert {reason.split(" ")[1] for reason in result.reasons} == {"banned-import", "dunder"}


def test_stdlib_random_is_blocked_not_coupled() -> None:
    result = check("import random\nvalue = random.uniform(0, 1)\n")

    assert result.status == "blocked" and result.hints == []
    assert result.reasons[0].startswith("security: banned-import at line 12")


def test_security_reasons_are_capped(monkeypatch: pytest.MonkeyPatch) -> None:
    findings = [
        Finding("banned-import", "import of 'subprocess' is not allowed", 3),
        Finding("size", "code is 70,000 characters; the limit is 65,536", None),
        *(Finding("dunder", f"dunder {i}", i) for i in range(5)),
    ]
    monkeypatch.setattr(readiness, "validate_security", lambda code, *, library: findings)
    result = check("")

    assert result.status == "blocked"
    assert result.reasons[0] == "security: banned-import at line 3: import of 'subprocess' is not allowed"
    assert result.reasons[1] == "security: size: code is 70,000 characters; the limit is 65,536"
    assert result.reasons[-1] == "security: 2 more findings"


def test_compile_only_syntax_error_blocks() -> None:
    """`ast.parse` accepts a module-level `return`; the validator compiles and reports it."""
    result = check("return\n")

    assert result.status == "blocked"
    assert any(reason.startswith("security: syntax at line 12") for reason in result.reasons), result.reasons


def test_crashing_validator_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    def explode(code: str, *, library: str) -> list[Finding]:
        raise RuntimeError("boom")

    monkeypatch.setattr(readiness, "validate_security", explode)
    assert check("").reasons == ["security: the validator failed (RuntimeError)"]


@pytest.mark.parametrize(
    ("code", "reason"),
    [
        (HEAD.replace('THEME = os.getenv("ANYPLOT_THEME", "light")', 'THEME = "light"') + SAVE, "no-theme"),
        (HEAD + 'plt.savefig("plot.png", dpi=400)\n', "savefig-target: single-theme savefig target 'plot.png'"),
        (HEAD + 'plt.savefig(os.path.join(d, f"plot-{THEME}.png"))\n', "savefig-target: savefig saves to os.path.join"),
        (HEAD + "if True:\n    " + SAVE, "savefig-target: the last savefig is not a module-level statement"),
        (HEAD, "savefig-target: no savefig call"),
        (HEAD + 'fig.savefig("draft.png")\n' + SAVE, "savefig-target: single-theme savefig target 'draft.png'"),
    ],
)
def test_structure_blocks(code: str, reason: str) -> None:
    result = scan(code, spec_id="scatter-basic", library="matplotlib", enabled_libraries=ENABLED)

    assert result.status == "blocked"
    assert any(r.startswith(reason) for r in result.reasons), result.reasons


def test_syntax_error_blocks_without_calling_the_validator(validator_calls: list[str]) -> None:
    result = scan("def broken(:\n", spec_id="x", library="matplotlib", enabled_libraries=ENABLED)

    assert result == Readiness("blocked", ["syntax: line 1 does not parse"], [])
    assert validator_calls == []


# --- catalogue sweep ------------------------------------------------------------------------


@pytest.mark.skipif(not CATALOGUE_FILES, reason="plots/ is not checked out")
@pytest.mark.parametrize("path", CATALOGUE_FILES, ids=lambda p: f"{p.parts[-4]}-{p.stem}")
def test_catalogue_scan_never_raises(path: Path) -> None:
    code = normalise(path.read_text(encoding="utf-8"), library=path.stem)
    result = scan(code, spec_id=path.parts[-4], library=path.stem, enabled_libraries=ENABLED)

    assert result.status in ("blocked", "coupled", "clean")
    assert all(len(text) <= MAX_NOTE_CHARS for text in [*result.reasons, *result.hints])
    assert (result.status == "coupled") == bool(result.hints)
