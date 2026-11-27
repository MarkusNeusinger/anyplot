"""automation/scripts/contract_check.py: the static contract of an implementation file, record-only.

The sources here never come from `plots/` at test time. The catalogue changes
every night, so a test that reads it would pin counts that a regeneration
moves. The base rules use synthetic sources; the library mandates use
excerpts of real files pasted in, each with the commit and pull request it
comes from, so a pattern is tested against the spellings the generator writes.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from automation.scripts import contract_check
from automation.scripts.contract_check import (
    ADVISORY,
    BASE_REASONS,
    MANDATES,
    PALETTE_HEXES,
    RETIRED_RAMP_STOPS,
    RULES,
    build_record,
    check,
    notice_line,
    reason,
    selfcheck_lines,
    strip_comments,
    strip_header,
    summary_line,
    violations,
)
from core import palette


SCRIPT = Path(contract_check.__file__)
ROOT = SCRIPT.parents[2]
SPEC = "scatter-basic"

PYTHON = '''""" anyplot.ai
scatter-basic: Basic Scatter Plot
Library: matplotlib 3.11.0 | Python 3.14.9
Quality: pending | Created: 2026-11-10
"""

import os

import matplotlib.pyplot as plt

THEME = os.getenv("ANYPLOT_THEME", "light")
fig, ax = plt.subplots()
ax.scatter([1, 2], [3, 4], color="#009E73")
ax.set_title("scatter-basic · python · matplotlib · anyplot.ai")
fig.savefig(f"plot-{THEME}.png", dpi=200)
'''

R = """#' anyplot.ai
#' scatter-basic: Basic Scatter Plot
#' Library: ggplot2 4.0.1 | R 4.5.2
#' Quality: pending | Created: 2026-11-10

library(ggplot2)
THEME <- Sys.getenv("ANYPLOT_THEME", "light")
p <- ggplot(df, aes(x, y)) + geom_point(colour = "#009E73") +
  labs(title = "scatter-basic · r · ggplot2 · anyplot.ai")
ggsave(sprintf("plot-%s.png", THEME), p, width = 16, height = 9, dpi = 200)
"""

JULIA = """# anyplot.ai
# scatter-basic: Basic Scatter Plot
# Library: makie 0.22.10 | Julia 1.12.1
# Quality: pending | Created: 2026-11-10

using CairoMakie
THEME = get(ENV, "ANYPLOT_THEME", "light")
fig = Figure()
ax = Axis(fig[1, 1], title = "scatter-basic · julia · makie · anyplot.ai")
scatter!(ax, x, y, color = "#009E73")
save("plot-$(THEME).png", fig)
"""

JAVASCRIPT = """// anyplot.ai
// scatter-basic: Basic Scatter Plot
// Library: d3 7.9.0 | JavaScript
//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;
const SPEC_ID = "scatter-basic";
svg.append("text").text(`${SPEC_ID} · javascript · d3 · anyplot.ai`).attr("fill", t.ink);
const ramp = d3.interpolateRgb("#009E73", "#4467A3");
"""

CLEAN = {
    "python": (PYTHON, "matplotlib"),
    "r": (R, "ggplot2"),
    "julia": (JULIA, "makie"),
    "javascript": (JAVASCRIPT, "d3"),
}


def _check(language: str, source: str, library: str | None = None) -> list[str]:
    return violations(source, spec_id=SPEC, language=language, library=library or CLEAN[language][1])


@pytest.mark.parametrize("language", sorted(CLEAN))
def test_a_compliant_file_breaks_no_rule(language):
    assert _check(language, CLEAN[language][0]) == []


@pytest.mark.parametrize(
    ("language", "old", "new", "rules"),
    [
        # title: the tail without the language segment, a capitalised language, another site, no spec id
        ("python", "scatter-basic · python · matplotlib", "scatter-basic · matplotlib", ["title"]),
        ("python", "· python ·", "· Python ·", ["title"]),
        ("r", 'anyplot.ai")', 'pyplots.ai")', ["title"]),
        ("julia", "scatter-basic · julia", "Basic Scatter · julia", ["title"]),
        ("javascript", 'const SPEC_ID = "scatter-basic";', 'const SPEC_ID = "x";', ["title"]),
        # theme: the file never names it
        ("python", 'os.getenv("ANYPLOT_THEME", "light")', '"light"', ["theme"]),
        ("r", 'Sys.getenv("ANYPLOT_THEME", "light")', '"light"', ["theme"]),
        ("julia", 'get(ENV, "ANYPLOT_THEME", "light")', '"light"', ["theme"]),
        ("javascript", "window.ANYPLOT_TOKENS", "{ ink: '#1A1A17' }", ["theme"]),
        # save: a fixed name, a hard-coded theme, or a legacy name beside the themed one
        ("python", 'f"plot-{THEME}.png"', '"output.png"', ["save"]),
        ("python", 'f"plot-{THEME}.png"', '"plot-light.png"', ["save"]),
        ("python", "fig.savefig(f", 'fig.savefig("plot.png")\nfig.savefig(f', ["save"]),
        ("python", "fig.savefig(f", 'fig.write_html("plot.html")\nfig.savefig(f', ["save"]),
        ("python", "fig.savefig(f", "fig.savefig('./plot.svg')\nfig.savefig(f", ["save"]),
        ("r", 'sprintf("plot-%s.png", THEME)', '"plot.png"', ["save"]),
        ("julia", '"plot-$(THEME).png"', '"plot-light.png"', ["save"]),
        # legacy brand colours, in any case and with an alpha suffix; they are outside the palette too
        ("python", '"#009E73"', '"#306998"', ["legacy-colour", "palette"]),
        ("r", '"#009E73"', '"#ffd43b"', ["legacy-colour", "palette"]),
        ("javascript", '"#009E73", "#4467A3"', '"#9418DB", "#4467A3"', ["legacy-colour", "palette"]),
        ("python", '"#009E73"', '"#30699880"', ["legacy-colour"]),
        # a stop of a replaced continuous ramp, in any case and with an alpha suffix; it is outside the palette too
        ("python", '"#009E73"', '"#002850"', ["retired-ramp", "palette"]),
        ("r", '"#009E73"', '"#00573d"', ["retired-ramp", "palette"]),
        ("javascript", '"#009E73", "#4467A3"', '"#007755", "#4467A3"', ["retired-ramp", "palette"]),
        ("python", '"#009E73"', '"#007755CC"', ["retired-ramp"]),
        # a named library colormap where a colormap goes: one case per pattern
        ("python", 'color="#009E73"', 'c=[1, 2], cmap="viridis"', ["colormap"]),
        ("python", 'color="#009E73"', 'c=[1, 2], cmap="terrain"', ["colormap"]),
        ("python", 'color="#009E73"', 'coloraxis_colorscale="Viridis"', ["colormap"]),
        ("python", 'color="#009E73"', 'palette="Blues"', ["colormap"]),
        ("python", 'color="#009E73"', 'color=alt.Color("v", scale=alt.Scale(scheme="brownbluegreen"))', ["colormap"]),
        ("python", 'color="#009E73"', 'c=[1, 2], cmap=sns.color_palette("rocket", as_cmap=True)', ["colormap"]),
        ("python", 'color="#009E73"', 'c=[1, 2], cmap=plt.get_cmap("magma")', ["colormap"]),
        ("python", 'color="#009E73"', 'c=[1, 2], cmap=matplotlib.colormaps["RdBu"]', ["colormap"]),
        ("python", 'color="#009E73"', "c=[1, 2], cmap=plt.cm.Blues_r", ["colormap"]),
        ("python", 'color="#009E73"', "c=mpl_cm.viridis(0.5)", ["colormap"]),
        ("python", 'color="#009E73"', "color=z) + scale_fill_distiller(", ["colormap"]),
        ("python", 'color="#009E73"', "color=Viridis256[10]", ["colormap"]),
        ("python", 'color="#009E73"', "color=bokeh.palettes.Spectral11[0]", ["colormap"]),
        ("r", 'geom_point(colour = "#009E73")', "geom_point() + scale_colour_viridis_c()", ["colormap"]),
        ("r", 'geom_point(colour = "#009E73")', "geom_point(colour = rainbow(5)[1])", ["colormap"]),
        ("r", 'geom_point(colour = "#009E73")', 'geom_point(colour = brewer.pal(9, "Blues")[5])', ["colormap"]),
        ("r", 'geom_point(colour = "#009E73")', "geom_point(colour = viridis::viridis(5)[1])", ["colormap"]),
        ("julia", 'color = "#009E73"', "color = z, colormap = :viridis", ["colormap"]),
        ("julia", 'color = "#009E73"', 'color = z, colormap = "plasma"', ["colormap"]),
        ("julia", 'color = "#009E73"', "color = z, colormap = cgrad(:RdBu, 5)", ["colormap"]),
        ("javascript", 'd3.interpolateRgb("#009E73", "#4467A3")', "d3.interpolateViridis", ["colormap"]),
        ("javascript", 'd3.interpolateRgb("#009E73", "#4467A3")', "d3.schemeCategory10", ["colormap"]),
        # a colour outside the Imprint palette, its anchors and the theme tokens
        ("python", '"#009E73"', '"#3A3A36"', ["palette"]),
        ("python", '"#009E73"', '"#FFFFFF"', ["palette"]),
        ("r", '"#009E73"', '"#f0d9b5"', ["palette"]),
        ("julia", '"#009E73"', '"#888888"', ["palette"]),
        ("javascript", '"#009E73", "#4467A3"', '"#440154", "#4467A3"', ["palette"]),
    ],
)
def test_a_broken_rule_is_named(language, old, new, rules):
    source = CLEAN[language][0]
    assert old in source
    assert _check(language, source.replace(old, new)) == rules


def test_javascript_is_exempt_from_the_save_rule():
    """The render harness saves, so a snippet names no file."""
    assert "save" not in _check("javascript", JAVASCRIPT)
    assert ".png" not in JAVASCRIPT


@pytest.mark.parametrize(
    ("language", "old", "new"),
    [
        # A data label that happens to be a colormap's name is not a colormap.
        ("python", "[1, 2], [3, 4]", '[1, 2], [3, 4], label="Oranges"'),
        ("python", "[1, 2], [3, 4]", '[1, 2], [3, 4], label="Spectral Type"'),
        ("javascript", "const ramp", 'const label = "Blues and Greens";\nconst ramp'),
        ("r", 'colour = "#009E73"', "colour = hsv_value"),
        # The save target under a directory, and the other ways to build the name.
        ("python", 'f"plot-{THEME}.png"', 'f"{out_dir}/plot-{THEME}.png"'),
        ("python", 'f"plot-{THEME}.png"', '"plot-%s.png" % THEME'),
        ("python", 'f"plot-{THEME}.png"', '"plot-" + THEME + ".png"'),
        ("python", 'f"plot-{THEME}.png"', '"plot-{}.png".format(THEME)'),
        ("r", 'sprintf("plot-%s.png", THEME)', 'paste0("plot-", THEME, ".png")'),
        ("r", 'sprintf("plot-%s.png", THEME)', 'paste0("output/plot-", THEME, ".png")'),
        ("julia", '"plot-$(THEME).png"', '"plot-$THEME.png"'),
        ("julia", '"plot-$(THEME).png"', '"plot-" * THEME * ".png"'),
        ("julia", '"plot-$(THEME).png"', 'string("plot-", THEME, ".png")'),
        # A title built over two lines of paste0.
        (
            "r",
            'labs(title = "scatter-basic · r · ggplot2 · anyplot.ai")',
            'labs(title = paste0("Revenue · scatter-basic",\n    " · r · ggplot2 · anyplot.ai"))',
        ),
        # A "#" or "//" inside a string is not a comment.
        ("python", '"scatter-basic · python', '"Issue # 42 · scatter-basic · python'),
        ("r", '"scatter-basic · r', '"Run # 7 · scatter-basic · r'),
        ("javascript", "const ramp", 'const link = "https://anyplot.ai/scatter-basic";\nconst ramp'),
        # JavaScript may read the theme itself instead of the tokens.
        ("javascript", "window.ANYPLOT_TOKENS", 'tokensFor(window.ANYPLOT_THEME === "dark")'),
        # A commented-out block never counts, whatever its lines start with.
        ("javascript", "const ramp", "/*\nconst old = d3.interpolateViridis;\nconst c = '#440154';\n*/\nconst ramp"),
        ("julia", "fig = Figure()", 'fig = Figure()\n#=\nheatmap!(ax, z, colormap = :viridis, color = "#306998")\n=#'),
        # Comments never count, with or without a space after the marker.
        ("python", "fig, ax = plt.subplots()", 'fig, ax = plt.subplots()\n# old: cmap="viridis", color="#306998"'),
        ("python", 'color="#009E73")', 'color="#009E73")  # was #306998'),
        ("python", 'color="#009E73")', 'color="#009E73")  #was "#3A3A36" and cmap="jet"'),
        ("r", 'colour = "#009E73") +', 'colour = "#009E73") + #was "#306998"'),
        ("julia", 'color = "#009E73")', 'color = "#009E73") #was colormap = :viridis'),
        ("javascript", "const ramp", "// const old = d3.interpolateViridis;\nconst ramp"),
        ("javascript", '"#4467A3");', '"#4467A3"); //was "#440154"'),
        # The Imprint colormaps are built from stops, by any name; every style-guide colour is allowed.
        ("python", 'color="#009E73"', 'c=[1, 2], cmap=LinearSegmentedColormap.from_list("imprint_seq", stops)'),
        ("python", 'color="#009E73"', 'color="#ddcc77", edgecolor="#FAF8F1", mfc="#6b6a63"'),
        # The stops of the per-theme continuous ramps are style-guide colours too.
        ("python", 'color="#009E73"', 'c=[1, 2], cmap=from_list("s", ["#66E2B2", "#024582", "#351E45", "#404C02"])'),
        ("r", 'colour = "#009E73"', 'colour = "#6F7E20"'),
        ("r", 'colour = "#009E73"', 'colour = "#686762"'),
        # An eight-digit hex is a palette colour with alpha, not a custom six-digit one.
        ("python", 'color="#009E73"', 'color="#009E7380"'),
    ],
)
def test_compliant_variants_stay_clean(language, old, new):
    source = CLEAN[language][0]
    assert old in source
    assert _check(language, source.replace(old, new)) == []


def test_the_header_never_satisfies_or_breaks_a_rule():
    """The header names the spec id, so the title rule looks for it in the code only."""
    no_spec_in_code = PYTHON.replace('"scatter-basic · python', '"Basic Scatter · python')
    assert "scatter-basic: Basic Scatter Plot" in no_spec_in_code
    assert _check("python", no_spec_in_code) == ["title"]
    assert _check("python", "# ruff: noqa: F403\n" + no_spec_in_code) == ["title"]  # a comment before the docstring
    legacy_in_header = PYTHON.replace("Quality: pending", "Quality: pending (was #306998)")
    assert _check("python", legacy_in_header) == []


@pytest.mark.parametrize(
    ("language", "source", "first_code_line"),
    [
        ("python", PYTHON, "import os"),
        ("python", "import os\n", "import os"),
        ("python", "'''doc'''\nx = 1\n", "x = 1"),
        ("python", "#!/usr/bin/env python\n# ruff: noqa\n\n" + PYTHON, "import os"),
        ("r", R, "library(ggplot2)"),
        ("julia", JULIA, "using CairoMakie"),
        ("javascript", JAVASCRIPT, "const t = window.ANYPLOT_TOKENS;"),
        ("javascript", "/* anyplot.ai\n * scatter-basic\n */\nconst t = 1;\n", "const t = 1;"),
        ("javascript", "const t = window.ANYPLOT_TOKENS;\n", "const t = window.ANYPLOT_TOKENS;"),
    ],
)
def test_strip_header_stops_at_the_first_line_of_code(language, source, first_code_line):
    assert strip_header(language, source).strip().split("\n")[0] == first_code_line


def test_an_unterminated_docstring_leaves_no_code():
    assert strip_header("python", '""" anyplot.ai\nno end') == ""


@pytest.mark.parametrize(
    ("language", "code", "expected"),
    [
        ("python", 'x = "#009E73"  # green\n# whole line\ny = 1\n', 'x = "#009E73"  \ny = 1'),
        ("python", 'x = "a # b"  #c\n', 'x = "a # b"  '),
        ("python", 'x = (\n    "open', 'x = (\n    "open'),  # does not tokenize: the scanner still runs
        # Only the tokens know that a line inside a triple-quoted string is no comment.
        ("python", 'note = """a\n# not a comment\n"""\ny = 1  # one\n', 'note = """a\n# not a comment\n"""\ny = 1  '),
        ("r", "x <- '#AE3030' # red\n#' doc\n", "x <- '#AE3030' "),
        ("julia", 'x = "#4467A3" #blue\ny = a\' #transpose\n', 'x = "#4467A3" \ny = a\' '),
        ("javascript", 'const u = "https://x"; // link\n/* block\n * more\n */\nconst v = `a // b`;\n', None),
        # A block comment goes whole, whatever its lines start with, and an inline one leaves its line.
        (
            "javascript",
            "const a = 1;\n/*\nconst cmap = d3.interpolateViridis;\n*/\nconst b = 2;\n",
            "const a = 1;\nconst b = 2;",
        ),
        ("javascript", "const a = /* was 3 */ 1;\n", "const a =  1;"),
        ("javascript", 'const accept = "image/*"; const t = 1; // "*/"\n', 'const accept = "image/*"; const t = 1; '),
        ("javascript", "const s = `line // one\n/* two */`; // gone\n", "const s = `line // one\n/* two */`; "),
        ("julia", 'a = 1\n#=\ncolormap = :viridis\n=#\nb = "#= no =#"\n', 'a = 1\nb = "#= no =#"'),
        ("julia", "a = 1 #= inline =# + 2\n", "a = 1  + 2"),
    ],
)
def test_strip_comments_keeps_markers_inside_strings(language, code, expected):
    stripped = strip_comments(language, code)
    if expected is None:
        assert stripped == 'const u = "https://x"; \nconst v = `a // b`;'
    else:
        assert stripped == expected


# --- the palette -----------------------------------------------------------------------------------


def test_the_palette_set_is_core_palette_and_inside_the_style_guide():
    """One list in three places: core/palette.py, the style guide, and this stdlib-only copy."""
    core_colours = {
        *palette.IMPRINT,
        palette.AMBER,
        *palette.RAMP_STOPS,
        palette.neutral_for("light"),
        palette.neutral_for("dark"),
        palette.muted_for("light"),
        palette.muted_for("dark"),
    }
    assert {colour.upper() for colour in core_colours} <= PALETTE_HEXES
    guide = (ROOT / "prompts" / "default-style-guide.md").read_text(encoding="utf-8")
    documented = {value.upper() for value in re.findall(r"#[0-9A-Fa-f]{6}\b", guide)}
    assert PALETTE_HEXES <= documented
    # The style guide names pure black and white only to forbid them.
    assert documented - PALETTE_HEXES == {"#000000", "#FFFFFF"}


def test_the_palette_rule_lists_what_it_found():
    source = PYTHON.replace('color="#009E73"', 'color="#3a3a36", edgecolor="#888888", mfc="#3A3A36"')
    found, details = check(source, spec_id=SPEC, language="python", library="matplotlib")
    assert found == ["palette"]
    assert details == {"palette": ["#3A3A36", "#888888"]}  # upper case, once each, in order of appearance
    many = PYTHON.replace('color="#009E73"', "colors=[" + ", ".join(f'"#0000{i:02X}"' for i in range(1, 12)) + "]")
    assert len(check(many, spec_id=SPEC, language="python", library="matplotlib")[1]["palette"]) == 8


# --- the record ----------------------------------------------------------------------------------

LEGACY = PYTHON.replace("scatter-basic · python · matplotlib", "scatter-basic · matplotlib").replace(
    'color="#009E73"', 'c=[1, 2], cmap="viridis"'
)


def _record(new: str | None, prev: str | None) -> dict:
    return build_record(new, prev, spec_id=SPEC, language="python", library="matplotlib")


def test_a_first_generation_has_no_predecessor_side():
    record = _record(LEGACY, None)
    assert record["status"] == "violations"
    assert record["violations"] == record["new_only"] == ["title", "colormap"]
    assert record["prev_violations"] is None and record["details"] == {}
    assert summary_line(record) == "**Contract check (record-only):** title, colormap"
    assert notice_line(record) == (
        "::notice::contract_check library=matplotlib status=violations violations=title,colormap prev=n/a "
        "new_only=title,colormap"
    )


def test_a_regeneration_separates_what_only_the_new_file_breaks():
    only_title = PYTHON.replace("scatter-basic · python · matplotlib", "scatter-basic · matplotlib")
    record = _record(LEGACY, only_title)
    assert record["violations"] == ["title", "colormap"]
    assert record["prev_violations"] == ["title"]
    assert record["new_only"] == ["colormap"]
    assert summary_line(record) == "**Contract check (record-only):** title, colormap (new in this version: colormap)"
    inherited = _record(only_title, LEGACY)
    assert inherited["new_only"] == []
    assert summary_line(inherited) == "**Contract check (record-only):** title (new in this version: none)"
    assert "prev=title,colormap new_only=none" in notice_line(inherited)


def test_a_palette_violation_carries_its_hexes():
    record = _record(PYTHON.replace('"#009E73"', '"#F0D9B5"'), PYTHON)
    assert record["violations"] == record["new_only"] == ["palette"]
    assert record["details"] == {"palette": ["#F0D9B5"]}
    assert summary_line(record) == (
        "**Contract check (record-only):** palette (new in this version: palette); outside the palette: `#F0D9B5`"
    )
    assert notice_line(record).endswith("prev=none new_only=palette palette_hexes=#F0D9B5")


def test_a_clean_file_and_a_missing_one():
    clean = _record(PYTHON, LEGACY)
    assert (clean["status"], clean["violations"], clean["new_only"]) == ("clean", [], [])
    assert summary_line(clean) == "**Contract check (record-only):** clean"
    assert "status=clean violations=none prev=title,colormap new_only=none" in notice_line(clean)
    missing = _record(None, PYTHON)
    assert (missing["status"], missing["violations"], missing["prev_violations"]) == ("unreadable", [], None)
    assert summary_line(missing).startswith("**Contract check (record-only):** unreadable")


# --- the command ---------------------------------------------------------------------------------


def _run(tmp_path: Path, script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(script),
            "check",
            "--spec-id",
            SPEC,
            "--language",
            "python",
            "--library",
            "matplotlib",
            *args,
        ],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env={"PATH": "/usr/bin:/bin", "GITHUB_STEP_SUMMARY": str(tmp_path / "summary")},
    )


def test_check_records_and_never_fails(tmp_path):
    """Run as impl-review runs it: a lone copy outside the repository, with no package around it."""
    script = tmp_path / "regen-tools" / "contract_check.py"
    script.parent.mkdir()
    shutil.copy(SCRIPT, script)
    (tmp_path / "new.py").write_text(LEGACY, encoding="utf-8")
    (tmp_path / "prev.py").write_text(PYTHON, encoding="utf-8")
    result = _run(tmp_path, script, "--source", "new.py", "--prev", "prev.py", "--out", "record.json")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == (
        "::notice::contract_check library=matplotlib status=violations violations=title,colormap prev=none "
        "new_only=title,colormap"
    )
    assert (tmp_path / "summary").read_text(encoding="utf-8") == (
        "**Contract check (record-only):** title, colormap (new in this version: title, colormap)\n"
    )
    record = json.loads((tmp_path / "record.json").read_text(encoding="utf-8"))
    assert record["version"] == 2 and record["new_only"] == ["title", "colormap"]


@pytest.mark.parametrize("content", [None, b"\xff\xfe not utf-8"], ids=["missing", "not-utf-8"])
def test_an_unreadable_source_is_recorded_not_raised(tmp_path, content):
    if content is not None:
        (tmp_path / "new.py").write_bytes(content)
    result = _run(tmp_path, SCRIPT, "--source", "new.py", "--prev", "prev.py")
    assert result.returncode == 0, result.stderr
    assert "status=unreadable" in result.stdout


# --- the library mandates ------------------------------------------------------------------------
# Excerpts of real files, pasted at the commit named beside each. A constant's comment says whether
# the file breaks the rule (true positive) or keeps it in one of its spellings (true negative).

# bokeh sn-curve-basic, 564fcdf54 (#14313): the screenshot without a page colour. Its dark render
# shows the light line rgb(197, 197, 196) along the top and left edge.
BOKEH_SAVE_UNPAINTED = """
driver = webdriver.Chrome(options=opts)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
"""
# bokeh contour-map-geographic, 7513611e6 (#14356): the prompt's own spelling.
BOKEH_SAVE_PAINTED = """
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_script(
    "document.documentElement.style.background = arguments[0]; document.body.style.background = arguments[0];", PAGE_BG
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
"""
# bokeh dashboard-metrics-tiles, 55fcfa1e3 (#14470): the body alone, as backgroundColor. Its render is clean.
BOKEH_SAVE_BODY = """
driver = webdriver.Chrome(options=opts)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)
driver.execute_script(
    f"document.body.style.margin='0'; document.body.style.padding='0';document.body.style.backgroundColor='{PAGE_BG}';"
)
driver.save_screenshot(f"plot-{THEME}.png")
"""
# bokeh barcode-ean13, 23ba3b6c0 (#14454): CSS written into the saved HTML. Its render is clean.
BOKEH_SAVE_CSS = """
html_content = file_html(p, INLINE)
html_content = html_content.replace("<body>", f'<body style="background-color:{PAGE_BG};margin:0;padding:0;">', 1)
html_content = html_content.replace(
    "</head>",
    (
        f"<style>"
        f"html{{background-color:{PAGE_BG}!important;margin:0!important;padding:0!important;}}"
        f"</style></head>"
    ),
    1,
)
driver = webdriver.Chrome(options=opts)
"""
# bokeh contour-map-geographic, 7513611e6 (#14356): the toolbar off as a keyword.
BOKEH_FIGURE = """
p = figure(
    width=W,
    height=H,
    title="contour-map-geographic · python · bokeh · anyplot.ai",
    toolbar_location=None,
    tools="pan,wheel_zoom,reset",
)
"""
# bokeh line-markers, b0ea31e41 (#13453): the figure keeps its toolbar.
BOKEH_FIGURE_TOOLBAR = """
p = figure(
    width=4800,
    height=2700,
    title="line-markers · bokeh · anyplot.ai",
    x_axis_label="Month",
    y_axis_label="Temperature (°C)",
)
"""
# bokeh timeseries-decomposition, b4924a6a5 (#13729): the toolbar off as a key of a keyword dict.
BOKEH_FIGURE_DICT = """
kwargs = {
    "width": width,
    "height": height,
    "x_axis_type": "datetime",
    "title": title_text,
    "toolbar_location": None,
}
p = figure(**kwargs)
"""

# pygal maze-circular, e0a7f5e3b (#14278): two tick sizes, and no guide lines drawn.
PYGAL_56_44_NO_GUIDES = """
custom_style = Style(
    background=PAGE_BG,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
)
chart = pygal.XY(
    style=custom_style,
    show_x_guides=False,
    show_y_guides=False,
)
"""
# pygal barcode-ean13, 161dfc0dd (#14456): equal sizes at a value of its own, both guide colours.
PYGAL_84_84 = """
custom_style = Style(
    title_font_size=66,
    label_font_size=84,
    major_label_font_size=84,
    legend_font_size=44,
    guide_stroke_color=PAGE_BG,
    major_guide_stroke_color=PAGE_BG,
)
chart = pygal.StackedBar(style=custom_style)
"""
# pygal audiogram-clinical, be1db4a91 (#12838): value_label_font_size through a name is not a tick size.
PYGAL_VALUE_LABEL = """
LABEL_FS = 40
custom_style = Style(
    label_font_size=44,
    major_label_font_size=44,
    value_label_font_size=LABEL_FS,
)
chart = pygal.XY(style=custom_style, show_x_guides=False, show_y_guides=False)
"""
# pygal line-stock-comparison, 75b6947db (#14522): y guides drawn in pygal's black.
PYGAL_BLACK_GUIDES = """
custom_style = Style(
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
)
chart = pygal.Line(
    style=custom_style,
    show_x_guides=False,
    show_y_guides=True,
)
"""
# pygal map-connection-lines, ed97feb86 (#14646): one guide colour of the two.
PYGAL_ONE_GUIDE = """
custom_style = Style(
    label_font_size=44,
    major_label_font_size=44,
    guide_stroke_color=GRID_COLOR,
    guide_stroke_dasharray="2,6",
)
chart = pygal.XY(style=custom_style, show_x_guides=True, show_y_guides=True)
"""
# pygal donut-basic, a06623ee4 (#9457), and choropleth-basic, 89a1c5c1d: chart types without guide lines.
PYGAL_PIE = """
custom_style = Style(label_font_size=44, major_label_font_size=44)
chart = pygal.Pie(style=custom_style, inner_radius=0.45)
"""
PYGAL_WORLD = """
from pygal_maps_world.maps import World
custom_style = Style(label_font_size=44, major_label_font_size=44)
worldmap = World(style=custom_style)
"""

# altair arc-basic, 54f96fd46 (#8042): a single chart sized as its view only.
ALTAIR_NO_FIT = """
chart = (
    alt.layer(arcs, nodes)
    .properties(
        width=620,
        height=320,
        padding={"left": 10, "right": 10, "top": 10, "bottom": 30},
    )
)
"""
# altair area-basic, bd2b3573d (#14682): the prompt's spelling.
ALTAIR_FIT = """
chart = (
    alt.Chart(df)
    .mark_area()
    .properties(
        width=800,
        height=450,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        padding=10,
    )
)
"""
# altair dashboard-metrics-tiles, 0134d8070 (#14471): a compound chart, which cannot fit.
ALTAIR_COMPOUND = """
tile = alt.vconcat(sparkline, change_row, spacing=4).properties(title=name)
rows = [alt.hconcat(*tiles[i : i + GRID_COLUMNS], spacing=18) for i in range(0, len(tiles), GRID_COLUMNS)]
chart = alt.vconcat(*rows, spacing=18).properties(padding=10)
"""

# plotly area-basic, 54ba9e761 (#14678): autosize off, as the prompt asks. No file in the catalogue turns
# it on; the true positive is this excerpt with the one value flipped.
PLOTLY_LAYOUT = """
fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
)
"""

# lets-plot contour-map-geographic, bb137dc09 (#14367): a fixed aspect without the wrap. Its dark render
# is 26.7 % transparent, in bands at the left and right.
LETSPLOT_UNWRAPPED = """
plot = (
    ggplot(df)
    + ggsize(800, 450)
    + coord_fixed(ratio=geo_ratio)
)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
"""
# lets-plot heatmap-geographic, 60da8d465 (#14301): the fixed aspect wrapped in a one-panel grid.
LETSPLOT_WRAPPED = """
plot = ggplot(df) + coord_fixed(ratio=1.0, xlim=[lon_min, lon_max], ylim=[lat_min, lat_max])
plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))
"""

# matplotlib circlepacking-basic, 92a990eb8 (#13409): the trimming save.
MATPLOTLIB_TIGHT = """
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
"""

# highcharts alluvial-basic, 2bad103f9 (#11105): the chart's switch only, no plotOptions.
HIGHCHARTS_CHART_ONLY = """
Highcharts.chart("container", {
  chart: {
    backgroundColor: "transparent",
    animation: false,
  },
  series: [{ type: "sankey", data: links }],
});
"""
# highcharts area-basic, 307fa8c72 (#10508): both switches.
HIGHCHARTS_BOTH = """
Highcharts.chart("container", {
  chart: {
    type: "area",
    backgroundColor: "transparent",
    animation: false,
  },
  legend: { enabled: false },
  plotOptions: {
    series: { animation: false },
  },
});
"""
# chartjs area-basic, 85708dfc5 (#8275); echarts area-basic, 538d0adc3 (#8277); muix area-basic,
# c75c393a7 (#12285). No file in the catalogue leaves the animation on; the true positives remove the line.
CHARTJS_OPTIONS = """
  options: {
    maintainAspectRatio: false,
    animation: false,
  },
"""
ECHARTS_OPTION = """
chart.setOption({
  animation: false,
  series: [{ type: "line", areaStyle: {} }],
});
"""
MUIX_CHART = """
      <LineChart
        width={width}
        height={height - TITLE_H}
        skipAnimation
      />
"""


def _mandates(source: str, library: str, language: str = "python") -> list[str]:
    """The library mandates ``source`` breaks: the base rules are left out, the excerpts carry no title."""
    keys = {mandate.key for mandate in MANDATES}
    return [key for key in violations(source, spec_id=SPEC, language=language, library=library) if key in keys]


@pytest.mark.parametrize(
    ("library", "source", "expected"),
    [
        ("bokeh", BOKEH_FIGURE + BOKEH_SAVE_UNPAINTED, ["bokeh-page-paint"]),
        ("bokeh", BOKEH_FIGURE + BOKEH_SAVE_PAINTED, []),
        ("bokeh", BOKEH_FIGURE + BOKEH_SAVE_BODY, []),
        ("bokeh", BOKEH_FIGURE + BOKEH_SAVE_CSS, []),
        ("bokeh", BOKEH_FIGURE_TOOLBAR + BOKEH_SAVE_PAINTED, ["bokeh-toolbar"]),
        ("bokeh", BOKEH_FIGURE_DICT + BOKEH_SAVE_PAINTED, []),
        ("bokeh", BOKEH_FIGURE_TOOLBAR + BOKEH_SAVE_UNPAINTED, ["bokeh-page-paint", "bokeh-toolbar"]),
        ("pygal", PYGAL_56_44_NO_GUIDES, ["pygal-tick-sizes"]),
        ("pygal", PYGAL_84_84, []),
        ("pygal", PYGAL_VALUE_LABEL, []),
        ("pygal", PYGAL_BLACK_GUIDES, ["pygal-grid-colour"]),
        ("pygal", PYGAL_ONE_GUIDE, ["pygal-grid-colour"]),
        ("pygal", PYGAL_PIE, []),
        ("pygal", PYGAL_WORLD, []),
        ("altair", ALTAIR_NO_FIT, ["altair-autosize"]),
        ("altair", ALTAIR_FIT, []),
        ("altair", ALTAIR_COMPOUND, []),
        ("plotly", PLOTLY_LAYOUT, []),
        ("plotly", PLOTLY_LAYOUT.replace("autosize=False", "autosize=True"), ["plotly-autosize"]),
        ("letsplot", LETSPLOT_UNWRAPPED, ["letsplot-wrap"]),
        ("letsplot", LETSPLOT_WRAPPED, []),
        ("matplotlib", MATPLOTLIB_TIGHT, ["bbox-tight"]),
        ("seaborn", MATPLOTLIB_TIGHT, ["bbox-tight"]),
        ("matplotlib", MATPLOTLIB_TIGHT.replace(', bbox_inches="tight"', ""), []),
        # The same text in another library's file is not that library's rule.
        ("plotnine", MATPLOTLIB_TIGHT, []),
        ("matplotlib", BOKEH_FIGURE_TOOLBAR + BOKEH_SAVE_UNPAINTED, []),
    ],
)
def test_python_mandates(library, source, expected):
    assert _mandates(source, library) == expected


@pytest.mark.parametrize(
    ("library", "source", "expected"),
    [
        ("highcharts", HIGHCHARTS_CHART_ONLY, ["animation"]),
        ("highcharts", HIGHCHARTS_BOTH, []),
        ("chartjs", CHARTJS_OPTIONS, []),
        ("chartjs", CHARTJS_OPTIONS.replace("    animation: false,\n", ""), ["animation"]),
        ("echarts", ECHARTS_OPTION, []),
        ("echarts", ECHARTS_OPTION.replace("  animation: false,\n", ""), ["animation"]),
        ("muix", MUIX_CHART, []),
        ("muix", MUIX_CHART.replace("        skipAnimation\n", ""), ["animation"]),
        ("muix", MUIX_CHART.replace("skipAnimation", "skipAnimation={false}"), ["animation"]),
        # A switch in a comment does not count.
        ("echarts", ECHARTS_OPTION.replace("  animation: false,", "  // animation: false,"), ["animation"]),
    ],
)
def test_javascript_mandates(library, source, expected):
    assert _mandates(source, library, language="javascript") == expected


def test_a_size_set_through_a_name_is_compared_by_its_value():
    """No catalogue file sets the tick sizes through names yet; a generator may, so the rule reads the names."""
    same = "TICK = 44\nTICK_MAJOR = 44\nstyle = Style(label_font_size=TICK, major_label_font_size=TICK_MAJOR)\n"
    assert _mandates(same, "pygal") == ["pygal-grid-colour"]  # no guide colours: the Style sets none
    apart = same.replace("TICK_MAJOR = 44", "TICK_MAJOR = 40")
    assert _mandates(apart, "pygal") == ["pygal-tick-sizes", "pygal-grid-colour"]
    # Two names the code never assigns a number: not judged, never flagged.
    unknown = "style = Style(label_font_size=sizes.tick, major_label_font_size=sizes.major)\n"
    assert "pygal-tick-sizes" not in _mandates(unknown, "pygal")
    # A typed constant is a constant too.
    typed = "FS_TICK: int = 44\nFS_MAJOR: int = 40\nstyle = Style(label_font_size=FS_TICK, major_label_font_size=FS_MAJOR)\n"
    assert "pygal-tick-sizes" in _mandates(typed, "pygal")
    assert "pygal-tick-sizes" not in _mandates(typed.replace("FS_MAJOR: int = 40", "FS_MAJOR: int = 44"), "pygal")


# The forms below occur in no catalogue file yet; each is written the way a generator could write it,
# from the excerpts above.


def test_pygal_reads_chart_types_and_style_keys_in_every_import_and_call_form():
    """A guideless chart imported by name, the module under an alias, and the style passed as a dict."""
    pie_by_name = "from pygal import Pie\n" + PYGAL_PIE.replace("pygal.Pie(", "Pie(")
    assert _mandates(pie_by_name, "pygal") == []
    pie_aliased = "from pygal import Pie as Donut\n" + PYGAL_PIE.replace("pygal.Pie(", "Donut(")
    assert _mandates(pie_aliased, "pygal") == []
    module_alias = "import pygal as pg\n" + PYGAL_PIE.replace("pygal.Pie(", "pg.Pie(")
    assert _mandates(module_alias, "pygal") == []
    # A chart with guides, imported by name, still needs both colours.
    line_by_name = "from pygal import Line, Pie\n" + PYGAL_BLACK_GUIDES.replace("pygal.Line(", "Line(")
    assert _mandates(line_by_name, "pygal") == ["pygal-grid-colour"]
    # The style as a dict of keywords (`Style(**STYLE)`): its string keys count like keywords.
    as_dict = """
STYLE = {
    "label_font_size": 44,
    "major_label_font_size": 44,
    "guide_stroke_color": INK_MUTED,
    "major_guide_stroke_color": INK_MUTED,
}
chart = pygal.Line(style=Style(**STYLE), show_y_guides=True)
"""
    assert _mandates(as_dict, "pygal") == []
    assert _mandates(as_dict.replace('"major_label_font_size": 44', '"major_label_font_size": 56'), "pygal") == [
        "pygal-tick-sizes"
    ]
    assert _mandates(as_dict.replace('    "major_guide_stroke_color": INK_MUTED,\n', ""), "pygal") == [
        "pygal-grid-colour"
    ]


def test_altair_fit_in_its_positional_form_and_compound_charts_by_composition():
    positional = ALTAIR_FIT.replace('alt.AutoSizeParams(type="fit"', 'alt.AutoSizeParams("fit"')
    assert _mandates(positional, "altair") == []
    # A pandas mask, a string and a selection union are no composition: an unfitted single chart is judged.
    masked = 'peaks = df[(df["elevation"] > 0) & (df["distance"] < 40)]\n' + ALTAIR_NO_FIT
    assert _mandates(masked, "altair") == ["altair-autosize"]
    titled = ALTAIR_NO_FIT.replace("width=620,", 'width=620,\n        title="Home & Garden | 2026",')
    assert _mandates(titled, "altair") == ["altair-autosize"]
    selection = "opacity = alt.condition(highlight | click, alt.value(1.0), alt.value(0.4))\n" + ALTAIR_NO_FIT
    assert _mandates(selection, "altair") == ["altair-autosize"]
    # A layer fits like a single chart, so it is judged too.
    layered = "base = alt.Chart(df)\nbars = base.mark_bar()\ntext = base.mark_text()\nchart = (bars + text).properties(width=800)\n"
    assert _mandates(layered, "altair") == ["altair-autosize"]
    # Composition with the chart operators, also of charts derived from one base, is compound and exempt.
    for compose in ("chart = bars | text\n", "chart = (bars & text)\n", "chart = bars\nchart |= text\n"):
        assert (
            _mandates("base = alt.Chart(df)\nbars = base.mark_bar()\ntext = base.mark_text()\n" + compose, "altair")
            == []
        )
    inline = "chart = alt.Chart(df).mark_bar() | alt.Chart(df).mark_line()\n"
    assert _mandates(inline, "altair") == []
    channel = 'chart = alt.Chart(df).mark_bar().encode(x=X, y=Y, column="region:N").properties(width=200)\n'
    assert _mandates(channel, "altair") == []


def test_named_animation_switches_count_where_they_are_used():
    """A switch held in a named object counts once per use; a value the file does not resolve is not judged."""
    shared = """
const NO_ANIMATION = { animation: false };
Highcharts.chart("container", {
  chart: { backgroundColor: "transparent", ...NO_ANIMATION },
  plotOptions: { series: NO_ANIMATION },
});
"""
    assert _mandates(shared, "highcharts", language="javascript") == []
    once = shared.replace("  plotOptions: { series: NO_ANIMATION },\n", "")
    assert _mandates(once, "highcharts", language="javascript") == ["animation"]
    by_name = HIGHCHARTS_BOTH.replace(
        'Highcharts.chart("container", {', 'const ANIMATE = false;\nHighcharts.chart("container", {'
    )
    by_name = by_name.replace("animation: false", "animation: ANIMATE")
    assert _mandates(by_name, "highcharts", language="javascript") == []
    unresolved = HIGHCHARTS_BOTH.replace("series: { animation: false }", "series: { animation: options.animate }")
    assert _mandates(unresolved, "highcharts", language="javascript") == []
    assert _mandates(
        CHARTJS_OPTIONS.replace("animation: false", "animation: true"), "chartjs", language="javascript"
    ) == ["animation"]
    assert _mandates(
        MUIX_CHART.replace("skipAnimation", "{...{ skipAnimation: false }}"), "muix", language="javascript"
    ) == ["animation"]


def test_code_patterns_skip_string_literals():
    """A pattern that looks for code never matches the text of a string: a title can name `coord_fixed(`."""
    titled = 'plot = ggplot(df) + geom_point() + labs(title="Why coord_fixed( matters · python · letsplot")\n'
    assert _mandates(titled, "letsplot") == []
    hidden = LETSPLOT_UNWRAPPED.replace(
        "+ ggsize(800, 450)", '+ labs(caption="no gggrid( here")\n    + ggsize(800, 450)'
    )
    assert _mandates(hidden, "letsplot") == ["letsplot-wrap"]
    # In an f-string too, fields included.
    assert _mandates('note = f"coord_fixed({RATIO}) keeps the aspect"\n', "letsplot") == []
    # The patterns that read a value inside a string still see it.
    assert _mandates(MATPLOTLIB_TIGHT, "matplotlib") == ["bbox-tight"]
    assert _mandates(BOKEH_FIGURE + BOKEH_SAVE_PAINTED, "bokeh") == []


def test_javascript_switches_in_strings_are_text():
    """A JavaScript string or template literal that spells a switch is no switch; its `${}` fields are code."""
    note = CHARTJS_OPTIONS.replace("    animation: false,\n", "") + 'const note = "animation: false";\n'
    assert _mandates(note, "chartjs", language="javascript") == ["animation"]
    single = note.replace('"animation: false"', "'animation: false'")
    assert _mandates(single, "chartjs", language="javascript") == ["animation"]
    escaped = note.replace('"animation: false"', '"say \\"animation: false\\" here"')
    assert _mandates(escaped, "chartjs", language="javascript") == ["animation"]
    template = note.replace('"animation: false"', "`${t.ink} animation: false`")
    assert _mandates(template, "chartjs", language="javascript") == ["animation"]
    # Code inside a template field stays code, and a key in quotes stays a key.
    field = ECHARTS_OPTION.replace("  animation: false,\n", "  name: `${JSON.stringify({ animation: false })}`,\n")
    assert _mandates(field, "echarts", language="javascript") == []
    quoted_key = ECHARTS_OPTION.replace("  animation: false,", '  "animation": false,')
    assert _mandates(quoted_key, "echarts", language="javascript") == []
    # Highcharts needs both switches: one of them in a string leaves one.
    in_string = HIGHCHARTS_BOTH.replace("series: { animation: false }", 'series: { name: "animation: false" }')
    assert _mandates(in_string, "highcharts", language="javascript") == ["animation"]
    # MUI X: the prop in a hint string is no prop; an apostrophe in JSX text closes at the end of its line.
    hint = MUIX_CHART.replace("        skipAnimation\n", "") + 'const hint = "pass skipAnimation";\n'
    assert _mandates(hint, "muix", language="javascript") == ["animation"]
    jsx_text = "<Typography>Users' share</Typography>\n" + MUIX_CHART
    assert _mandates(jsx_text, "muix", language="javascript") == []


def test_the_letsplot_wrapper_must_hold_the_fixed_aspect_plot_and_paint_the_page():
    """The wrap the prompt asks for: a gggrid or ggbunch that holds the plot and carries the page colour."""
    # The real wrap of heatmap-geographic (#14301), and the wrap painted in a later statement, as
    # line-parametric does it.
    assert _mandates(LETSPLOT_WRAPPED, "letsplot") == []
    later = LETSPLOT_WRAPPED.replace(
        "plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))",
        "grid = gggrid([plot])\nfinal = grid + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG))",
    )
    assert _mandates(later, "letsplot") == []
    named = "PAGE = theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))\n" + LETSPLOT_WRAPPED.replace(
        "+ theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))", "+ PAGE"
    )
    assert _mandates(named, "letsplot") == []
    through_list = """
map_plot = ggplot(df) + coord_fixed(ratio=1.0)
key_plot = ggplot(df) + geom_tile()
panels = [map_plot, key_plot]
plot = gggrid(panels, ncol=2) + ggsize(800, 450) + theme(plot_background=element_rect(fill=PAGE_BG))
"""
    assert _mandates(through_list, "letsplot") == []
    inline = (
        "plot = ggplot(df) + coord_fixed()\nggsave(gggrid([plot]) + theme(plot_background=element_rect(fill=BG)), f)\n"
    )
    assert _mandates(inline, "letsplot") == []
    # A wrapper that holds another panel, a wrapper without the page colour, and the page colour
    # only on the panel inside the wrapper all leave the strips transparent.
    other_panel = through_list.replace("panels = [map_plot, key_plot]", "panels = [key_plot]")
    assert _mandates(other_panel, "letsplot") == ["letsplot-wrap"]
    unpainted = LETSPLOT_WRAPPED.replace(" + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))", "")
    assert _mandates(unpainted, "letsplot") == ["letsplot-wrap"]
    inside = unpainted.replace("gggrid([plot])", "gggrid([plot + theme(plot_background=element_rect(fill=PAGE_BG))])")
    assert _mandates(inside, "letsplot") == ["letsplot-wrap"]
    # A theme painted before the wrap belongs to the panel, not to the wrapper.
    before = LETSPLOT_WRAPPED.replace(
        "plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))",
        "plot = plot + theme(plot_background=element_rect(fill=PAGE_BG))\nplot = gggrid([plot]) + ggsize(600, 600)",
    )
    assert _mandates(before, "letsplot") == ["letsplot-wrap"]


def test_every_rule_has_its_reason_and_the_prompt_still_says_it():
    """Each rule names what it found and quotes its prompt; the quote must still stand in that file."""
    keys = [mandate.key for mandate in MANDATES]
    assert set(BASE_REASONS) | set(keys) == set(RULES)
    # The mandates come after the base rules and keep RULES order, so a record lists them in that order.
    assert sorted(set(keys), key=RULES.index) == list(dict.fromkeys(keys))
    assert ADVISORY == {"palette"}
    for mandate in MANDATES:
        what, path, quote = reason(mandate.key, mandate.library)
        assert path == f"prompts/library/{mandate.library}.md"
        assert quote in (ROOT / path).read_text(encoding="utf-8"), (mandate.key, mandate.library)
    for key, (_found, path, quote) in BASE_REASONS.items():
        assert quote in (ROOT / path).read_text(encoding="utf-8"), key


def test_a_regeneration_records_the_mandates_its_predecessor_also_broke():
    """A legacy file without the page paint keeps it out of `new_only`; a fresh omission is in it."""
    painted = PYTHON.replace("fig.savefig(f", "driver = webdriver.Chrome()\n" + BOKEH_SAVE_PAINTED + "fig.savefig(f")
    painted = painted.replace("· matplotlib ·", "· bokeh ·").replace(
        "fig, ax", "p = figure(toolbar_location=None)\nfig, ax"
    )
    unpainted = painted.replace(BOKEH_SAVE_PAINTED, BOKEH_SAVE_UNPAINTED)
    kwargs = {"spec_id": SPEC, "language": "python", "library": "bokeh"}
    assert build_record(unpainted, unpainted, **kwargs)["new_only"] == []
    record = build_record(unpainted, painted, **kwargs)
    assert record["violations"] == record["new_only"] == ["bokeh-page-paint"]


# --- the generator's self-check ------------------------------------------------------------------


def test_the_selfcheck_names_what_to_fix_and_keeps_the_palette_advisory():
    source = PYTHON.replace("· matplotlib ·", "· seaborn ·").replace("dpi=200)", 'dpi=200, bbox_inches="tight")')
    source = source.replace('color="#009E73"', 'color="#FFFFFF"')
    lines, code = selfcheck_lines(source, spec_id=SPEC, language="python", library="seaborn")
    assert code == 1
    assert lines[-1] == "contract: fix (bbox-tight)"
    assert lines[0].startswith("palette (advisory): #FFFFFF: these colours are outside the style guide's palette")
    assert lines[1] == (
        'bbox-tight: the figure is saved with `bbox_inches="tight"`, which trims the canvas → '
        'prompts/library/seaborn.md: “**Do not use `bbox_inches="tight"` on `savefig`.**”'
    )
    only_palette, code = selfcheck_lines(
        source.replace(', bbox_inches="tight"', ""), spec_id=SPEC, language="python", library="seaborn"
    )
    assert (code, only_palette[-1]) == (0, "contract: pass (advisory: palette)")
    clean, code = selfcheck_lines(PYTHON, spec_id=SPEC, language="python", library="matplotlib")
    assert (code, clean) == (0, ["contract: pass"])
    missing, code = selfcheck_lines(None, spec_id=SPEC, language="python", library="matplotlib")
    assert code == 2 and missing[-1].startswith("contract: not run")


def test_the_selfcheck_makes_a_retired_ramp_stop_a_fix_beside_the_palette_line():
    """The advisory palette line alone let a regeneration keep its predecessor's ramp."""
    source = PYTHON.replace('color="#009E73"', 'color="#002850"')
    lines, code = selfcheck_lines(source, spec_id=SPEC, language="python", library="matplotlib")
    assert (code, lines[-1]) == (1, "contract: fix (retired-ramp)")
    assert lines[0].startswith("retired-ramp: a stop of a continuous ramp the style guide has replaced")
    assert lines[1].startswith("palette (advisory): #002850: ")


def test_no_retired_ramp_stop_is_a_colour_of_the_style_guide():
    retired = {f"#{stop}".upper() for stop in RETIRED_RAMP_STOPS}
    assert not retired & PALETTE_HEXES
    assert not retired & {stop.upper() for stop in palette.RAMP_STOPS}


def test_the_selfcheck_command_prints_plain_lines_and_writes_no_summary(tmp_path):
    """The generator runs it inside its session: no workflow command, no job summary, exit 0/1/2."""
    (tmp_path / "good.py").write_text(PYTHON, encoding="utf-8")
    (tmp_path / "bad.py").write_text(PYTHON.replace('f"plot-{THEME}.png"', '"plot.png"'), encoding="utf-8")
    env = {"PATH": "/usr/bin:/bin", "GITHUB_STEP_SUMMARY": str(tmp_path / "summary")}
    common = ["--spec-id", SPEC, "--language", "python", "--library", "matplotlib"]
    runs = {
        name: subprocess.run(
            [sys.executable, "-I", str(SCRIPT), "selfcheck", name, *common],
            capture_output=True,
            text=True,
            cwd=tmp_path,
            env=env,
        )
        for name in ("good.py", "bad.py", "missing.py")
    }
    assert (runs["good.py"].returncode, runs["good.py"].stdout) == (0, "contract: pass\n")
    assert runs["bad.py"].returncode == 1
    assert runs["bad.py"].stdout.splitlines()[-1] == "contract: fix (save)"
    assert runs["missing.py"].returncode == 2
    assert not any("::" in run.stdout for run in runs.values())
    assert not (tmp_path / "summary").exists()
