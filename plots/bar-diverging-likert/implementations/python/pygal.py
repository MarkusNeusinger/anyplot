"""anyplot.ai
bar-diverging-likert: Likert Scale Diverging Bar Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-06-01
"""

import importlib.util
import os
import re
import sys

import cairosvg
import pandas as pd


# Prevent self-import: this file is named pygal.py, so import the installed package explicitly
_spec = importlib.util.find_spec("pygal")
if _spec and _spec.origin != __file__:
    import pygal
    from pygal.style import Style
else:
    _cwd = os.getcwd()
    sys.path = [p for p in sys.path if os.path.abspath(p) != _cwd]
    try:
        import pygal
        from pygal.style import Style
    finally:
        sys.path.insert(0, _cwd)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette (canonical order); the diverging Likert scale uses the semantic red and blue anchors
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]


# Constants
def lerp_hex(c0, c1, t):
    r0, g0, b0 = (int(c0[i : i + 2], 16) for i in (1, 3, 5))
    r1, g1, b1 = (int(c1[i : i + 2], 16) for i in (1, 3, 5))
    return "#" + "".join(f"{round(a + (b - a) * t):02X}" for a, b in ((r0, r1), (g0, g1), (b0, b1)))


# Theme-invariant neutral so the intermediate blends are identical in both themes
NEUTRAL_GREY = "#6B6A63"
SD_COLOR = IMPRINT_PALETTE[4]
D_COLOR = lerp_hex(SD_COLOR, NEUTRAL_GREY, 0.35)
N_COLOR = NEUTRAL_GREY
A_COLOR = lerp_hex(NEUTRAL_GREY, IMPRINT_PALETTE[2], 0.5)
SA_COLOR = IMPRINT_PALETTE[2]


# Column constants
QUESTION = "Survey question"  # role: question
STRONGLY_DISAGREE = "Strongly Disagree"  # role: strongly_disagree
DISAGREE = "Disagree"  # role: disagree
NEUTRAL = "Neutral"  # role: neutral
AGREE = "Agree"  # role: agree
STRONGLY_AGREE = "Strongly Agree"  # role: strongly_agree


# Data: replace this block with your own table, for example df = pd.read_csv("survey.csv")
# Employee engagement survey: 8 questions, 5-point Likert scale, response percentages per question
df = pd.DataFrame(
    {
        QUESTION: [
            "I feel valued at work",
            "My manager provides clear direction",
            "I have opportunities for growth",
            "Work-life balance is supported",
            "I receive fair compensation",
            "Team collaboration is effective",
            "Company vision is inspiring",
            "My contributions are recognized",
        ],
        STRONGLY_DISAGREE: [5, 8, 12, 6, 22, 3, 18, 7],
        DISAGREE: [10, 15, 22, 12, 30, 7, 28, 14],
        NEUTRAL: [15, 20, 18, 22, 18, 10, 22, 16],
        AGREE: [40, 35, 30, 38, 20, 42, 22, 38],
        STRONGLY_AGREE: [30, 22, 18, 22, 10, 38, 10, 25],
    }
)


# Plot
# Sort ascending by net agreement (most positive renders at top in a horizontal chart)
net = df[[AGREE, STRONGLY_AGREE]].sum(axis=1) - df[[STRONGLY_DISAGREE, DISAGREE]].sum(axis=1)
df = df.loc[net.sort_values(kind="stable").index]

# Title scaled for length (long mandated title)
title = "Employee Engagement Survey · bar-diverging-likert · python · pygal · anyplot.ai"
n = len(title)
title_font_size = max(44, round(66 * 67 / n)) if n > 67 else 66

# Colors in series-addition order: N_left, D, SD, N_right, A, SA
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(N_COLOR, D_COLOR, SD_COLOR, N_COLOR, A_COLOR, SA_COLOR),
    title_font_size=title_font_size,
    label_font_size=48,
    major_label_font_size=48,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
    opacity=1,
    opacity_hover=1,
    value_colors=("#F0EFE8",) * 6,
)

chart = pygal.HorizontalStackedBar(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    show_x_guides=False,
    show_y_guides=False,
    print_values=True,
    print_values_position="center",
    value_formatter=lambda x: f"{abs(x):.0f}%" if abs(x) >= 8 else "",
    x_title="Response Percentage (%)",
    margin=50,
    spacing=15,
    truncate_label=-1,
    truncate_legend=-1,
)

# Add series in stacking order (center outward); legend shows N, D, SD, A, SA
chart.add(NEUTRAL, (-df[NEUTRAL] / 2).tolist())
chart.add(DISAGREE, (-df[DISAGREE]).tolist())
chart.add(STRONGLY_DISAGREE, (-df[STRONGLY_DISAGREE]).tolist())
chart.add(None, (df[NEUTRAL] / 2).tolist())  # right-half neutral hidden from legend
chart.add(AGREE, df[AGREE].tolist())
chart.add(STRONGLY_AGREE, df[STRONGLY_AGREE].tolist())

chart.x_labels = df[QUESTION].tolist()


# SVG post-processing: remove residual guide lines and reorder legend to SD, D, N, A, SA
svg_content = chart.render().decode("utf-8")

svg_content = re.sub(r'<path [^>]*class="(?:major )?(?:axis major )?guide line"[^/]*/>', "", svg_content)

# Re-flow the legend entries left to right as SD | D | N | A | SA, spaced by label length
char_width, swatch, gap = 27, 40, 90
cursor = 0.0
for serie, label in ((2, STRONGLY_DISAGREE), (1, DISAGREE), (0, NEUTRAL), (4, AGREE), (5, STRONGLY_AGREE)):
    entry = re.search(rf'<g id="activate-serie-{serie}".*?</g>', svg_content)
    if entry is None:
        continue
    moved = re.sub(r'(<rect x=")[\d.]+', rf"\g<1>{cursor}", entry.group(0))
    moved = re.sub(r'(<text x=")[\d.]+', rf"\g<1>{cursor + 17}", moved)
    svg_content = svg_content.replace(entry.group(0), moved)
    cursor += swatch + len(label) * char_width + gap


# Save
cairosvg.svg2png(bytestring=svg_content.encode("utf-8"), write_to=f"plot-{THEME}.png")

with open(f"plot-{THEME}.html", "w") as f:
    f.write(svg_content)
