""" pyplots.ai
polar-line: Polar Line Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Monthly temperature variation pattern (cyclical data)
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# City A - Northern climate (cold winters, warm summers)
city_a = [2, 4, 8, 14, 19, 24, 27, 26, 21, 14, 8, 3]

# City B - Mild coastal climate (less variation)
city_b = [10, 11, 13, 15, 18, 21, 23, 23, 21, 17, 13, 11]

# Custom style for 4800x2700
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B"),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=48,
    value_font_size=36,
    stroke_width=6,
    opacity=0.9,
    opacity_hover=1.0,
)

# Create Radar chart (polar line visualization)
chart = pygal.Radar(
    width=4800,
    height=2700,
    style=custom_style,
    title="polar-line · pygal · pyplots.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=36,
    dots_size=12,
    stroke_style={"width": 6},
    fill=False,
    show_dots=True,
    inner_radius=0.2,
    margin=50,
    margin_top=120,
    margin_bottom=150,
)

# Set angular labels (months)
chart.x_labels = months

# Add temperature series
chart.add("Northern City", city_a)
chart.add("Coastal City", city_b)

# Render to files
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
