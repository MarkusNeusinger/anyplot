""" pyplots.ai
bar-error: Bar Chart with Error Bars
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-27
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Label, TeeHead, Whisker
from bokeh.plotting import figure


# Data - Quarterly revenue by product line with standard deviation
np.random.seed(42)
categories = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books"]
values = np.array([85.2, 62.8, 48.5, 71.3, 35.7])  # Revenue in millions
errors = np.array([8.5, 5.2, 6.8, 9.1, 4.2])  # Standard deviation

# Calculate upper and lower bounds
upper = values + errors
lower = values - errors

# Create ColumnDataSource
source = ColumnDataSource(data={"categories": categories, "values": values, "upper": upper, "lower": lower})

# Create figure (4800 x 2700 px)
p = figure(
    x_range=categories,
    width=4800,
    height=2700,
    title="bar-error · bokeh · pyplots.ai",
    x_axis_label="Product Category",
    y_axis_label="Quarterly Revenue ($ millions)",
    toolbar_location=None,
)

# Draw bars
p.vbar(
    x="categories",
    top="values",
    width=0.6,
    source=source,
    fill_color="#306998",
    line_color="#1e4d6b",
    line_width=3,
    fill_alpha=0.9,
)

# Add error bars with whiskers and caps (TeeHead)
whisker = Whisker(
    source=source,
    base="categories",
    upper="upper",
    lower="lower",
    line_color="#222222",
    line_width=5,
    upper_head=TeeHead(size=40, line_color="#222222", line_width=5),
    lower_head=TeeHead(size=40, line_color="#222222", line_width=5),
)
p.add_layout(whisker)

# Style - Text sizes for 4800x2700 canvas (scaled up significantly)
p.title.text_font_size = "42pt"
p.title.text_font_style = "bold"
p.xaxis.axis_label_text_font_size = "32pt"
p.yaxis.axis_label_text_font_size = "32pt"
p.xaxis.major_label_text_font_size = "26pt"
p.yaxis.major_label_text_font_size = "24pt"

# Axis styling
p.xaxis.axis_line_width = 3
p.yaxis.axis_line_width = 3
p.xaxis.major_tick_line_width = 3
p.yaxis.major_tick_line_width = 3
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xgrid.visible = False
p.ygrid.grid_line_alpha = 0.3
p.ygrid.grid_line_dash = [6, 4]
p.ygrid.grid_line_width = 2

# Set y-axis to start at 0
p.y_range.start = 0
p.y_range.end = max(upper) + 15

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "#ffffff"
p.outline_line_color = None

# Add min_border for better layout
p.min_border_left = 120
p.min_border_bottom = 100

# Add text annotation for error bar meaning (±1 SD)
annotation = Label(
    x=4650,
    y=2500,
    x_units="screen",
    y_units="screen",
    text="Error bars: ±1 SD",
    text_font_size="24pt",
    text_color="#555555",
    text_align="right",
)
p.add_layout(annotation)

# Save as PNG
export_png(p, filename="plot.png")

# Save as HTML for interactive version
output_file("plot.html")
save(p)
