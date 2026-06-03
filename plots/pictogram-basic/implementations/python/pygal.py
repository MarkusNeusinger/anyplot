"""anyplot.ai
pictogram-basic: Pictogram Chart (Isotype Visualization)
Library: pygal 3.1.0 | Python 3.13.13
Quality: 82/100 | Updated: 2026-06-03
"""

import os
import sys


# The script is named pygal.py — prevent it from shadowing the installed pygal package.
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _script_dir]

import pygal
from pygal.style import Style


# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — canonical order, first series always #009E73
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Data — fruit production (thousands of tonnes), descending for visual hierarchy
categories = ["Apples", "Oranges", "Bananas", "Grapes", "Mangoes"]
values = [35, 22, 18, 15, 8]
icon_unit = 5  # each dot represents 5 thousand tonnes

# Build dot matrix: 1.0 = full icon, fraction = proportional partial, None = empty
max_icons = max(v // icon_unit + (1 if v % icon_unit else 0) for v in values)
dot_data = {}
for cat, val in zip(categories, values, strict=True):
    full = val // icon_unit
    remainder = val % icon_unit
    row = [1.0] * full
    if remainder:
        row.append(remainder / icon_unit)  # proportional fraction for accurate partial
    row += [None] * (max_icons - len(row))
    dot_data[cat] = row

# Title length-aware font size (baseline: 67 chars → size 66)
title = "Fruit Production · pictogram-basic · python · pygal · anyplot.ai"
title_n = len(title)
title_fontsize = max(44, round(66 * (67 / title_n if title_n > 67 else 1.0)))

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=title_fontsize,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
    font_family="Helvetica, Arial, sans-serif",
)

chart = pygal.Dot(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    x_title="Thousands of tonnes  ·  each dot = 5k t",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    legend_box_size=28,
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=True,
    spacing=35,
    margin=50,
    margin_left=110,
    margin_right=80,
    margin_top=80,
    margin_bottom=170,
    x_label_rotation=0,
    truncate_label=-1,
    truncate_legend=-1,
    dot_size=46,
    print_values=False,
    stroke=False,
    value_formatter=lambda v: f"{int(round(v * icon_unit))}k t" if v else "",
)

# X-axis labels show cumulative scale in thousands
chart.x_labels = [f"{(i + 1) * icon_unit}k" for i in range(max_icons)]

# Add each category as a series — Imprint palette cycles in canonical order
for cat in categories:
    chart.add(cat, dot_data[cat])

# Save — theme-suffixed filenames, PNG + interactive HTML
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
