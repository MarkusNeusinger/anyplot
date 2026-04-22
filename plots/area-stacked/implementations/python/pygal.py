""" pyplots.ai
area-stacked: Stacked Area Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import pygal
from pygal.style import Style


# Data - Monthly revenue by product category over 2 years (2023-2024)
months = [
    "Jan'23",
    "Feb'23",
    "Mar'23",
    "Apr'23",
    "May'23",
    "Jun'23",
    "Jul'23",
    "Aug'23",
    "Sep'23",
    "Oct'23",
    "Nov'23",
    "Dec'23",
    "Jan'24",
    "Feb'24",
    "Mar'24",
    "Apr'24",
    "May'24",
    "Jun'24",
    "Jul'24",
    "Aug'24",
    "Sep'24",
    "Oct'24",
    "Nov'24",
    "Dec'24",
]

# Revenue in thousands ($K) - ordered from largest to smallest at bottom
electronics = [
    120,
    115,
    130,
    125,
    140,
    155,
    160,
    175,
    165,
    180,
    210,
    245,
    135,
    125,
    145,
    150,
    165,
    180,
    185,
    195,
    190,
    205,
    235,
    270,
]
clothing = [
    85,
    80,
    90,
    95,
    105,
    100,
    95,
    90,
    100,
    115,
    145,
    165,
    95,
    85,
    100,
    110,
    120,
    115,
    110,
    105,
    120,
    135,
    170,
    190,
]
home_garden = [45, 40, 55, 70, 85, 90, 95, 85, 65, 50, 45, 40, 50, 45, 60, 80, 95, 105, 110, 95, 75, 55, 50, 45]
books = [30, 35, 32, 28, 25, 22, 20, 35, 45, 40, 55, 70, 32, 38, 35, 30, 27, 24, 22, 38, 50, 45, 60, 78]

# Custom style for large canvas (4800x2700)
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    opacity=".85",
    opacity_hover=".95",
    colors=("#306998", "#FFD43B", "#2ECC71", "#E74C3C"),
    title_font_size=60,
    label_font_size=36,
    major_label_font_size=32,
    legend_font_size=40,
    value_font_size=28,
    stroke_width=2,
    font_family="sans-serif",
)

# Create stacked area chart
chart = pygal.StackedLine(
    width=4800,
    height=2700,
    style=custom_style,
    title="area-stacked · pygal · pyplots.ai",
    x_title="Month",
    y_title="Revenue ($K)",
    fill=True,
    show_y_guides=True,
    show_x_guides=False,
    x_label_rotation=45,
    legend_at_bottom=False,
    legend_box_size=30,
    truncate_legend=-1,
    show_dots=False,
    stroke_style={"width": 2},
    margin=50,
    margin_bottom=120,
    spacing=40,
)

# Add x-axis labels
chart.x_labels = months

# Add series (largest at bottom for easier reading)
chart.add("Electronics", electronics)
chart.add("Clothing", clothing)
chart.add("Home & Garden", home_garden)
chart.add("Books", books)

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
