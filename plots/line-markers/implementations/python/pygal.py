""" pyplots.ai
line-markers: Line Plot with Markers
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Temperature readings over time (sparse experimental data)
np.random.seed(42)
x_values = np.arange(0, 12)  # 12 months
sensor_a = 20 + 5 * np.sin(x_values * np.pi / 6) + np.random.randn(12) * 1.5
sensor_b = 18 + 4 * np.sin(x_values * np.pi / 6 + 1) + np.random.randn(12) * 1.2
sensor_c = 22 + 3 * np.sin(x_values * np.pi / 6 + 2) + np.random.randn(12) * 1.0

months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Custom style for large canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#E74C3C"),  # Python Blue, Python Yellow, Red
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=42,
    value_font_size=36,
    stroke_width=6,
    opacity=0.9,
    opacity_hover=1.0,
    transition="400ms ease-in",
    font_family="sans-serif",
)

# Create line chart with markers
chart = pygal.Line(
    width=4800,
    height=2700,
    style=custom_style,
    title="line-markers · pygal · pyplots.ai",
    x_title="Month",
    y_title="Temperature (°C)",
    show_dots=True,
    dots_size=16,
    stroke_style={"width": 6},
    show_x_guides=False,
    show_y_guides=True,
    legend_at_bottom=False,
    legend_box_size=32,
    margin=100,
    spacing=50,
    explicit_size=True,
    truncate_legend=-1,
    x_label_rotation=0,
    show_x_labels=True,
)

# Set x-axis labels
chart.x_labels = months

# Add data series
chart.add("Sensor A", sensor_a.tolist())
chart.add("Sensor B", sensor_b.tolist())
chart.add("Sensor C", sensor_c.tolist())

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
