"""anyplot.ai
violin-basic: Basic Violin Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-29
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


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
BASE_WIDTH = 0.38  # half-width of the widest point of a unimodal violin, in x units
MULTIMODAL_SCALE = 1.2  # violins with more than one density peak are drawn wider
BOX_WIDTH = 0.16  # half-width of the IQR box
N_POINTS = 100  # density grid resolution
Y_PAD = 3.0  # value-axis padding around the data range

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
y_min = float(np.nanmin(df[TEST_SCORE])) - Y_PAD
y_max = float(np.nanmax(df[TEST_SCORE])) + Y_PAD
y_grid = np.linspace(y_min, y_max, N_POINTS)

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

    # KDE with Silverman's rule
    n = len(values)
    std = np.std(values)
    iqr_val = np.percentile(values, 75) - np.percentile(values, 25)
    bandwidth = max(0.9 * min(std, iqr_val / 1.34) * n ** (-0.2), y_grid[1] - y_grid[0])  # floor: one grid step

    density = np.exp(-0.5 * ((y_grid[:, None] - values[None, :]) / bandwidth) ** 2).sum(axis=1)
    density /= n * bandwidth * np.sqrt(2 * np.pi)
    density /= density.max()

    # Violins with several density peaks are drawn wider so the second mode reads at thumbnail scale
    is_peak = (density[1:-1] > density[:-2]) & (density[1:-1] >= density[2:]) & (density[1:-1] > 0.1)
    multimodal = int(is_peak.sum()) > 1
    density *= BASE_WIDTH * (MULTIMODAL_SCALE if multimodal else 1.0)

    median_val = float(np.median(values))
    q1 = float(np.percentile(values, 25))
    q3 = float(np.percentile(values, 75))
    tooltip = f"{category} — Median: {median_val:.1f}%, Q1: {q1:.1f}%, Q3: {q3:.1f}%"
    if multimodal:
        tooltip += " · Multimodal: more than one sub-population"

    # Mirrored violin shape
    left_pts = [(center_x - d, y) for y, d in zip(y_grid, density, strict=True)]
    right_pts = [(center_x + d, y) for y, d in zip(y_grid[::-1], density[::-1], strict=True)]
    violin_pts = left_pts + right_pts + [left_pts[0]]
    chart.add(category, violin_pts, formatter=lambda x, t=tooltip: t, stroke_style={"width": 2})

    # IQR box, filled with the darker shade from the next palette slot
    iqr_box = [
        (center_x - BOX_WIDTH, q1),
        (center_x - BOX_WIDTH, q3),
        (center_x + BOX_WIDTH, q3),
        (center_x + BOX_WIDTH, q1),
        (center_x - BOX_WIDTH, q1),
    ]
    chart.add(None, iqr_box, stroke=True, fill=True, show_dots=False, stroke_style={"width": 4, "color": INK_MUTED})

    # Median line in the third palette slot of the violin
    median_line = [(center_x - BOX_WIDTH * 1.1, median_val), (center_x + BOX_WIDTH * 1.1, median_val)]
    chart.add(None, median_line, stroke=True, fill=False, show_dots=False, stroke_style={"width": 18})

chart.x_labels = ["", *categories, ""]
chart.x_labels_major_count = max(2, len(categories))  # pygal divides by count - 1

# Save
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
chart.render_to_png(f"plot-{THEME}.png")
