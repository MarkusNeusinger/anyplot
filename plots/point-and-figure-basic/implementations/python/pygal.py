"""anyplot.ai
point-and-figure-basic: Point and Figure Chart
Library: pygal | Python 3.13
Quality: pending | Updated: 2026-05-20
"""

import os as _os
import sys as _sys


# This file is named pygal.py — remove its directory from sys.path first so
# Python resolves `pygal` to the installed package, not this file itself.
_here = _os.path.abspath(_os.path.dirname(__file__))
_sys.path = [p for p in _sys.path if _os.path.abspath(p or ".") != _here]

import os

import numpy as np
import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Data
np.random.seed(42)
n_days = 150
base_price = 100.0
returns = np.random.normal(0.001, 0.02, n_days)
prices = base_price * np.cumprod(1 + returns)

# P&F parameters
box_size = 2.0
reversal = 3

# P&F algorithm
columns = []
current_direction = None
current_column_start = np.floor(prices[0] / box_size) * box_size
current_column_end = current_column_start

for price in prices[1:]:
    rounded_price = np.floor(price / box_size) * box_size

    if current_direction is None:
        if rounded_price >= current_column_end + box_size:
            current_direction = "X"
            current_column_end = rounded_price
        elif rounded_price <= current_column_end - box_size:
            current_direction = "O"
            current_column_end = rounded_price
    elif current_direction == "X":
        if rounded_price >= current_column_end + box_size:
            current_column_end = rounded_price
        elif rounded_price <= current_column_end - (reversal * box_size):
            columns.append((current_column_start, current_column_end, "X"))
            current_column_start = current_column_end - box_size
            current_column_end = rounded_price
            current_direction = "O"
    else:
        if rounded_price <= current_column_end - box_size:
            current_column_end = rounded_price
        elif rounded_price >= current_column_end + (reversal * box_size):
            columns.append((current_column_start, current_column_end, "O"))
            current_column_start = current_column_end + box_size
            current_column_end = rounded_price
            current_direction = "X"

if current_direction:
    columns.append((current_column_start, current_column_end, current_direction))

# Price range for y-axis
all_prices = [p for start, end, _ in columns for p in (start, end)]
y_min = min(all_prices) - box_size
y_max = max(all_prices) + box_size
y_labels = list(np.arange(y_min, y_max + box_size, box_size))

# Style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=3,
)

# Plot — no chart-level stroke setting so per-series stroke works correctly
chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="point-and-figure-basic · python · pygal · anyplot.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    show_y_guides=True,
    show_x_guides=False,
    x_title="Column (Reversal)",
    y_title="Price ($)",
    margin=80,
    margin_bottom=200,
    margin_left=220,
    margin_top=120,
    margin_right=100,
    y_labels=y_labels,
    range=(y_min, y_max),
    dots_size=18,
)

# Build X and O data points
x_points = []
o_points = []

for col_idx, (start, end, direction) in enumerate(columns):
    low = min(start, end)
    high = max(start, end)
    price_levels = np.arange(low, high + box_size * 0.5, box_size)
    if direction == "X":
        x_points.extend((col_idx, lv) for lv in price_levels)
    else:
        o_points.extend((col_idx, lv) for lv in price_levels)

# Per-series stroke=False keeps dots unconnected; overrides chart default
chart.add("X (Rising)", x_points, stroke=False)
chart.add("O (Falling)", o_points, stroke=False)

# Trend lines — per-series stroke=True draws the line
support_lows = [(ci, min(s, e)) for ci, (s, e, d) in enumerate(columns) if d == "O"]
resistance_highs = [(ci, max(s, e)) for ci, (s, e, d) in enumerate(columns) if d == "X"]

if len(support_lows) >= 2:
    c0, p0 = support_lows[0]
    c1 = min(c0 + 6, len(columns) - 1)
    chart.add(
        "Support (45°)",
        [(c0, p0), (c1, p0 + (c1 - c0) * box_size)],
        stroke=True,
        dots_size=4,
        stroke_style={"width": 4, "dasharray": "8, 6"},
    )

if len(resistance_highs) >= 2:
    c0, p0 = resistance_highs[0]
    c1 = min(c0 + 6, len(columns) - 1)
    chart.add(
        "Resistance (45°)",
        [(c0, p0), (c1, p0 - (c1 - c0) * box_size)],
        stroke=True,
        dots_size=4,
        stroke_style={"width": 4, "dasharray": "8, 6"},
    )

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
