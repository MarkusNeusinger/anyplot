""" pyplots.ai
histogram-stepwise: Step Histogram
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
import pygal
from pygal.style import Style


# Data
np.random.seed(42)
values = np.concatenate([np.random.normal(50, 10, 200), np.random.normal(80, 8, 150)])

# Compute histogram bins
counts, bin_edges = np.histogram(values, bins=25)

# Build step coordinates for pygal.XY
# Step histogram: horizontal segments at count levels, vertical connections
step_data = []
for i in range(len(counts)):
    left = bin_edges[i]
    right = bin_edges[i + 1]
    count = counts[i]
    # Horizontal segment for this bin
    step_data.append((left, count))
    step_data.append((right, count))

# Add baseline at start and end
step_data.insert(0, (bin_edges[0], 0))
step_data.append((bin_edges[-1], 0))

# Custom style for large canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998",),
    title_font_size=48,
    label_font_size=36,
    major_label_font_size=32,
    legend_font_size=32,
    value_font_size=28,
    stroke_width=4,
    opacity=1.0,
    opacity_hover=1.0,
)

# Create XY chart for step lines
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="histogram-stepwise · pygal · pyplots.ai",
    x_title="Value",
    y_title="Frequency",
    show_dots=False,
    stroke_style={"width": 4},
    fill=False,
    show_legend=False,
    show_y_guides=True,
    show_x_guides=False,
    x_label_rotation=0,
)

# Add step line data
chart.add("Distribution", step_data)

# Save outputs
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
