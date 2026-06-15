"""anyplot.ai
line-cycle-seasonal: Cycle Plot (Seasonal Subseries)
Library: pygal | Python 3.13
Quality: pending | Created: 2026-06-15
"""

import os
import sys

import numpy as np


# Prevent the local pygal.py from shadowing the installed pygal package
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir in sys.path:
    sys.path.remove(_script_dir)

import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

TREND_COLOR = "#009E73"  # Imprint palette position 1 — monthly subseries
MEAN_COLOR = "#AE3030"  # Imprint palette position 5 — seasonal mean reference

# Data: Monthly average temperatures (°C), temperate Northern European city, 2015–2024
np.random.seed(42)
years = list(range(2015, 2025))  # 10 years
n_years = len(years)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
n_months = 12

# Base monthly temperatures inspired by Berlin climate
month_base = np.array([1.3, 2.7, 6.5, 11.5, 16.0, 19.2, 21.3, 21.0, 16.2, 10.8, 5.6, 2.2])
warming_rate = 0.08  # °C per year — slight but visible warming over 10 years

temps = np.zeros((n_years, n_months))
for y in range(n_years):
    for m in range(n_months):
        temps[y, m] = month_base[m] + y * warming_rate + np.random.normal(0, 1.1)

month_means = temps.mean(axis=0)

# Concatenated x-axis: 12 month groups × 10 year positions, separated by 1 None slot
gap = 1
group_width = n_years + gap  # 11 slots per group
total_slots = n_months * n_years + (n_months - 1) * gap  # 131 total positions


def gstart(m):
    return m * group_width


# x_labels: month name at center of each group, empty string elsewhere
x_labels = [""] * total_slots
for m in range(n_months):
    x_labels[gstart(m) + n_years // 2] = months[m]


def trend_series(m):
    d = [None] * total_slots
    for y in range(n_years):
        d[gstart(m) + y] = round(float(temps[y, m]), 2)
    return d


def mean_series(m):
    d = [None] * total_slots
    mv = round(float(month_means[m]), 2)
    for y in range(n_years):
        d[gstart(m) + y] = mv
    return d


# Title with font size scaled to length (floor: 44)
title = "Monthly Temperature Cycle · line-cycle-seasonal · python · pygal · anyplot.ai"
n_ch = len(title)
title_font = max(44, round(66 * 67 / n_ch)) if n_ch > 67 else 66

# Palette: 12 × TREND_COLOR first, then 12 × MEAN_COLOR
palette_colors = tuple([TREND_COLOR] * n_months + [MEAN_COLOR] * n_months)

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=palette_colors,
    title_font_size=title_font,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

# Plot
chart = pygal.Line(
    style=custom_style,
    width=3200,
    height=1800,
    title=title,
    y_title="Average Temperature (°C)",
    show_dots=True,
    dots_size=2.5,
    show_legend=False,
    show_x_guides=False,
    show_y_guides=True,
    allow_interruptions=True,
    x_labels_major=months,
    show_minor_x_labels=False,
)
chart.x_labels = x_labels

# Trend line series — one per month, brand green (Imprint position 1)
for m in range(n_months):
    chart.add(months[m], trend_series(m))

# Seasonal mean reference lines — one per month, matte red (Imprint position 5)
for m in range(n_months):
    chart.add(f"Mean {months[m]}", mean_series(m), stroke_style={"width": 5, "dasharray": "8, 4"})

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
