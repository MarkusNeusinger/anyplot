""" pyplots.ai
bar-grouped: Grouped Bar Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-24
"""

import pygal
from pygal.style import Style


# Data: Quarterly Revenue by Product Line (in $M)
categories = ["Q1", "Q2", "Q3", "Q4"]
products = {"Software": [4.2, 5.1, 4.8, 6.3], "Hardware": [3.1, 2.8, 3.5, 4.0], "Services": [2.5, 3.2, 3.8, 4.2]}

# Custom style for large canvas (4800x2700)
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#FF6B6B", "#4ECDC4"),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=42,
    value_font_size=36,
    stroke_width=2,
    opacity=0.9,
    opacity_hover=1.0,
)

# Create grouped bar chart
chart = pygal.Bar(
    width=4800,
    height=2700,
    style=custom_style,
    title="bar-grouped · pygal · pyplots.ai",
    x_title="Quarter",
    y_title="Revenue ($M)",
    show_y_guides=True,
    show_x_guides=False,
    legend_at_bottom=False,
    legend_box_size=36,
    margin=80,
    spacing=60,
    print_values=True,
    print_values_position="top",
    value_formatter=lambda x: f"${x:.1f}M",
)

# Set x-axis labels
chart.x_labels = categories

# Add data series
for product, values in products.items():
    chart.add(product, values)

# Save outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
