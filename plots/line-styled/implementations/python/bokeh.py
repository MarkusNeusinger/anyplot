""" pyplots.ai
line-styled: Styled Line Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Legend
from bokeh.plotting import figure


# Data - Monthly performance metrics over a year
np.random.seed(42)
months = np.arange(1, 13)

# Generate realistic trending data for different metrics
base = np.array([65, 68, 72, 75, 78, 82, 85, 84, 80, 77, 74, 70])
cpu_usage = base + np.random.randn(12) * 3
memory_usage = base * 0.85 + np.random.randn(12) * 4 + 10
disk_io = base * 0.7 + np.random.randn(12) * 5 + 20
network = base * 1.1 + np.random.randn(12) * 2 - 5

# Create ColumnDataSource
source = ColumnDataSource(
    data={"month": months, "cpu": cpu_usage, "memory": memory_usage, "disk": disk_io, "network": network}
)

# Create figure (4800 × 2700 px)
p = figure(
    width=4800,
    height=2700,
    title="line-styled · bokeh · pyplots.ai",
    x_axis_label="Month",
    y_axis_label="Utilization (%)",
)

# Define line styles and colors
# Using solid, dashed, dotted, and dash-dot patterns with pronounced differences
line_styles = ["solid", [20, 10], [4, 8], [20, 8, 4, 8]]
colors = ["#306998", "#FFD43B", "#4CAF50", "#FF5722"]
series_names = ["CPU Usage", "Memory Usage", "Disk I/O", "Network Traffic"]
y_columns = ["cpu", "memory", "disk", "network"]

# Create legend items
legend_items = []

for col, style, color, name in zip(y_columns, line_styles, colors, series_names, strict=True):
    # Add line with appropriate style
    line = p.line(x="month", y=col, source=source, line_width=6, color=color, line_dash=style)

    # Add scatter points for better visibility
    scatter = p.scatter(x="month", y=col, source=source, size=25, color=color, alpha=0.9)

    legend_items.append((name, [line, scatter]))

# Create and configure legend - place inside plot area
legend = Legend(items=legend_items, location="top_left")
legend.label_text_font_size = "28pt"
legend.glyph_height = 40
legend.glyph_width = 80
legend.spacing = 15
legend.padding = 20
legend.background_fill_alpha = 0.85
legend.background_fill_color = "white"
legend.border_line_color = "#cccccc"
legend.border_line_width = 2
p.add_layout(legend, "center")
p.legend.location = "top_left"

# Style configuration - larger fonts for 4800x2700 canvas
p.title.text_font_size = "48pt"
p.title.align = "center"
p.xaxis.axis_label_text_font_size = "36pt"
p.yaxis.axis_label_text_font_size = "36pt"
p.xaxis.major_label_text_font_size = "28pt"
p.yaxis.major_label_text_font_size = "28pt"

# Grid styling - subtle
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = "dashed"

# Axis styling
p.xaxis.ticker = list(range(1, 13))
p.xaxis.major_label_overrides = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec",
}

# Background and outline
p.background_fill_color = "#fafafa"
p.border_fill_color = "#ffffff"
p.outline_line_color = "#333333"

# Axis line styling
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_width = 2
p.yaxis.major_tick_line_width = 2

# Save as PNG
export_png(p, filename="plot.png")

# Save as HTML for interactivity
output_file("plot.html")
save(p)
