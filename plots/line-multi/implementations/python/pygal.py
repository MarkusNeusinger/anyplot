""" pyplots.ai
line-multi: Multi-Line Comparison Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import pygal
from pygal.style import Style


# Data - Monthly sales for 4 product lines over 12 months
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

electronics = [45, 52, 48, 61, 55, 67, 72, 78, 69, 85, 92, 110]
clothing = [38, 42, 51, 48, 55, 62, 58, 65, 71, 68, 75, 88]
home_goods = [28, 31, 35, 38, 42, 45, 48, 52, 49, 55, 62, 72]
sports = [22, 25, 32, 45, 58, 65, 72, 68, 55, 42, 35, 28]

# Custom style for large canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#E85D04", "#2A9D8F"),  # Python colors + colorblind-safe
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=42,
    value_font_size=36,
    stroke_width=8,
    opacity=0.9,
    opacity_hover=1.0,
)

# Create chart
chart = pygal.Line(
    width=4800,
    height=2700,
    title="line-multi \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Month",
    y_title="Sales (thousands USD)",
    style=custom_style,
    show_dots=True,
    dots_size=12,
    show_legend=True,
    legend_at_bottom=False,
    legend_box_size=36,
    x_label_rotation=0,
    show_y_guides=True,
    show_x_guides=False,
    margin=80,
    margin_top=150,
    margin_bottom=150,
    spacing=40,
)

# Add data series
chart.x_labels = months
chart.add("Electronics", electronics)
chart.add("Clothing", clothing)
chart.add("Home Goods", home_goods)
chart.add("Sports", sports)

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
