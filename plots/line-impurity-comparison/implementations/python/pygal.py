""" anyplot.ai
line-impurity-comparison: Gini Impurity vs Entropy Comparison
Library: pygal 3.1.3 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-27
"""

import os
import re

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

_font = "Helvetica, Arial, sans-serif"

# Imprint palette — first series is brand green, second is lavender
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(
        "#009E73",  # 1: Gini — Imprint green (first categorical series)
        "#C475FD",  # 2: Entropy — Imprint lavender
        INK_MUTED,  # 3: vertical guide line — muted neutral
        "#009E73",  # 4: Gini peak dot — matches Gini
        "#C475FD",  # 5: Entropy peak dot — matches Entropy
        INK,  # 6: Gini label anchor (no dot drawn)
        INK,  # 7: Entropy label anchor (no dot drawn)
    ),
    opacity="1",
    opacity_hover="1",
    stroke_opacity="1",
    stroke_opacity_hover="1",
    stroke_width=2.5,
    guide_stroke_color=INK_MUTED,
    guide_stroke_dasharray="3, 5",
    major_guide_stroke_color=INK_SOFT,
    major_guide_stroke_dasharray="0",
    title_font_size=66,
    label_font_size=48,
    major_label_font_size=48,
    value_colors=(INK,) * 7,
    value_label_colors=(INK,) * 7,
    legend_font_size=44,
    value_font_size=36,
    value_label_font_size=48,
    tooltip_font_size=32,
    font_family=_font,
    label_font_family=_font,
    major_label_font_family=_font,
    legend_font_family=_font,
    title_font_family=_font,
    value_font_family=_font,
    value_label_font_family=_font,
)

# Data: 200 points across the full [0, 1] probability range
N_POINTS = 200
p = np.linspace(0, 1, N_POINTS)
gini = 2 * p * (1 - p)
with np.errstate(divide="ignore", invalid="ignore"):
    entropy = -p * np.log2(p) - (1 - p) * np.log2(1 - p)
entropy = np.nan_to_num(entropy, nan=0.0)  # entropy is defined as 0 at p = 0 and p = 1

# Plot
chart = pygal.XY(
    width=3200,
    height=1800,
    title="line-impurity-comparison · python · pygal · anyplot.ai",
    x_title="Probability p",
    y_title="Impurity measure",
    style=custom_style,
    show_dots=False,
    fill=False,
    show_y_guides=True,
    show_x_guides=False,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
    legend_box_size=24,
    truncate_legend=-1,
    xrange=(0, 1),
    range=(0, 1.15),
    y_labels=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
    show_y_labels=True,
    x_label_rotation=0,
    margin=80,
    margin_bottom=0,
    margin_left=160,
    margin_right=80,
    margin_top=80,
    interpolate="cubic",
    print_values=False,
    print_zeroes=False,
    print_labels=True,
    x_value_formatter=lambda x: f"{x:.1f}",
    js=[],
)

# Convert to pygal XY point lists
gini_points = list(zip(p.tolist(), gini.tolist(), strict=True))
entropy_points = list(zip(p.tolist(), entropy.tolist(), strict=True))

# Series 1: Gini impurity — Imprint green, first categorical series
chart.add("Gini: 2p(1−p)", gini_points, stroke_style={"width": 5})

# Series 2: Shannon entropy (normalized to [0,1]) — Imprint lavender
chart.add("Entropy: −p log₂p − (1−p) log₂(1−p)", entropy_points, stroke_style={"width": 5})

# Peak positions come from the curves themselves
gini_peak = (p[gini.argmax()], gini.max())
entropy_peak = (p[entropy.argmax()], entropy.max())

# Series 3: Vertical guide through the shared peak position
chart.add(
    None, [(gini_peak[0], 0.0), (gini_peak[0], float(entropy.max()))], stroke_style={"width": 1.5, "dasharray": "8, 6"}
)

# Series 4: Gini peak annotation dot at (0.5, 0.5)
chart.add(None, [gini_peak], stroke_style={"width": 0}, show_dots=True, dots_size=10)

# Series 5: Entropy peak annotation dot at (0.5, 1.0)
chart.add(None, [entropy_peak], stroke_style={"width": 0}, show_dots=True, dots_size=10)

# Series 6-7: label anchors a fixed offset above each peak dot, so no curve crosses the text
LABEL_LIFT = 0.07
chart.add(
    None,
    [{"value": (gini_peak[0], gini_peak[1] + LABEL_LIFT), "label": f"Gini peak = {gini_peak[1]:.2f}"}],
    stroke_style={"width": 0},
    show_dots=True,
    dots_size=0.1,
)
chart.add(
    None,
    [{"value": (entropy_peak[0], entropy_peak[1] + LABEL_LIFT), "label": f"Entropy peak = {entropy_peak[1]:.2f}"}],
    stroke_style={"width": 0},
    show_dots=True,
    dots_size=0.1,
)


# Save: soften the default axis border lines (left/bottom frame) in the rendered SVG
svg_str = chart.render().decode("utf-8")
m = re.search(r'id="(chart-[^"]+)"', svg_str)
chart_id = f"#{m.group(1)} " if m else ""
border_css = (
    f"\n      {chart_id}.axis .line {{ stroke: {INK_MUTED} !important; stroke-opacity: 0.45 !important; }}"
    f"\n      {chart_id}.axis .major.line {{ stroke: {INK_MUTED} !important; stroke-opacity: 0.45 !important; }}"
    f"\n      {chart_id}text.value {{ fill: {INK} !important; }}"
    "\n    "
)
svg_str = svg_str.replace("</style>", border_css + "</style>", 1)
cairosvg.svg2png(
    bytestring=svg_str.encode("utf-8"), write_to=f"plot-{THEME}.png", output_width=3200, output_height=1800
)
chart.render_to_file(f"plot-{THEME}.svg")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
