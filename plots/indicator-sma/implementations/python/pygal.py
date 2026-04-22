""" pyplots.ai
indicator-sma: Simple Moving Average (SMA) Indicator Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Data - Generate realistic stock price data with SMAs
np.random.seed(42)

# Create date range for ~1 year of trading days
dates = pd.date_range("2025-01-02", periods=300, freq="B")

# Generate realistic price movement using geometric Brownian motion
initial_price = 150.0
returns = np.random.normal(0.0003, 0.015, len(dates))
prices = initial_price * np.cumprod(1 + returns)

# Calculate SMAs
df = pd.DataFrame({"date": dates, "close": prices})
df["sma_20"] = df["close"].rolling(window=20).mean()
df["sma_50"] = df["close"].rolling(window=50).mean()
df["sma_200"] = df["close"].rolling(window=200).mean()

# Convert dates to strings for x-axis labels (show every 30 days)
x_labels = [d.strftime("%Y-%m-%d") if i % 30 == 0 else "" for i, d in enumerate(dates)]

# Custom style for large canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#E74C3C", "#2ECC71"),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=48,
    value_font_size=36,
    stroke_width=4,
    opacity=".9",
    opacity_hover=".95",
)

# Create line chart
chart = pygal.Line(
    width=4800,
    height=2700,
    style=custom_style,
    title="indicator-sma \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Date",
    y_title="Price (USD)",
    show_x_guides=False,
    show_y_guides=True,
    x_label_rotation=45,
    truncate_label=10,
    show_dots=False,
    legend_at_bottom=False,
    legend_box_size=24,
    margin=50,
    spacing=30,
)

# Add data series
chart.x_labels = x_labels

# Add price and SMA lines - convert NaN to None for pygal
close_list = [float(v) for v in df["close"]]
sma_20_list = [None if pd.isna(v) else float(v) for v in df["sma_20"]]
sma_50_list = [None if pd.isna(v) else float(v) for v in df["sma_50"]]
sma_200_list = [None if pd.isna(v) else float(v) for v in df["sma_200"]]

chart.add("Close Price", close_list)
chart.add("SMA 20", sma_20_list)
chart.add("SMA 50", sma_50_list)
chart.add("SMA 200", sma_200_list)

# Save as PNG
chart.render_to_png("plot.png")

# Save as HTML for interactive viewing
chart.render_to_file("plot.html")
