""" pyplots.ai
range-interval: Range Interval Chart
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure, output_file, save


# Data - Monthly temperature ranges for a city
np.random.seed(42)

months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Realistic temperature ranges (daily low/high in Celsius)
base_temps = [2, 4, 8, 12, 16, 20, 23, 22, 18, 13, 7, 3]
min_temps = [base - np.random.uniform(3, 6) for base in base_temps]
max_temps = [base + np.random.uniform(5, 10) for base in base_temps]

# Calculate midpoints for reference
mid_temps = [(min_t + max_t) / 2 for min_t, max_t in zip(min_temps, max_temps, strict=True)]

# Create ColumnDataSource
source = ColumnDataSource(
    data={
        "month": months,
        "min_temp": min_temps,
        "max_temp": max_temps,
        "mid_temp": mid_temps,
        "x": list(range(len(months))),
    }
)

# Create figure - 4800x2700 for 16:9 landscape
p = figure(
    width=4800,
    height=2700,
    title="range-interval · bokeh · pyplots.ai",
    x_axis_label="Month",
    y_axis_label="Temperature (°C)",
    x_range=months,
    tools="",
    toolbar_location=None,
)

# Draw range bars using segment glyph (vertical lines showing min to max)
p.segment(
    x0="month",
    y0="min_temp",
    x1="month",
    y1="max_temp",
    source=source,
    line_width=40,
    line_color="#306998",
    line_alpha=0.7,
    line_cap="round",
)

# Add markers at min and max endpoints for emphasis
p.scatter(
    x="month",
    y="min_temp",
    source=source,
    size=30,
    color="#1a4971",
    line_color="white",
    line_width=4,
    legend_label="Min Temperature",
)

p.scatter(
    x="month",
    y="max_temp",
    source=source,
    size=30,
    color="#FFD43B",
    line_color="#306998",
    line_width=4,
    legend_label="Max Temperature",
)

# Add midpoint markers
p.scatter(
    x="month",
    y="mid_temp",
    source=source,
    size=18,
    marker="diamond",
    color="white",
    line_color="#1a4971",
    line_width=3,
    legend_label="Midpoint",
)

# Style the plot - larger sizes for 4800x2700 canvas
p.title.text_font_size = "36pt"
p.title.text_font_style = "bold"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Grid styling
p.xgrid.grid_line_color = None
p.ygrid.grid_line_alpha = 0.3
p.ygrid.grid_line_dash = "dashed"

# Legend styling
p.legend.label_text_font_size = "22pt"
p.legend.location = "top_left"
p.legend.background_fill_alpha = 0.9
p.legend.border_line_color = "#306998"
p.legend.border_line_width = 2
p.legend.padding = 15
p.legend.spacing = 10

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "white"

# Axis styling
p.xaxis.major_tick_line_color = "#306998"
p.yaxis.major_tick_line_color = "#306998"
p.axis.axis_line_width = 2
p.axis.axis_line_color = "#306998"

# Save outputs
export_png(p, filename="plot.png")
output_file("plot.html")
save(p)
