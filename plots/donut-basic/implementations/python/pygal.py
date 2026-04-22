""" pyplots.ai
donut-basic: Basic Donut Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import pygal
from pygal.style import Style


# Data - Budget allocation by department
categories = ["Engineering", "Marketing", "Sales", "Operations", "HR"]
values = [35, 25, 20, 12, 8]

# Custom style for 4800x2700 px
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#4B8BBE", "#FFE873", "#646464"),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=42,
    value_font_size=36,
    tooltip_font_size=36,
)

# Create donut chart
chart = pygal.Pie(
    width=4800,
    height=2700,
    style=custom_style,
    inner_radius=0.6,  # Creates donut hole
    title="donut-basic · pygal · pyplots.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=36,
    print_values=True,
    print_values_position="call",
    value_formatter=lambda x: f"{x}%",
)

# Add data with percentage labels
for category, value in zip(categories, values, strict=True):
    chart.add(category, value)

# Save outputs
chart.render_to_file("plot.svg")
chart.render_to_png("plot.png")

# Also save HTML for interactive version
chart.render_to_file("plot.html")
