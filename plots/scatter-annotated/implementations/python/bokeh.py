""" pyplots.ai
scatter-annotated: Annotated Scatter Plot with Text Labels
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, LabelSet
from bokeh.plotting import figure


# Data - Company market performance example
np.random.seed(42)
companies = [
    "TechCorp",
    "DataSys",
    "CloudNet",
    "AIVenture",
    "NetFlow",
    "CodeBase",
    "ByteWorks",
    "DigiCore",
    "InfoTech",
    "WebScale",
    "AppLogic",
    "SoftPeak",
    "CyberLink",
    "DevOps",
    "QuantumBit",
]

# Revenue (billions) and Market Cap (billions)
revenue = np.array([12.5, 8.3, 22.1, 5.7, 15.8, 9.2, 18.4, 6.9, 11.3, 25.6, 7.4, 14.2, 19.8, 4.5, 10.1])
market_cap = np.array([45.2, 28.1, 85.3, 32.5, 52.8, 35.6, 68.9, 25.4, 41.7, 98.2, 22.3, 55.4, 72.1, 18.9, 38.5])

# Create ColumnDataSource
source = ColumnDataSource(data={"x": revenue, "y": market_cap, "labels": companies})

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="scatter-annotated · bokeh · pyplots.ai",
    x_axis_label="Revenue (Billions $)",
    y_axis_label="Market Cap (Billions $)",
    tools="pan,wheel_zoom,box_zoom,reset",
)

# Plot scatter points - larger size for visibility
p.scatter(x="x", y="y", source=source, size=40, color="#306998", alpha=0.7, line_color="#1a3d5c", line_width=3)

# Add text labels with offset - larger font for 4800x2700 canvas
labels = LabelSet(
    x="x",
    y="y",
    text="labels",
    source=source,
    x_offset=25,
    y_offset=15,
    text_font_size="24pt",
    text_color="#333333",
    text_font_style="bold",
)
p.add_layout(labels)

# Style title - large for visibility
p.title.text_font_size = "42pt"
p.title.text_color = "#333333"
p.title.align = "center"

# Style axes labels - large for readability
p.xaxis.axis_label_text_font_size = "32pt"
p.yaxis.axis_label_text_font_size = "32pt"
p.xaxis.axis_label_text_color = "#333333"
p.yaxis.axis_label_text_color = "#333333"

# Style tick labels - larger
p.xaxis.major_label_text_font_size = "24pt"
p.yaxis.major_label_text_font_size = "24pt"

# Style grid
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = [6, 4]
p.grid.grid_line_color = "#888888"

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "#ffffff"

# Axis styling
p.axis.axis_line_color = "#555555"
p.axis.axis_line_width = 2
p.axis.major_tick_line_width = 2
p.axis.minor_tick_line_width = 1

# Save
export_png(p, filename="plot.png")
