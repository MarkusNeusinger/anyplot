"""automation/scripts/contract_check.py: the static contract of an implementation file, record-only.

The sources here are synthetic on purpose. The catalogue changes every night,
so a test that reads `plots/` would pin counts that a regeneration moves.
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
    PALETTE_HEXES,
    build_record,
    check,
    notice_line,
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
    assert record["version"] == 1 and record["new_only"] == ["title", "colormap"]


@pytest.mark.parametrize("content", [None, b"\xff\xfe not utf-8"], ids=["missing", "not-utf-8"])
def test_an_unreadable_source_is_recorded_not_raised(tmp_path, content):
    if content is not None:
        (tmp_path / "new.py").write_bytes(content)
    result = _run(tmp_path, SCRIPT, "--source", "new.py", "--prev", "prev.py")
    assert result.returncode == 0, result.stderr
    assert "status=unreadable" in result.stdout
