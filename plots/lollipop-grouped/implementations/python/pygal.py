""" anyplot.ai
lollipop-grouped: Grouped Lollipop Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-17
"""

import os
import sys


# Prevent local filename from shadowing the pygal package by removing script dir from path
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p) != _script_dir]

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette (first series is always #009E73)
OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Data: Quarterly revenue (in millions) by product line across regions
categories = ["North", "South", "East", "West"]
series_names = ["Electronics", "Furniture", "Apparel"]
series_values = [[42, 35, 48, 31], [28, 32, 25, 38], [15, 22, 18, 26]]

# Build color list: repeating Okabe-Ito colors for each lollipop
all_colors = []
for _i, color in enumerate(OKABE_ITO[: len(series_names)]):
    all_colors.extend([color] * len(categories))

# Custom style for 4800x2700 canvas with theme-adaptive chrome
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(all_colors),
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
)

# Create XY chart for lollipop visualization
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="lollipop-grouped · Python · pygal · anyplot.ai",
    x_title="Region",
    y_title="Revenue ($ millions)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    show_y_guides=True,
    show_x_guides=False,
    dots_size=22,
    stroke_width=3,
    margin=80,
    range=(0, 55),
    xrange=(0.3, 4.7),
    show_minor_x_labels=False,
    truncate_legend=-1,
)

# Position offsets for grouped lollipops within each category
offsets = [-0.2, 0, 0.2]

# Add each lollipop as its own series (prevents connecting lines)
for series_idx, (name, values) in enumerate(zip(series_names, series_values, strict=True)):
    for cat_idx, val in enumerate(values):
        x_pos = cat_idx + 1 + offsets[series_idx]
        # Each lollipop is a separate series: stem from 0 to value
        lollipop_data = [{"value": (x_pos, 0), "node": {"r": 0}}, {"value": (x_pos, val), "node": {"r": 22}}]
        # Only first lollipop of each series shows in legend
        show_label = name if cat_idx == 0 else None
        chart.add(show_label, lollipop_data)

# Custom x-axis labels at category positions
chart.x_labels = [1, 2, 3, 4]
chart.x_labels_major = [1, 2, 3, 4]

# X-axis label mapping
label_map = {1: "North", 2: "South", 3: "East", 4: "West"}
chart.x_value_formatter = lambda x: label_map.get(int(x), "") if x == int(x) else ""

# Save as PNG and HTML with theme suffix
chart.render_to_png(f"plot-{THEME}.png")
chart.render_to_file(f"plot-{THEME}.html")
