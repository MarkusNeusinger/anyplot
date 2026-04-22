""" pyplots.ai
line-basic: Basic Line Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import pygal
from pygal.style import Style


# Data - Monthly average temperatures (°C) for a temperate climate
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
temperatures = [2.3, 3.5, 7.2, 11.8, 16.4, 19.8, 22.1, 21.5, 17.6, 12.3, 7.1, 3.4]

# Custom style for 4800x2700 canvas
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

# Create line chart
chart = pygal.Line(
    width=4800,
    height=2700,
    title="line-basic · pygal · pyplots.ai",
    x_title="Month",
    y_title="Temperature (°C)",
    style=custom_style,
    show_dots=True,
    dots_size=8,
    stroke_style={"width": 5},
    show_y_guides=True,
    show_x_guides=False,
    x_label_rotation=0,
    legend_at_bottom=True,
    truncate_legend=-1,
)

# Add data
chart.x_labels = months
chart.add("Average Temperature", temperatures)

# Save outputs
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
