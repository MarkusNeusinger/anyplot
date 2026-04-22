""" pyplots.ai
bar-horizontal: Horizontal Bar Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import pygal
from pygal.style import Style


# Data - Programming language popularity survey results (sorted by popularity)
categories = ["Python", "JavaScript", "Java", "C++", "TypeScript", "C#", "Go", "Rust", "PHP", "Swift"]
values = [68.7, 62.3, 45.2, 38.5, 37.1, 29.8, 22.4, 18.6, 16.3, 12.9]

# Custom style for large canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998",),  # Python Blue
    title_font_size=48,
    label_font_size=32,
    major_label_font_size=28,
    legend_font_size=28,
    value_font_size=24,
    value_label_font_size=24,
    tooltip_font_size=24,
)

# Create horizontal bar chart
chart = pygal.HorizontalBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="bar-horizontal · pygal · pyplots.ai",
    x_title="Popularity (%)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    show_y_guides=True,
    show_x_guides=False,
    spacing=40,
    margin=50,
    margin_left=60,
    margin_right=60,
    margin_top=80,
    margin_bottom=150,
    print_values=True,
    print_values_position="top",
    value_formatter=lambda x: f"{x:.1f}%",
    truncate_label=-1,
    truncate_legend=-1,
)

# Add data - each category as its own series for legend display
for category, value in zip(categories, values, strict=True):
    chart.add(category, value)

# Save outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
