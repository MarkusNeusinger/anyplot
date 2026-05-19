""" anyplot.ai
indicator-ema: Exponential Moving Average (EMA) Indicator Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-19
"""

import os
import sys


# Prevent the local pygal.py from shadowing the installed pygal package
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _here]

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Data
np.random.seed(42)
dates = pd.date_range(start="2024-01-02", periods=120, freq="B")
initial_price = 150.0
returns = np.random.normal(0.0008, 0.018, 120)
prices = initial_price * np.cumprod(1 + returns)

close = prices
ema_12 = pd.Series(close).ewm(span=12, adjust=False).mean().values
ema_26 = pd.Series(close).ewm(span=26, adjust=False).mean().values

# Detect EMA crossover points
crossover_vals = [None] * len(close)
for i in range(1, len(ema_12)):
    prev_diff = ema_12[i - 1] - ema_26[i - 1]
    curr_diff = ema_12[i] - ema_26[i]
    if prev_diff * curr_diff < 0:
        crossover_vals[i] = float(close[i])

# Style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=48,
    value_font_size=36,
    tooltip_font_size=36,
    stroke_width=6,
    opacity=0.9,
    opacity_hover=1.0,
)

# Chart
chart = pygal.Line(
    width=4800,
    height=2700,
    style=custom_style,
    title="indicator-ema · python · pygal · anyplot.ai",
    x_title="Date",
    y_title="Price ($)",
    show_dots=False,
    show_x_guides=True,
    show_y_guides=True,
    stroke_style={"width": 6},
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    x_label_rotation=45,
    truncate_label=10,
    show_minor_x_labels=False,
    dots_size=10,
)

chart.x_labels = [d.strftime("%Y-%m-%d") for d in dates]
chart.x_labels_major = [dates[i].strftime("%Y-%m-%d") for i in range(0, len(dates), 20)]

chart.add("Close Price", close.tolist(), stroke_style={"width": 8})
chart.add("EMA 12-day", ema_12.tolist(), stroke_style={"width": 5, "dasharray": "10,5"})
chart.add("EMA 26-day", ema_26.tolist(), stroke_style={"width": 5, "dasharray": "5,5"})
chart.add("Crossovers", crossover_vals, show_dots=True, stroke=False)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
