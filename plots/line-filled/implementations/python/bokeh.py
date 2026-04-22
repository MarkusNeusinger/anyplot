""" pyplots.ai
line-filled: Filled Line Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - Monthly website traffic over a year
np.random.seed(42)
months = np.arange(1, 13)
# Simulate traffic with seasonal trend (higher in summer/winter holidays)
base_traffic = 50000
seasonal = 15000 * np.sin(2 * np.pi * (months - 3) / 12)  # Peak in summer
trend = 2000 * months  # Gradual growth
noise = np.random.normal(0, 3000, 12)
traffic = base_traffic + seasonal + trend + noise
traffic = np.maximum(traffic, 0)  # Ensure positive values

# Create ColumnDataSource
source = ColumnDataSource(data={"month": months, "traffic": traffic, "traffic_zero": np.zeros(len(months))})

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="line-filled · bokeh · pyplots.ai",
    x_axis_label="Month",
    y_axis_label="Website Visitors",
)

# Filled area using varea
p.varea(x="month", y1="traffic_zero", y2="traffic", source=source, fill_color="#306998", fill_alpha=0.4)

# Line on top of the fill
p.line(x="month", y="traffic", source=source, line_color="#306998", line_width=4)

# Add points for visual emphasis
p.scatter(x="month", y="traffic", source=source, size=12, color="#306998", fill_alpha=0.8)

# Add hover tool
hover = HoverTool(tooltips=[("Month", "@month"), ("Visitors", "@traffic{0,0}")])
p.add_tools(hover)

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
p.background_fill_color = "#fafafa"
p.border_fill_color = "#ffffff"

# X-axis ticks for each month
p.xaxis.ticker = list(range(1, 13))

# Save as PNG and HTML
export_png(p, filename="plot.png")

# Also save interactive HTML
save(p, filename="plot.html", resources=CDN, title="line-filled · bokeh · pyplots.ai")
