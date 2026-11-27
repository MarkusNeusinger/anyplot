"""anyplot.ai
violin-basic: Basic Violin Plot
Library: pygal 3.1.3 | Python 3.14.10
Quality: pending | Updated: 2026-11-27
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style
from scipy.stats import gaussian_kde


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
# Warm white median line, high contrast against the darker IQR boxes in both themes
MEDIAN_COLOR = "#FAF8F1"


def darken(hex_color, factor=0.68):
    """Darker shade of an Imprint color, used for the IQR box inside its violin."""
    return "#" + "".join(f"{round(int(hex_color[i : i + 2], 16) * factor):02X}" for i in (1, 3, 5))


# Constants
HALF_WIDTH = 0.38  # half-width of the widest point of every violin, in x units
BOX_WIDTH = 0.16  # half-width of the IQR box
MEDIAN_THICKNESS = 0.012  # median bar thickness as a share of the value-axis span
N_POINTS = 100  # density grid resolution
TAIL_BANDWIDTHS = 2.5  # the density grid runs this many bandwidths past each group's data range

# Columns: set these to your table's column names
CLASS_GROUP = "Class Group"  # role: category
TEST_SCORE = "Test Score (%)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
np.random.seed(42)
scores = {
    "Honors": np.clip(np.random.normal(88, 6, 200), 50, 100),
    "Standard": np.clip(60 + np.random.gamma(3.5, 4, 200), 40, 100),
    "Remedial": np.clip(np.random.normal(62, 8, 200), 30, 100),
    "Advanced": np.clip(np.concatenate([np.random.normal(75, 6, 120), np.random.normal(93, 4, 80)]), 45, 100),
}
df = pd.DataFrame(
    {
        CLASS_GROUP: [name for name, vals in scores.items() for _ in vals],
        TEST_SCORE: np.concatenate(list(scores.values())),
    }
)

# Plot: reads only df and the constants above
groups = {name: g[TEST_SCORE].dropna().to_numpy() for name, g in df.groupby(CLASS_GROUP, sort=False)}
categories = list(groups)

# One KDE per group (Silverman bandwidth) on a grid that ends where the density has fallen to near zero
densities = {}
for name, values in groups.items():
    kde = gaussian_kde(values, bw_method="silverman")
    reach = TAIL_BANDWIDTHS * kde.factor * values.std(ddof=1)
    grid = np.linspace(values.min() - reach, values.max() + reach, N_POINTS)
    dens = kde(grid)
    densities[name] = (grid, dens / dens.max())
y_min = min(grid.min() for grid, _ in densities.values())
y_max = max(grid.max() for grid, _ in densities.values())
median_half = MEDIAN_THICKNESS * (y_max - y_min) / 2

palette = []
for i in range(len(categories)):
    color = IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)]
    palette.extend([color, darken(color), MEDIAN_COLOR])

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=tuple(palette),
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    opacity=0.78,
    opacity_hover=0.92,
    stroke_opacity="0",  # fill-only shapes: the closing edges pygal adds to every filled series stay invisible
    stroke_opacity_hover="0",
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="violin-basic · python · pygal · anyplot.ai",
    x_title=CLASS_GROUP,
    y_title=TEST_SCORE,
    show_legend=False,
    stroke=True,
    fill=True,
    dots_size=0,
    show_x_guides=False,
    show_y_guides=True,
    range=(y_min, y_max),
    xrange=(0, len(categories) + 1.0),
    margin=50,
    value_formatter=lambda x: f"{x:.0f}%",
    x_value_formatter=lambda x: "",
    tooltip_border_radius=10,
    tooltip_fancy_mode=True,
    human_readable=True,
    pretty_print=True,
)

for i, (category, values) in enumerate(groups.items()):
    center_x = i + 1.0
    y_grid, density = densities[category]
    density = density * HALF_WIDTH

    median_val = float(np.median(values))
    q1 = float(np.percentile(values, 25))
    q3 = float(np.percentile(values, 75))
    tooltip = f"{category} — Median: {median_val:.1f}%, Q1: {q1:.1f}%, Q3: {q3:.1f}%"

    # Mirrored violin shape
    left_pts = [(center_x - d, y) for y, d in zip(y_grid, density, strict=True)]
    right_pts = [(center_x + d, y) for y, d in zip(y_grid[::-1], density[::-1], strict=True)]
    violin_pts = left_pts + right_pts + [left_pts[0]]
    chart.add(category, violin_pts, formatter=lambda x, t=tooltip: t)

    # IQR box and median bar are fill-only polygons: pygal closes every filled series down to the axis, and the
    # invisible strokes (Style stroke_opacity) keep those closing edges from showing
    iqr_box = [
        (center_x - BOX_WIDTH, q1),
        (center_x - BOX_WIDTH, q3),
        (center_x + BOX_WIDTH, q3),
        (center_x + BOX_WIDTH, q1),
        (center_x - BOX_WIDTH, q1),
    ]
    chart.add(None, iqr_box, stroke=True, fill=True, show_dots=False)

    median_bar = [
        (center_x - BOX_WIDTH, median_val - median_half),
        (center_x - BOX_WIDTH, median_val + median_half),
        (center_x + BOX_WIDTH, median_val + median_half),
        (center_x + BOX_WIDTH, median_val - median_half),
        (center_x - BOX_WIDTH, median_val - median_half),
    ]
    chart.add(None, median_bar, stroke=True, fill=True, show_dots=False)

chart.x_labels = ["", *categories, ""]
chart.x_labels_major_count = max(2, len(categories))  # pygal divides by count - 1

# Save
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
chart.render_to_png(f"plot-{THEME}.png")
