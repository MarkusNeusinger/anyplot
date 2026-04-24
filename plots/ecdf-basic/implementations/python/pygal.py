""" anyplot.ai
ecdf-basic: Basic ECDF Plot
Library: pygal 3.1.0 | Python 3.14.4
Quality: 84/100 | Created: 2026-04-24
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
ACCENT = "#D55E00"

# Data — 120 food-delivery times (minutes); right-skewed gamma is realistic for
# real order-to-door durations (mean ≈ 30 min, long right tail for outliers).
np.random.seed(42)
delivery_times = np.random.gamma(shape=6.0, scale=5.0, size=120)

# ECDF: sorted values on x, cumulative proportion (k/n) on y
sorted_values = np.sort(delivery_times)
n = len(sorted_values)
ecdf_y = np.arange(1, n + 1) / n

# Step function: horizontal lead-in at y=0, then each observation adds a vertical
# jump followed by a horizontal segment.
x_lead = float(sorted_values[0]) - 2.0
step_points = [(x_lead, 0.0), (float(sorted_values[0]), 0.0)]
for i in range(n):
    step_points.append((float(sorted_values[i]), float(ecdf_y[i])))
    x_next = float(sorted_values[i + 1]) if i + 1 < n else float(sorted_values[-1]) + 2.0
    step_points.append((x_next, float(ecdf_y[i])))

# Quartile reference markers: P25, median, P75 — let readers read percentiles directly
p25 = float(np.percentile(delivery_times, 25))
p50 = float(np.percentile(delivery_times, 50))
p75 = float(np.percentile(delivery_times, 75))

font = "DejaVu Sans, Helvetica, Arial, sans-serif"

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK_SOFT,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(BRAND, ACCENT),
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
    opacity=1,
    opacity_hover=1,
    stroke_width=28,
)

chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="ecdf-basic · pygal · anyplot.ai",
    x_title="Delivery Time (minutes)",
    y_title="Cumulative Proportion",
    show_dots=False,
    show_x_guides=True,
    show_y_guides=True,
    show_legend=False,
    range=(0, 1.05),
    x_labels_major_count=9,
    y_labels_major_count=6,
    value_formatter=lambda v: f"{v:.2f}",
    x_value_formatter=lambda v: f"{v:.0f}",
    margin=60,
    js=[],
)

chart.add("ECDF", step_points)
chart.add(
    "Quartiles",
    [
        {"value": (p25, 0.25), "label": f"P25 = {p25:.1f} min"},
        {"value": (p50, 0.50), "label": f"Median = {p50:.1f} min"},
        {"value": (p75, 0.75), "label": f"P75 = {p75:.1f} min"},
    ],
    stroke=False,
    show_dots=True,
    dots_size=22,
)

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
