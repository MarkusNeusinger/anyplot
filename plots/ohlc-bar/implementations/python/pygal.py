""" pyplots.ai
ohlc-bar: OHLC Bar Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-08
"""

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Data - Generate realistic stock price data
np.random.seed(42)
n_days = 40

# Starting price and generate daily returns
start_price = 150.0
daily_returns = np.random.normal(0.001, 0.02, n_days)

# Generate OHLC data
dates = pd.date_range("2024-06-01", periods=n_days, freq="B")  # Business days
closes = start_price * np.cumprod(1 + daily_returns)
opens = np.roll(closes, 1)
opens[0] = start_price

# Generate highs and lows based on volatility
daily_volatility = np.abs(np.random.normal(0.01, 0.005, n_days))
highs = np.maximum(opens, closes) * (1 + daily_volatility)
lows = np.minimum(opens, closes) * (1 - daily_volatility)

# Custom style for 4800x2700 px canvas
# Use green for up bars, red for down bars
up_color = "#27AE60"
down_color = "#E74C3C"

custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#999999",
    guide_stroke_color="#CCCCCC",
    opacity=".95",
    opacity_hover=".85",
    colors=(up_color, down_color),
    title_font_size=60,
    label_font_size=32,
    major_label_font_size=28,
    legend_font_size=32,
    value_font_size=28,
    tooltip_font_size=24,
    stroke_width=6,
)

# Create date labels for x-axis (every 5th date for clarity)
date_labels = {i: dates[i].strftime("%b %d") for i in range(0, n_days, 5)}

# Create XY chart with legend near plot
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="ohlc-bar · pygal · pyplots.ai",
    x_title="Date (Jun-Aug 2024)",
    y_title="Price ($)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
    legend_box_size=24,
    show_x_guides=False,
    show_y_guides=True,
    truncate_label=-1,
    truncate_legend=-1,
    stroke=True,
    show_dots=False,
    x_labels=list(date_labels.values()),
    x_labels_major_every=1,
)

# Tick width for open/close marks (slightly wider for visibility)
tick_width = 0.4

# Build OHLC bar segments - each bar needs:
# 1. Vertical line from low to high
# 2. Open tick (left horizontal)
# 3. Close tick (right horizontal)

# Separate up and down bars into different series
up_bars = []  # Each bar as list of points with None separators
down_bars = []

for i in range(n_days):
    x = float(i)
    o, h, lo, c = opens[i], highs[i], lows[i], closes[i]

    # Each OHLC bar: vertical line + open tick + close tick
    bar_points = [
        # Vertical line (low to high)
        (x, lo),
        (x, h),
        # Break
        (None, None),
        # Open tick (left horizontal)
        (x - tick_width, o),
        (x, o),
        # Break
        (None, None),
        # Close tick (right horizontal)
        (x, c),
        (x + tick_width, c),
        # Break for next bar
        (None, None),
    ]

    if c >= o:  # Up bar (bullish)
        up_bars.extend(bar_points)
    else:  # Down bar (bearish)
        down_bars.extend(bar_points)

# Add series with descriptive legend labels
chart.add("Bullish (Close ≥ Open)", up_bars)
chart.add("Bearish (Close < Open)", down_bars)

# Save outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
