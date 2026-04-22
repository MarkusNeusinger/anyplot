""" pyplots.ai
indicator-sma: Simple Moving Average (SMA) Indicator Chart
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, Legend
from bokeh.plotting import figure


# Data - Generate realistic stock price data
np.random.seed(42)
n_days = 300

# Generate a price series with trend and volatility
dates = pd.date_range(start="2024-01-01", periods=n_days, freq="B")
returns = np.random.normal(0.0005, 0.015, n_days)
price = 100 * np.exp(np.cumsum(returns))

# Create DataFrame
df = pd.DataFrame({"date": dates, "close": price})

# Calculate SMAs
df["sma_20"] = df["close"].rolling(window=20).mean()
df["sma_50"] = df["close"].rolling(window=50).mean()
df["sma_200"] = df["close"].rolling(window=200).mean()

# Convert date to string for Bokeh x-axis
df["date_str"] = df["date"].dt.strftime("%Y-%m-%d")

# Create ColumnDataSource
source = ColumnDataSource(df)

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="indicator-sma · bokeh · pyplots.ai",
    x_axis_label="Date",
    y_axis_label="Price ($)",
    x_axis_type="datetime",
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

# Plot close price
close_line = p.line(x="date", y="close", source=source, line_width=2, color="#306998", alpha=0.9)

# Plot SMAs with distinct colors
sma20_line = p.line(x="date", y="sma_20", source=source, line_width=3, color="#FFD43B", alpha=0.9)

sma50_line = p.line(x="date", y="sma_50", source=source, line_width=3, color="#E74C3C", alpha=0.9)

sma200_line = p.line(x="date", y="sma_200", source=source, line_width=3, color="#2ECC71", alpha=0.9)

# Create legend
legend = Legend(
    items=[
        ("Close Price", [close_line]),
        ("SMA 20", [sma20_line]),
        ("SMA 50", [sma50_line]),
        ("SMA 200", [sma200_line]),
    ],
    location="top_left",
)

p.add_layout(legend)
p.legend.label_text_font_size = "18pt"
p.legend.background_fill_alpha = 0.7
p.legend.border_line_alpha = 0

# Styling for large canvas
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = [6, 4]
p.ygrid.grid_line_dash = [6, 4]

# Background
p.background_fill_color = "#FAFAFA"
p.border_fill_color = "#FFFFFF"

# Save
export_png(p, filename="plot.png")
