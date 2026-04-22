""" pyplots.ai
indicator-macd: MACD Technical Indicator Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-07
"""

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Data - Generate MACD data from simulated stock prices
np.random.seed(42)

# Generate 150 days of simulated price data with a trend
n_days = 150
dates = pd.date_range("2024-01-01", periods=n_days, freq="D")
price = 100 + np.cumsum(np.random.randn(n_days) * 2 + 0.05)

# Calculate EMAs for MACD (12, 26, 9)
price_series = pd.Series(price)
ema_12 = price_series.ewm(span=12, adjust=False).mean().values
ema_26 = price_series.ewm(span=26, adjust=False).mean().values

# MACD line = 12-day EMA - 26-day EMA
macd_line = ema_12 - ema_26

# Signal line = 9-day EMA of MACD
macd_series = pd.Series(macd_line)
signal_line = macd_series.ewm(span=9, adjust=False).mean().values

# Histogram = MACD - Signal
histogram = macd_line - signal_line

# Use last 100 periods for clearer visualization
start_idx = 50
dates = dates[start_idx:]
macd_line = macd_line[start_idx:]
signal_line = signal_line[start_idx:]
histogram = histogram[start_idx:]

# Custom style for 4800x2700 canvas with distinct colors
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    # Colors: Hist+ (green), Hist- (red), MACD (blue), Signal (orange), Zero (gray)
    colors=("#2CA02C", "#D62728", "#306998", "#FF7F0E", "#888888"),
    title_font_size=72,
    label_font_size=44,
    major_label_font_size=40,
    legend_font_size=44,
    value_font_size=36,
    tooltip_font_size=32,
    stroke_width=8,
)

# Create Line chart for proper line rendering of MACD and Signal
chart = pygal.Line(
    width=4800,
    height=2700,
    style=custom_style,
    title="indicator-macd · pygal · pyplots.ai",
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

# Format dates for x-axis labels (show every 20th date to reduce crowding)
date_labels = [d.strftime("%b %d") if i % 20 == 0 else "" for i, d in enumerate(dates)]
chart.x_labels = date_labels

# Add histogram as filled area from zero line
# Positive histogram (green) - fill from zero up
hist_positive = [h if h >= 0 else 0 for h in histogram]
# Negative histogram (red) - fill from zero down
hist_negative = [h if h < 0 else 0 for h in histogram]

# Add histogram series with fill enabled (creates area from zero)
chart.add("Histogram (+)", hist_positive, fill=True, stroke_style={"width": 0})
chart.add("Histogram (−)", hist_negative, fill=True, stroke_style={"width": 0})

# Add MACD and Signal lines (rendered as proper lines)
chart.add("MACD (12,26)", list(macd_line), stroke_style={"width": 8})
chart.add("Signal (9)", list(signal_line), stroke_style={"width": 8})

# Add zero reference line (dashed)
zero_line = [0] * len(macd_line)
chart.add("Zero", zero_line, stroke_style={"width": 4, "dasharray": "15, 8"})

# Save as PNG
chart.render_to_png("plot.png")
