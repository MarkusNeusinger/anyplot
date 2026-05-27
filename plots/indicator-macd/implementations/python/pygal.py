""" anyplot.ai
indicator-macd: MACD Technical Indicator Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 80/100 | Updated: 2026-05-16
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

np.random.seed(42)

n_days = 150
dates = pd.date_range("2024-01-01", periods=n_days, freq="D")
price = 100 + np.cumsum(np.random.randn(n_days) * 2 + 0.05)

price_series = pd.Series(price)
ema_12 = price_series.ewm(span=12, adjust=False).mean().values
ema_26 = price_series.ewm(span=26, adjust=False).mean().values

macd_line = ema_12 - ema_26

macd_series = pd.Series(macd_line)
signal_line = macd_series.ewm(span=9, adjust=False).mean().values

histogram = macd_line - signal_line

start_idx = 50
dates = dates[start_idx:]
macd_line = macd_line[start_idx:]
signal_line = signal_line[start_idx:]
histogram = histogram[start_idx:]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=("#009E73", "#C475FD", "#2CA02C", "#D62728", INK_MUTED),
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=3,
)

chart = pygal.Line(
    width=4800,
    height=2700,
    style=custom_style,
    title="indicator-macd · pygal · anyplot.ai",
    x_title="Date",
    y_title="MACD Value",
    show_x_guides=False,
    show_y_guides=True,
    x_label_rotation=45,
    legend_at_bottom=True,
    legend_box_size=36,
    margin=60,
    show_dots=False,
    fill=False,
    zero=0,
)

date_labels = [d.strftime("%b %d") if i % 20 == 0 else "" for i, d in enumerate(dates)]
chart.x_labels = date_labels

hist_positive = [h if h >= 0 else 0 for h in histogram]
hist_negative = [h if h < 0 else 0 for h in histogram]

chart.add("Histogram (+)", hist_positive, fill=True, stroke_style={"width": 0})
chart.add("Histogram (−)", hist_negative, fill=True, stroke_style={"width": 0})

chart.add("MACD (12,26)", list(macd_line), stroke_style={"width": 3})
chart.add("Signal (9)", list(signal_line), stroke_style={"width": 3})

zero_line = [0] * len(macd_line)
chart.add("Zero", zero_line, stroke_style={"width": 2, "dasharray": "15, 8"})

chart.render_to_png(f"plot-{THEME}.png")

with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
