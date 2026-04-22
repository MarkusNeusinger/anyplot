""" pyplots.ai
pyramid-basic: Basic Pyramid Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-23
"""

import pygal
from pygal.style import Style


# Data - Population pyramid showing age distribution by gender (US 2023 estimates)
age_groups = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]
male = [4.8, 5.2, 6.1, 7.3, 8.5, 7.8, 5.9, 3.2, 1.2]  # Millions
female = [4.5, 5.0, 6.3, 7.5, 8.7, 8.2, 6.4, 4.1, 2.1]  # Millions

# Custom style for 4800x2700 canvas with larger legend text
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333",
    foreground_strong="#333",
    foreground_subtle="#666",
    colors=("#FFD43B", "#306998"),  # Yellow for Female (right), Blue for Male (left)
    title_font_size=60,
    label_font_size=40,
    major_label_font_size=36,
    legend_font_size=48,  # Larger legend for better readability
    value_font_size=28,
    stroke_width=1,
)

# Create pyramid chart - pygal's native chart type for population pyramids
chart = pygal.Pyramid(
    width=4800,
    height=2700,
    style=custom_style,
    title="pyramid-basic · pygal · pyplots.ai",
    x_title="Population (millions)",
    y_title="Age Group",
    show_y_guides=True,
    show_x_guides=False,
    print_values=False,
    legend_at_bottom=True,  # Position legend at bottom for better visibility
    legend_box_size=24,
    show_legend=True,
    human_readable=True,
)

# Set category labels (age groups)
chart.x_labels = age_groups

# Add data series - pygal Pyramid: first series goes RIGHT, second goes LEFT
# Female (right), Male (left) following demographic convention
chart.add("Female", female)
chart.add("Male", male)

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
