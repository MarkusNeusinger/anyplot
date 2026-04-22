""" pyplots.ai
indicator-ema: Exponential Moving Average (EMA) Indicator Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Data - Generate synthetic stock price data with EMA indicators
np.random.seed(42)

# Create 120 trading days
dates = pd.date_range(start="2024-01-02", periods=120, freq="B")  # Business days

# Generate realistic stock price movement (random walk with drift)
initial_price = 150.0
returns = np.random.normal(0.0008, 0.018, 120)  # Daily returns with slight upward drift
prices = initial_price * np.cumprod(1 + returns)


# Calculate EMAs (exponentially weighted moving average)
close = prices
ema_12 = pd.Series(close).ewm(span=12, adjust=False).mean().values
ema_26 = pd.Series(close).ewm(span=26, adjust=False).mean().values

# Custom style for large canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#E74C3C"),  # Price in blue, EMA12 in yellow, EMA26 in red
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

# Create line chart
chart = pygal.Line(
    width=4800,
    height=2700,
    style=custom_style,
    title="indicator-ema · pygal · pyplots.ai",
    x_title="Date",
    y_title="Price ($)",
    show_dots=False,  # Cleaner line appearance
    show_x_guides=False,
    show_y_guides=True,
    stroke_style={"width": 6},
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    x_label_rotation=45,
    truncate_label=10,
    show_minor_x_labels=False,
)

# Format date labels (show every 10th date)
chart.x_labels = [d.strftime("%Y-%m-%d") for d in dates]
chart.x_labels_major = [dates[i].strftime("%Y-%m-%d") for i in range(0, len(dates), 20)]

# Add data series - Price line should be most prominent
chart.add("Close Price", close.tolist(), stroke_style={"width": 8})
chart.add("EMA 12-day", ema_12.tolist(), stroke_style={"width": 5, "dasharray": "10,5"})
chart.add("EMA 26-day", ema_26.tolist(), stroke_style={"width": 5, "dasharray": "5,5"})

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
