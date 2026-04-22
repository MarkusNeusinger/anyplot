""" pyplots.ai
ecdf-basic: Basic ECDF Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-17
"""

import numpy as np
import pygal
from pygal.style import Style


# Data
np.random.seed(42)
values = np.random.randn(100)

# Calculate ECDF
sorted_values = np.sort(values)
n = len(sorted_values)
ecdf_y = np.arange(1, n + 1) / n

# Build step function data for XY chart
# Each point needs to create a horizontal step then a vertical step
xy_data = []
for i in range(n):
    if i == 0:
        # First point: start from (value, 0) to show initial step
        xy_data.append((sorted_values[i], 0))
    else:
        # Horizontal line from previous point to current x
        xy_data.append((sorted_values[i], ecdf_y[i - 1]))
    # Vertical step up to current y
    xy_data.append((sorted_values[i], ecdf_y[i]))

# Extend to the right edge for completeness
xy_data.append((sorted_values[-1] + 0.5, ecdf_y[-1]))

# Custom style for 4800x2700 px canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333",
    foreground_strong="#333",
    foreground_subtle="#666",
    colors=("#306998",),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=42,
    value_font_size=36,
)

# Create XY chart (scatter-like with lines for step function)
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="ecdf-basic · pygal · pyplots.ai",
    x_title="Value",
    y_title="Cumulative Proportion",
    show_dots=False,
    stroke_style={"width": 4},
    show_x_guides=True,
    show_y_guides=True,
    show_legend=False,
    range=(0, 1.05),
)

# Add ECDF data
chart.add("ECDF", xy_data)

# Save outputs
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
