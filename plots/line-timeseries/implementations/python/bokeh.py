""" pyplots.ai
line-timeseries: Time Series Line Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - Stock price simulation over one year
np.random.seed(42)
dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
n_points = len(dates)

# Simulate stock price with trend, seasonality, and noise
base_price = 150
trend = np.linspace(0, 30, n_points)
seasonality = 10 * np.sin(np.linspace(0, 4 * np.pi, n_points))
noise = np.cumsum(np.random.randn(n_points) * 0.8)
prices = base_price + trend + seasonality + noise
prices = np.maximum(prices, 50)  # Floor at 50

source = ColumnDataSource(data={"date": dates, "price": prices})

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="line-timeseries · bokeh · pyplots.ai",
    x_axis_label="Date",
    y_axis_label="Stock Price (USD)",
    x_axis_type="datetime",
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

# Plot the line
p.line(x="date", y="price", source=source, line_width=6, line_color="#306998", legend_label="Stock Price")

# Add hover tool
hover = HoverTool(
    tooltips=[("Date", "@date{%F}"), ("Price", "$@price{0.00}")], formatters={"@date": "datetime"}, mode="vline"
)
p.add_tools(hover)

# Styling - text sizes for 4800x2700 px canvas (larger for visibility)
p.title.text_font_size = "48pt"
p.xaxis.axis_label_text_font_size = "36pt"
p.yaxis.axis_label_text_font_size = "36pt"
p.xaxis.major_label_text_font_size = "28pt"
p.yaxis.major_label_text_font_size = "28pt"

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

# Legend styling
p.legend.location = "top_left"
p.legend.label_text_font_size = "28pt"
p.legend.background_fill_alpha = 0.7
p.legend.glyph_height = 30
p.legend.glyph_width = 50

# Axis styling
p.xaxis.major_label_orientation = 0.8  # Slight rotation to prevent overlap

# Background
p.background_fill_color = "#fafafa"

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="line-timeseries · bokeh · pyplots.ai")
