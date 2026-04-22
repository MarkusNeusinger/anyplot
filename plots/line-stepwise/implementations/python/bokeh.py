""" pyplots.ai
line-stepwise: Step Line Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


# Data - CPU usage readings over time with discrete state changes
np.random.seed(42)
n_points = 24
hours = np.arange(n_points)

# Create realistic CPU usage that stays at levels then jumps
base_levels = [35, 45, 75, 85, 90, 80, 60, 40, 30, 25, 40, 55, 70, 85, 95, 90, 75, 60, 50, 45, 35, 30, 25, 20]
cpu_usage = np.array(base_levels[:n_points], dtype=float)

# Add small noise to make it realistic
cpu_usage += np.random.uniform(-2, 2, n_points)
cpu_usage = np.clip(cpu_usage, 0, 100)

# Create step function data by duplicating points
# For 'post' step style: value changes after the point
x_step = []
y_step = []
for i in range(len(hours)):
    x_step.append(hours[i])
    y_step.append(cpu_usage[i])
    if i < len(hours) - 1:
        x_step.append(hours[i + 1])
        y_step.append(cpu_usage[i])

# Create data source
source = ColumnDataSource(data={"x": x_step, "y": y_step})

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="line-stepwise · bokeh · pyplots.ai",
    x_axis_label="Hour of Day",
    y_axis_label="CPU Usage (%)",
)

# Plot step line
p.line(x="x", y="y", source=source, line_width=4, line_color="#306998", line_alpha=0.9)

# Add markers at actual data points for clarity
marker_source = ColumnDataSource(data={"x": hours, "y": cpu_usage})

p.scatter(x="x", y="y", source=marker_source, size=12, color="#306998", alpha=0.9)

# Style text sizes for large canvas
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

# Background
p.background_fill_color = "#fafafa"

# Axis ranges
p.y_range.start = 0
p.y_range.end = 105

# Save as PNG and HTML
export_png(p, filename="plot.png")

# Also save as HTML for interactive version
output_file("plot.html")
save(p)
