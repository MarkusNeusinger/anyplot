""" pyplots.ai
radar-basic: Basic Radar Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import pygal
from pygal.style import Style


# Data - Employee performance comparison across competencies
categories = ["Communication", "Technical Skills", "Teamwork", "Problem Solving", "Leadership", "Creativity"]

# Two employees for comparison (0-100 scale)
employee_a = [85, 92, 78, 88, 72, 80]
employee_b = [75, 68, 90, 82, 85, 78]

# Custom style for 4800x2700 px canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B"),
    title_font_size=48,
    label_font_size=32,
    major_label_font_size=28,
    legend_font_size=32,
    value_font_size=24,
    opacity=0.25,
    opacity_hover=0.5,
)

# Create radar chart
chart = pygal.Radar(
    width=4800,
    height=2700,
    style=custom_style,
    title="radar-basic · pygal · pyplots.ai",
    show_legend=True,
    legend_at_bottom=False,
    fill=True,
    dots_size=8,
    stroke_style={"width": 4},
    show_y_guides=True,
    y_labels_major_every=2,
)

# Set axis labels
chart.x_labels = categories

# Add data series
chart.add("Employee A", employee_a)
chart.add("Employee B", employee_b)

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
