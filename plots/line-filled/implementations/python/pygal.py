""" pyplots.ai
line-filled: Filled Line Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Monthly website traffic over a year
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
# Simulating website traffic with seasonal trend and some noise
base_traffic = 50000
seasonal = np.array([0.8, 0.85, 0.95, 1.0, 1.1, 1.15, 1.2, 1.1, 1.05, 0.95, 0.9, 1.3])  # Holiday spike in Dec
noise = np.random.normal(0, 2000, 12)
traffic = (base_traffic * seasonal + noise).astype(int)

# Custom style for large canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998",),  # Python Blue for the line/fill
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=42,
    value_font_size=36,
    stroke_width=5,
    opacity=0.4,  # Fill opacity
    opacity_hover=0.6,
)

# Create filled line chart
chart = pygal.Line(
    width=4800,
    height=2700,
    style=custom_style,
    title="line-filled · pygal · pyplots.ai",
    x_title="Month",
    y_title="Page Views",
    fill=True,  # Enable fill under the line
    show_legend=True,
    show_y_guides=True,
    show_x_guides=False,
    dots_size=8,
    stroke_style={"width": 5},
    legend_at_bottom=False,
    truncate_legend=-1,
    margin=50,
    x_label_rotation=0,
)

# Add data
chart.x_labels = months
chart.add("Website Traffic", traffic.tolist())

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
