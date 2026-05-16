"""anyplot.ai
candlestick-volume: Stock Candlestick Chart with Volume
Library: pygal | Python 3.13
Quality: pending | Created: 2025-05-16
"""

import os
import sys

import numpy as np
import pandas as pd


current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != current_dir]

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

UP_COLOR = "#009E73"
DOWN_COLOR = "#D55E00"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

np.random.seed(42)
n_periods = 60

dates = pd.date_range("2024-01-01", periods=n_periods, freq="D")
date_nums = np.arange(n_periods)

close_prices = 100 + np.cumsum(np.random.normal(0.3, 1.5, n_periods))
open_prices = close_prices + np.random.normal(0, 0.4, n_periods)
high_prices = np.maximum(open_prices, close_prices) + np.abs(np.random.normal(0, 1.2, n_periods))
low_prices = np.minimum(open_prices, close_prices) - np.abs(np.random.normal(0, 1.2, n_periods))
volumes = np.random.uniform(1e6, 4e6, n_periods)

volume_scaled = (volumes - volumes.min()) / (volumes.max() - volumes.min()) * 15 + low_prices.min()

up_mask = close_prices >= open_prices
down_mask = ~up_mask

up_points = [(float(date_nums[i]), float(high_prices[i])) for i in range(n_periods) if up_mask[i]]
down_points = [(float(date_nums[i]), float(high_prices[i])) for i in range(n_periods) if down_mask[i]]

high_points = [(float(date_nums[i]), float(high_prices[i])) for i in range(n_periods)]
low_points = [(float(date_nums[i]), float(low_prices[i])) for i in range(n_periods)]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=3,
)

chart = pygal.XY(
    style=custom_style,
    width=4800,
    height=2700,
    title="Tesla Stock · candlestick-volume · pygal · anyplot.ai",
    x_title="Trading Day",
    y_title="Price (USD) / Volume Index",
    show_legend=True,
    show_y_guides=True,
    show_x_guides=False,
)

if up_points:
    chart.add("↑ Close (Up days)", up_points, dots_size=10, color=UP_COLOR, show_only_major_dots=False)
if down_points:
    chart.add("↓ Close (Down days)", down_points, dots_size=10, color=DOWN_COLOR, show_only_major_dots=False)

chart.add("High", high_points, stroke_width=2, color=INK_MUTED, opacity=0.4, show_only_major_dots=False)
chart.add("Low", low_points, stroke_width=2, color=INK_MUTED, opacity=0.4, show_only_major_dots=False)
chart.add(
    "Volume Index",
    [(float(date_nums[i]), float(volume_scaled[i])) for i in range(n_periods)],
    stroke_width=2,
    color="#56B4E9",
    opacity=0.5,
    show_only_major_dots=False,
)

x_labels = [str(i + 1) if i % 10 == 0 else "" for i in range(n_periods)]
chart.x_labels = x_labels

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
