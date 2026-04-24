""" anyplot.ai
ecdf-basic: Basic ECDF Plot
Library: pygal 3.1.0 | Python 3.14.4
Quality: 80/100 | Created: 2026-04-24
"""

import os
import sys


# Script filename shadows the installed `pygal` package when run as `python pygal.py`;
# dropping the script directory from sys.path lets the real package resolve.
sys.path.pop(0)

import numpy as np  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#8A8A82" if THEME == "light" else "#6E6D66"
BRAND = "#009E73"

# Data — 120 samples from a normal distribution
np.random.seed(42)
values = np.random.randn(120)

# ECDF: sorted values on x, cumulative proportion (k/n) on y
sorted_values = np.sort(values)
n = len(sorted_values)
ecdf_y = np.arange(1, n + 1) / n

# Step function: each observation adds a horizontal segment then a vertical jump
step_points = []
for i in range(n):
    prev_y = 0.0 if i == 0 else float(ecdf_y[i - 1])
    step_points.append((float(sorted_values[i]), prev_y))
    step_points.append((float(sorted_values[i]), float(ecdf_y[i])))
# Extend final horizontal segment to the right so the last step is visible
step_points.append((float(sorted_values[-1]) + 0.4, float(ecdf_y[-1])))

font = "DejaVu Sans, Helvetica, Arial, sans-serif"

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK_SOFT,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(BRAND,),
    font_family=font,
    title_font_family=font,
    label_font_family=font,
    major_label_font_family=font,
    legend_font_family=font,
    tooltip_font_family=font,
    title_font_size=52,
    label_font_size=40,
    major_label_font_size=36,
    legend_font_size=34,
    tooltip_font_size=28,
    value_font_size=26,
    stroke_opacity=1,
    stroke_opacity_hover=1,
)

chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="ecdf-basic · pygal · anyplot.ai",
    x_title="Value",
    y_title="Cumulative Proportion",
    show_dots=False,
    stroke_style={"width": 6},
    show_x_guides=True,
    show_y_guides=True,
    show_legend=False,
    range=(0, 1.05),
    x_labels_major_count=9,
    y_labels_major_count=6,
    value_formatter=lambda v: f"{v:.2f}",
    x_value_formatter=lambda v: f"{v:.1f}",
    margin=60,
    js=[],
)

chart.add("ECDF", step_points)

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
