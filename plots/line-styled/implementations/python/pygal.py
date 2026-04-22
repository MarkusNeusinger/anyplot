""" pyplots.ai
line-styled: Styled Line Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Temperature measurements from 4 different sensors over 12 months
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
base_temp = np.array([5, 7, 12, 16, 20, 24, 26, 25, 21, 15, 9, 6])

sensor_a = base_temp + np.random.randn(12) * 1.5
sensor_b = base_temp + 3 + np.random.randn(12) * 1.5
sensor_c = base_temp - 2 + np.random.randn(12) * 1.5
sensor_d = base_temp + 1.5 + np.random.randn(12) * 1.5

# Custom style for large canvas (4800x2700)
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#E74C3C", "#2ECC71"),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=42,
    value_font_size=36,
    tooltip_font_size=36,
    stroke_width=6,
    font_family="DejaVu Sans",
)

# Create line chart with different stroke styles
chart = pygal.Line(
    width=4800,
    height=2700,
    style=custom_style,
    title="line-styled · pygal · pyplots.ai",
    x_title="Month",
    y_title="Temperature (°C)",
    show_x_guides=False,
    show_y_guides=True,
    legend_at_bottom=False,
    legend_box_size=30,
    dots_size=8,
    stroke_style={"width": 6},
    show_dots=True,
    truncate_legend=-1,
    margin=50,
    margin_top=120,
    margin_bottom=100,
)

# Set x-axis labels
chart.x_labels = months

# Add series with different stroke dash arrays for line styles
# Pygal uses stroke_dasharray for line styles
chart.add("Sensor A (Solid)", sensor_a.tolist(), stroke_style={"width": 6, "dasharray": "0"})
chart.add("Sensor B (Dashed)", sensor_b.tolist(), stroke_style={"width": 6, "dasharray": "30, 15"})
chart.add("Sensor C (Dotted)", sensor_c.tolist(), stroke_style={"width": 6, "dasharray": "8, 12"})
chart.add("Sensor D (Dash-Dot)", sensor_d.tolist(), stroke_style={"width": 6, "dasharray": "30, 10, 8, 10"})

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
