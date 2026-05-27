""" anyplot.ai
scatter-brush-zoom: Interactive Scatter Plot with Brush Selection and Zoom
Library: pygal 3.1.0 | Python 3.13.13
Quality: 83/100 | Created: 2026-05-16
"""

import os
import sys

import numpy as np


# Temporarily remove current directory from path to avoid name collision with pygal module
_cwd = sys.path[0] if sys.path[0] else "."
if _cwd in sys.path:
    sys.path.remove(_cwd)

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Restore path
sys.path.insert(0, _cwd)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Data: Generate 3 clusters for interactive selection demonstration
np.random.seed(42)

# Cluster 1 (brand green)
cluster1_x = np.random.normal(40, 8, 120)
cluster1_y = np.random.normal(50, 8, 120)
cluster1_group = ["Group A"] * 120

# Cluster 2 (vermillion)
cluster2_x = np.random.normal(70, 8, 100)
cluster2_y = np.random.normal(65, 8, 100)
cluster2_group = ["Group B"] * 100

# Cluster 3 (blue)
cluster3_x = np.random.normal(55, 10, 130)
cluster3_y = np.random.normal(35, 10, 130)
cluster3_group = ["Group C"] * 130

# Combine clusters
all_x = np.concatenate([cluster1_x, cluster2_x, cluster3_x])
all_y = np.concatenate([cluster1_y, cluster2_y, cluster3_y])
all_groups = cluster1_group + cluster2_group + cluster3_group

# Prepare data by group for separate series
group_a_data = [
    (x, y)
    for x, y, g in zip(all_x, all_y, all_groups, strict=False)
    if g == "Group A"
]
group_b_data = [
    (x, y)
    for x, y, g in zip(all_x, all_y, all_groups, strict=False)
    if g == "Group B"
]
group_c_data = [
    (x, y)
    for x, y, g in zip(all_x, all_y, all_groups, strict=False)
    if g == "Group C"
]

# Create custom style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    title_font_size=28,
    label_font_size=18,
    major_label_font_size=16,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=2,
)

# Create scatter plot with interactive features
chart = pygal.XY(
    style=custom_style,
    width=4800,
    height=2700,
    title="scatter-brush-zoom · pygal · anyplot.ai",
    x_title="X Axis",
    y_title="Y Axis",
    show_legend=True,
    show_dots=True,
    dots_size=4,
    stroke_style={"width": 2},
    explicit_size=True,
    range=(0, 100),
)

# Add series with point labels for interactivity
chart.add("Group A", group_a_data, dots_size=5, stroke=False)
chart.add("Group B", group_b_data, dots_size=5, stroke=False)
chart.add("Group C", group_c_data, dots_size=5, stroke=False)

# Save outputs
chart.render_to_png(f"plot-{THEME}.png")

with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
