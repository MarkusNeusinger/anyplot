""" pyplots.ai
line-markers: Line Plot with Markers
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, Legend
from bokeh.plotting import figure


# Data - Monthly temperature readings for three weather stations
np.random.seed(42)
months = np.arange(1, 13)
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Temperature patterns for different stations (°C)
base_temp = np.array([2, 4, 8, 12, 17, 21, 24, 23, 19, 13, 7, 3])
station_a = base_temp + np.random.randn(12) * 1.5
station_b = base_temp + 3 + np.random.randn(12) * 1.5  # Warmer station
station_c = base_temp - 2 + np.random.randn(12) * 1.5  # Cooler station

# Create ColumnDataSources
source_a = ColumnDataSource(data={"x": months, "y": station_a})
source_b = ColumnDataSource(data={"x": months, "y": station_b})
source_c = ColumnDataSource(data={"x": months, "y": station_c})

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="line-markers · bokeh · pyplots.ai",
    x_axis_label="Month",
    y_axis_label="Temperature (°C)",
)

# Color palette
color_a = "#306998"  # Python Blue
color_b = "#FFD43B"  # Python Yellow
color_c = "#E74C3C"  # Colorblind-safe red

# Plot lines with markers - Station A (circles)
line_a = p.line("x", "y", source=source_a, line_width=4, color=color_a, alpha=0.9)
scatter_a = p.scatter("x", "y", source=source_a, size=20, color=color_a, marker="circle", alpha=0.9)

# Station B (squares)
line_b = p.line("x", "y", source=source_b, line_width=4, color=color_b, alpha=0.9)
scatter_b = p.scatter("x", "y", source=source_b, size=20, color=color_b, marker="square", alpha=0.9)

# Station C (triangles)
line_c = p.line("x", "y", source=source_c, line_width=4, color=color_c, alpha=0.9)
scatter_c = p.scatter("x", "y", source=source_c, size=20, color=color_c, marker="triangle", alpha=0.9)

# Legend
legend = Legend(
    items=[("Station A", [line_a, scatter_a]), ("Station B", [line_b, scatter_b]), ("Station C", [line_c, scatter_c])],
    location="top_left",
)

p.add_layout(legend)
p.legend.label_text_font_size = "20pt"
p.legend.glyph_height = 30
p.legend.glyph_width = 30
p.legend.spacing = 10
p.legend.padding = 15
p.legend.background_fill_alpha = 0.7

# Style text for 4800x2700 canvas
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Custom x-axis tick labels for months
p.xaxis.ticker = months
p.xaxis.major_label_overrides = dict(zip(months, month_labels, strict=True))

# Grid styling
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = "dashed"

# Output
export_png(p, filename="plot.png")
save(p, filename="plot.html")
