""" pyplots.ai
dashboard-synchronized-crosshair: Synchronized Multi-Chart Dashboard
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-20
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, output_file, save
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, CrosshairTool, HoverTool
from bokeh.plotting import figure


# Data - Stock data with price, volume, and RSI over 200 trading days
np.random.seed(42)
n_points = 200
dates = pd.date_range("2024-01-01", periods=n_points, freq="B")

# Generate price data (random walk)
price_changes = np.random.randn(n_points) * 2 + 0.05
price = 100 + np.cumsum(price_changes)

# Generate volume data (correlated with price volatility)
volume = np.abs(price_changes) * 1e6 + np.random.uniform(1e6, 3e6, n_points)

# Generate RSI-like indicator (oscillating between 30-70 mostly)
rsi = 50 + np.cumsum(np.random.randn(n_points) * 3)
rsi = np.clip(rsi, 20, 80)

# Create ColumnDataSource for linked brushing
source = ColumnDataSource(
    data={
        "date": dates,
        "price": price,
        "volume": volume / 1e6,  # Convert to millions
        "rsi": rsi,
        "date_str": dates.strftime("%Y-%m-%d"),
    }
)

# Create synchronized crosshair tool
crosshair = CrosshairTool(dimensions="height", line_color="#306998", line_alpha=0.8, line_width=2)

# Common figure settings
common_opts = {"width": 4800, "height": 800, "x_axis_type": "datetime", "tools": "pan,wheel_zoom,box_zoom,reset"}

# Chart 1: Price
p1 = figure(**common_opts, title="dashboard-synchronized-crosshair · bokeh · pyplots.ai", y_axis_label="Price ($)")
p1.line("date", "price", source=source, line_width=3, color="#306998", legend_label="Price")
p1.add_tools(crosshair)
p1.add_tools(HoverTool(tooltips=[("Date", "@date_str"), ("Price", "$@price{0.00}")], mode="vline"))

# Chart 2: Volume
p2 = figure(
    **common_opts,
    x_range=p1.x_range,  # Link x-axis
    y_axis_label="Volume (M)",
)
p2.vbar(
    "date", top="volume", source=source, width=60 * 60 * 1000 * 20, color="#FFD43B", alpha=0.8, legend_label="Volume"
)
p2.add_tools(CrosshairTool(dimensions="height", line_color="#306998", line_alpha=0.8, line_width=2))
p2.add_tools(HoverTool(tooltips=[("Date", "@date_str"), ("Volume", "@volume{0.00}M")], mode="vline"))

# Chart 3: RSI
p3 = figure(
    **common_opts,
    x_range=p1.x_range,  # Link x-axis
    x_axis_label="Date",
    y_axis_label="RSI",
)
p3.line("date", "rsi", source=source, line_width=3, color="#4B8BBE", legend_label="RSI")
# RSI reference lines
p3.line(dates, [70] * n_points, line_dash="dashed", line_width=2, color="#E74C3C", alpha=0.7)
p3.line(dates, [30] * n_points, line_dash="dashed", line_width=2, color="#27AE60", alpha=0.7)
p3.add_tools(CrosshairTool(dimensions="height", line_color="#306998", line_alpha=0.8, line_width=2))
p3.add_tools(HoverTool(tooltips=[("Date", "@date_str"), ("RSI", "@rsi{0.0}")], mode="vline"))

# Style all charts
for p in [p1, p2, p3]:
    p.title.text_font_size = "28pt"
    p.xaxis.axis_label_text_font_size = "22pt"
    p.yaxis.axis_label_text_font_size = "22pt"
    p.xaxis.major_label_text_font_size = "18pt"
    p.yaxis.major_label_text_font_size = "18pt"
    p.legend.label_text_font_size = "18pt"
    p.legend.location = "top_left"
    p.grid.grid_line_alpha = 0.3
    p.background_fill_color = "#FAFAFA"

# Remove x-axis labels from top charts for cleaner layout
p1.xaxis.visible = False
p2.xaxis.visible = False

# Create stacked layout
layout = column(p1, p2, p3, sizing_mode="fixed")

# Save as PNG and HTML
export_png(layout, filename="plot.png")
output_file("plot.html")
save(layout)
