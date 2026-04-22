""" pyplots.ai
ecdf-basic: Basic ECDF Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data
np.random.seed(42)
values = np.random.randn(200) * 15 + 50  # Normal distribution: mean=50, std=15

# Compute ECDF
sorted_values = np.sort(values)
ecdf_y = np.arange(1, len(sorted_values) + 1) / len(sorted_values)

# Create step function data
# For proper ECDF step visualization, duplicate points for horizontal/vertical steps
x_step = np.repeat(sorted_values, 2)[1:]
y_step = np.repeat(ecdf_y, 2)[:-1]

# Add starting point at first value with y=0
x_step = np.concatenate([[sorted_values[0]], x_step])
y_step = np.concatenate([[0], y_step])

source = ColumnDataSource(data={"x": x_step, "y": y_step})

# Plot
p = figure(
    width=4800,
    height=2700,
    title="ecdf-basic · bokeh · pyplots.ai",
    x_axis_label="Value",
    y_axis_label="Cumulative Proportion",
    y_range=(0, 1.05),
)

# Draw step line
p.line(x="x", y="y", source=source, line_width=4, line_color="#306998", alpha=0.9)

# Style
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid styling
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = "dashed"

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="ecdf-basic · bokeh · pyplots.ai")
