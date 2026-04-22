""" pyplots.ai
area-basic: Basic Area Chart
Library: bokeh 3.8.2 | Python 3.14.2
Quality: 90/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label
from bokeh.plotting import figure


# Data - daily website visitors over a month
np.random.seed(42)
dates = pd.date_range(start="2024-01-01", periods=31, freq="D")
base_visitors = 5000
trend = np.linspace(0, 1500, 31)
weekly_pattern = 800 * np.sin(np.arange(31) * 2 * np.pi / 7)
noise = np.random.randn(31) * 400
visitors = base_visitors + trend + weekly_pattern + noise
visitors = np.maximum(visitors, 1000)

# Add a viral traffic spike on day 18 (campaign launch)
visitors[17] = 9200
visitors[18] = 8600
visitors[19] = 7800

source = ColumnDataSource(data={"date": dates, "visitors": visitors})

# Create figure (4800 x 2700 px)
p = figure(
    width=4800,
    height=2700,
    title="Daily Website Traffic · area-basic · bokeh · pyplots.ai",
    x_axis_label="Date",
    y_axis_label="Daily Visitors",
    x_axis_type="datetime",
)

# Area chart - fill from bottom to line
p.varea(x="date", y1=0, y2="visitors", source=source, fill_color="#306998", fill_alpha=0.4)

# Line on top for clear edge
p.line(x="date", y="visitors", source=source, line_color="#306998", line_width=5)

# Invisible scatter for hover targets
p.scatter(x="date", y="visitors", source=source, size=20, fill_alpha=0, line_alpha=0)

# HoverTool for interactive exploration
hover = HoverTool(
    tooltips=[("Date", "@date{%b %d, %Y}"), ("Visitors", "@visitors{0,0}")],
    formatters={"@date": "datetime"},
    mode="vline",
)
p.add_tools(hover)

# Annotation - highlight the viral spike
spike_label = Label(
    x=dates[17],
    y=9400,
    text="Campaign launch  +84%",
    text_font_size="32pt",
    text_color="#1a3d5c",
    text_font_style="bold",
    x_offset=20,
    y_offset=0,
)
p.add_layout(spike_label)

# Text sizing scaled for 4800x2700 canvas
p.title.text_font_size = "42pt"
p.xaxis.axis_label_text_font_size = "32pt"
p.yaxis.axis_label_text_font_size = "32pt"
p.xaxis.major_label_text_font_size = "26pt"
p.yaxis.major_label_text_font_size = "26pt"

# Grid styling - subtle solid lines
p.xgrid.grid_line_alpha = 0.2
p.ygrid.grid_line_alpha = 0.2

# Clean frame - remove outline border
p.outline_line_color = None

# Axis line styling
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_width = 2
p.yaxis.major_tick_line_width = 2

# Remove toolbar for clean export
p.toolbar_location = None

# Ensure y-axis starts at 0 with headroom for annotation
p.y_range.start = 0
p.y_range.end = 10500

# Add padding to margins
p.min_border_left = 140
p.min_border_bottom = 120

# Save as PNG
export_png(p, filename="plot.png")

# Save as HTML for interactive viewing
output_file("plot.html")
save(p)
