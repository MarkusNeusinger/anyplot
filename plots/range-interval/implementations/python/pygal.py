""" pyplots.ai
range-interval: Range Interval Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import pygal
from pygal.style import Style


# Data: Monthly temperature ranges (daily high/low averages)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
temp_min = [-2, 0, 4, 8, 13, 17, 19, 18, 14, 9, 4, 0]  # Average daily lows (°C)
temp_max = [6, 8, 12, 16, 21, 25, 28, 27, 22, 16, 10, 7]  # Average daily highs (°C)

# Calculate the range (difference) for the visible portion
temp_range = [high - low for low, high in zip(temp_min, temp_max, strict=True)]

# Custom style for large canvas
# The base (transparent) color needs to be invisible
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("rgba(0, 0, 0, 0)", "#306998"),  # First series invisible, second visible
    title_font_size=56,
    label_font_size=36,
    major_label_font_size=32,
    legend_font_size=36,
    value_font_size=28,
    tooltip_font_size=24,
    opacity=1.0,
    opacity_hover=1.0,
)

# Create stacked bar chart - first bar is invisible base, second is visible range
chart = pygal.StackedBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="range-interval · pygal · pyplots.ai",
    x_title="Month",
    y_title="Temperature (°C)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
    show_y_guides=True,
    show_x_guides=False,
    print_values=False,
    spacing=40,
    margin=80,
    margin_bottom=150,
    margin_left=150,
    truncate_legend=-1,
)

# Set x-axis labels
chart.x_labels = months

# Add invisible base (from 0 to min_value) - hidden from legend
chart.add("", temp_min, show_dots=False)

# Add visible range bars (from min to max)
chart.add("Temperature Range (°C)", temp_range)

# Render to PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
