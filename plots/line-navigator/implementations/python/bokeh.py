""" pyplots.ai
line-navigator: Line Chart with Mini Navigator
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, save
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, RangeTool
from bokeh.plotting import figure


# Data - Daily sensor readings over 3 years (1095 points)
np.random.seed(42)
n_points = 1095
dates = pd.date_range(start="2022-01-01", periods=n_points, freq="D")

# Generate realistic sensor data with trend, seasonality, and noise
trend = np.linspace(50, 80, n_points)
seasonal = 15 * np.sin(2 * np.pi * np.arange(n_points) / 365)
noise = np.random.randn(n_points) * 5
values = trend + seasonal + noise

source = ColumnDataSource(data={"date": dates, "value": values})

# Colors
line_color = "#306998"  # Python Blue

# Main chart - shows selected range in detail
main_plot = figure(
    width=4800,
    height=2200,
    title="line-navigator · bokeh · pyplots.ai",
    x_axis_type="datetime",
    x_axis_label="Date",
    y_axis_label="Sensor Reading (units)",
    x_range=(dates[700], dates[900]),  # Initial visible range (about 200 days)
)

main_plot.line("date", "value", source=source, line_width=3, line_color=line_color, alpha=0.9)

# Styling for main plot
main_plot.title.text_font_size = "32pt"
main_plot.xaxis.axis_label_text_font_size = "24pt"
main_plot.yaxis.axis_label_text_font_size = "24pt"
main_plot.xaxis.major_label_text_font_size = "18pt"
main_plot.yaxis.major_label_text_font_size = "18pt"
main_plot.grid.grid_line_alpha = 0.3
main_plot.grid.grid_line_dash = [6, 4]

# Navigator (mini chart) - shows full data extent
navigator = figure(
    width=4800,
    height=500,
    x_axis_type="datetime",
    y_axis_type=None,
    x_axis_label="",
    y_axis_label="",
    y_range=main_plot.y_range,
)

navigator.line("date", "value", source=source, line_width=2, line_color=line_color, alpha=0.6)

# RangeTool connects the navigator selection to the main plot's x_range
range_tool = RangeTool(x_range=main_plot.x_range)
range_tool.overlay.fill_color = "#FFD43B"  # Python Yellow
range_tool.overlay.fill_alpha = 0.3

navigator.add_tools(range_tool)

# Styling for navigator
navigator.xaxis.major_label_text_font_size = "16pt"
navigator.grid.grid_line_alpha = 0.2

# Combine plots vertically
layout = column(main_plot, navigator, sizing_mode="fixed")

# Save outputs
export_png(layout, filename="plot.png")
save(layout, filename="plot.html", title="Line Chart with Mini Navigator")
