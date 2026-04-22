""" pyplots.ai
radar-multi: Multi-Series Radar Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import pygal
from pygal.style import Style


# Data - Team performance comparison across skill dimensions
categories = ["Communication", "Technical", "Leadership", "Creativity", "Teamwork", "Problem Solving"]
teams = {
    "Alpha Team": [85, 90, 75, 80, 88, 82],
    "Beta Team": [78, 72, 85, 90, 70, 88],
    "Gamma Team": [65, 88, 70, 75, 92, 78],
}

# Custom style for 3600x3600 canvas (square for radar)
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#E74C3C"),
    title_font_size=72,
    label_font_size=42,
    major_label_font_size=36,
    legend_font_size=42,
    value_font_size=32,
    opacity=0.25,
    opacity_hover=0.5,
)

# Create radar chart
chart = pygal.Radar(
    width=3600,
    height=3600,
    style=custom_style,
    title="radar-multi · pygal · pyplots.ai",
    show_legend=True,
    legend_at_bottom=False,
    legend_box_size=30,
    dots_size=12,
    stroke_style={"width": 5},
    show_dots=True,
    fill=True,
    inner_radius=0.1,
    range=(0, 100),
)

# Set axis labels
chart.x_labels = categories

# Add data series
for team_name, values in teams.items():
    chart.add(team_name, values)

# Save outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
