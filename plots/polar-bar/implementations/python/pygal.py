""" pyplots.ai
polar-bar: Polar Bar Chart (Wind Rose)
Library: pygal 3.1.0 | Python 3.13.11
Quality: 88/100 | Created: 2025-12-30
"""

import pygal
from pygal.style import Style


# Data - Wind direction frequency (%) per category per direction
# Showing dominant westerly/northwesterly winds pattern (realistic meteorological data)
directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

# Wind speed categories with frequency percentages
calm_winds = [8, 5, 4, 3, 5, 7, 12, 11]  # 0-5 km/h
light_winds = [6, 4, 3, 2, 4, 7, 10, 9]  # 5-15 km/h
moderate_winds = [3, 2, 2, 1, 2, 4, 7, 6]  # 15-25 km/h
strong_winds = [2, 1, 1, 1, 1, 2, 4, 3]  # 25+ km/h

# Custom style for landscape canvas (4800x2700)
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#999999",
    colors=("#A6CEE3", "#5B9BD5", "#306998", "#2E5A88"),  # Light to dark blue gradient
    title_font_size=72,
    label_font_size=52,
    major_label_font_size=48,
    legend_font_size=44,
    value_font_size=40,
    stroke_width=2,
    opacity=0.9,
    opacity_hover=0.95,
)

# Create radar chart - pygal's polar visualization for wind rose
# Using stroke_fill mode for more discrete bar-like appearance
chart = pygal.Radar(
    width=4800,
    height=2700,
    style=custom_style,
    title="Wind Rose · Wind Frequency (%) by Direction · polar-bar · pygal · pyplots.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    fill=True,
    stroke=True,
    show_dots=True,
    dots_size=8,
    range=(0, 15),
    inner_radius=0.1,
    margin=120,
    spacing=60,
)

# X-axis labels (compass directions)
chart.x_labels = directions

# Add wind speed categories (layered from calm to strong)
chart.add("Calm (0-5 km/h)", calm_winds)
chart.add("Light (5-15 km/h)", light_winds)
chart.add("Moderate (15-25 km/h)", moderate_winds)
chart.add("Strong (25+ km/h)", strong_winds)

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
