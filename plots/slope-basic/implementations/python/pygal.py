""" anyplot.ai
slope-basic: Basic Slope Chart (Slopegraph)
Library: pygal 3.1.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-04-30
"""

import os
import sys


# Pop script dir so this file (pygal.py) doesn't shadow the installed pygal package
_script_dir = sys.path.pop(0)
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


sys.path.insert(0, _script_dir)

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

COLOR_INCREASE = "#009E73"  # Okabe-Ito position 1 — upward change
COLOR_DECREASE = "#D55E00"  # Okabe-Ito position 2 — downward change

# Realistic product category data — Q1 vs Q4 sales comparison
categories = [
    "Electronics",
    "Apparel",
    "Furniture",
    "Automotive",
    "Food & Bev",
    "Sporting Goods",
    "Home Decor",
    "Office Supplies",
    "Beauty",
    "Toys",
]
q1_sales = [85, 72, 95, 45, 68, 52, 78, 62, 88, 40]
q4_sales = [92, 58, 102, 75, 65, 71, 82, 48, 95, 55]

increasing = [(c, q1_sales[i], q4_sales[i]) for i, c in enumerate(categories) if q4_sales[i] >= q1_sales[i]]
decreasing = [(c, q1_sales[i], q4_sales[i]) for i, c in enumerate(categories) if q4_sales[i] < q1_sales[i]]

series_colors = tuple([COLOR_INCREASE] * len(increasing) + [COLOR_DECREASE] * len(decreasing))

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=series_colors,
    title_font_size=64,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=38,
    value_font_size=32,
    value_label_font_size=36,
    stroke_width=6,
)

# Slope chart: Line chart with only 2 x-axis time points
chart = pygal.Line(
    width=4800,
    height=2700,
    title="slope-basic · pygal · anyplot.ai",
    x_title="Time Period",
    y_title="Sales (units)",
    style=custom_style,
    show_dots=True,
    dots_size=18,
    stroke_style={"width": 6},
    show_y_guides=True,
    show_x_guides=False,
    show_legend=True,
    interpolate=None,
    margin=140,
    print_values=False,
    print_labels=True,
    range=(30, 115),
    margin_right=340,
)

chart.x_labels = ["Q1 2024", "Q4 2024"]

# Increasing categories — Okabe-Ito green
for c, start, end in increasing:
    chart.add(c, [{"value": start, "label": c}, {"value": end, "label": c}])

# Decreasing categories — Okabe-Ito vermillion
for c, start, end in decreasing:
    chart.add(c, [{"value": start, "label": c}, {"value": end, "label": c}])

# Save PNG and interactive HTML
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
