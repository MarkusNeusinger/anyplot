""" pyplots.ai
indicator-bollinger: Bollinger Bands Indicator Chart
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-07
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png
from bokeh.models import Band, ColumnDataSource, HoverTool, Legend
from bokeh.plotting import figure, output_file, save


# Data - Generate synthetic stock price data
np.random.seed(42)
n_days = 120

# Generate realistic price movement using random walk with drift
dates = pd.date_range("2024-01-01", periods=n_days, freq="B")  # Business days
returns = np.random.normal(0.0005, 0.015, n_days)  # Daily returns with slight upward drift
price = 100 * np.cumprod(1 + returns)

# Calculate Bollinger Bands (20-period SMA, 2 standard deviations)
window = 20
sma = pd.Series(price).rolling(window=window).mean().values
std = pd.Series(price).rolling(window=window).std().values
upper_band = sma + 2 * std
lower_band = sma - 2 * std

# Create DataFrame for cleaner handling
df = pd.DataFrame({"date": dates, "close": price, "sma": sma, "upper_band": upper_band, "lower_band": lower_band})

# Drop NaN values from the start (due to rolling window)
df = df.dropna().reset_index(drop=True)

# Create ColumnDataSource
source = ColumnDataSource(df)

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="indicator-bollinger · bokeh · pyplots.ai",
    x_axis_label="Date",
    y_axis_label="Price ($)",
    x_axis_type="datetime",
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

# Add the band fill between upper and lower bands
band = Band(
    base="date",
    lower="lower_band",
    upper="upper_band",
    source=source,
    fill_alpha=0.25,
    fill_color="#306998",
    line_color="#306998",
    line_alpha=0.3,
)
p.add_layout(band)

# Plot the bands and price lines with legend
# Upper band
upper_line = p.line(
    "date", "upper_band", source=source, line_color="#306998", line_width=3, line_dash="solid", alpha=0.8
)

# Lower band
lower_line = p.line(
    "date", "lower_band", source=source, line_color="#306998", line_width=3, line_dash="solid", alpha=0.8
)

# Middle band (SMA) - dashed line
sma_line = p.line("date", "sma", source=source, line_color="#FFD43B", line_width=4, line_dash="dashed", alpha=0.9)

# Price line - most prominent
price_line = p.line("date", "close", source=source, line_color="#1a1a2e", line_width=5, alpha=1.0)

# Add hover tool for interactivity
hover = HoverTool(
    tooltips=[
        ("Date", "@date{%F}"),
        ("Close", "$@close{0.2f}"),
        ("SMA (20)", "$@sma{0.2f}"),
        ("Upper Band", "$@upper_band{0.2f}"),
        ("Lower Band", "$@lower_band{0.2f}"),
    ],
    formatters={"@date": "datetime"},
    mode="vline",
    renderers=[price_line],
)
p.add_tools(hover)

# Create legend
legend = Legend(
    items=[("Close Price", [price_line]), ("SMA (20)", [sma_line]), ("Upper/Lower Band (±2σ)", [upper_line])],
    location="top_left",
)

p.add_layout(legend, "right")

# Style the plot
p.title.text_font_size = "36pt"
p.title.text_font_style = "bold"
p.xaxis.axis_label_text_font_size = "26pt"
p.yaxis.axis_label_text_font_size = "26pt"
p.xaxis.major_label_text_font_size = "20pt"
p.yaxis.major_label_text_font_size = "20pt"

# Legend styling
p.legend.label_text_font_size = "22pt"
p.legend.glyph_width = 50
p.legend.glyph_height = 30
p.legend.spacing = 15
p.legend.padding = 20
p.legend.background_fill_alpha = 0.9

# Grid styling
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = [6, 4]

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "#ffffff"

# Axis styling
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_width = 2
p.yaxis.major_tick_line_width = 2

# Save PNG
export_png(p, filename="plot.png")

# Save interactive HTML
output_file("plot.html", title="Bollinger Bands - bokeh - pyplots.ai")
save(p)
