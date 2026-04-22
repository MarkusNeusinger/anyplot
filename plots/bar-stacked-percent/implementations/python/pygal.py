""" pyplots.ai
bar-stacked-percent: 100% Stacked Bar Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import pygal
from pygal.style import Style


# Data: Energy mix by country (% of total energy production)
countries = ["USA", "Germany", "China", "Brazil", "Japan", "India"]

# Energy sources (values will be normalized to 100%)
fossil = [78, 52, 85, 18, 88, 75]
nuclear = [8, 6, 5, 1, 4, 2]
renewable = [14, 42, 10, 81, 8, 23]

# Custom style for large canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#4CAF50"),  # Python Blue, Python Yellow, Green
    title_font_size=60,
    label_font_size=40,
    major_label_font_size=36,
    legend_font_size=36,
    value_font_size=28,
    value_label_font_size=28,
    tooltip_font_size=28,
)

# Create 100% stacked bar chart
chart = pygal.StackedBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="bar-stacked-percent · pygal · pyplots.ai",
    x_title="Country",
    y_title="Percentage (%)",
    show_y_guides=True,
    show_x_guides=False,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    print_values=True,
    print_values_position="center",
    value_formatter=lambda x: f"{x:.0f}%",
    margin=50,
    spacing=30,
)

# Normalize data to percentages (100% stacked)
percentages_fossil = []
percentages_nuclear = []
percentages_renewable = []

for i in range(len(countries)):
    total = fossil[i] + nuclear[i] + renewable[i]
    percentages_fossil.append(round(fossil[i] / total * 100, 1))
    percentages_nuclear.append(round(nuclear[i] / total * 100, 1))
    percentages_renewable.append(round(renewable[i] / total * 100, 1))

# Add data series
chart.x_labels = countries
chart.add("Fossil Fuels", percentages_fossil)
chart.add("Nuclear", percentages_nuclear)
chart.add("Renewable", percentages_renewable)

# Set y-axis range to 0-100 for percentage scale
chart.range = (0, 100)

# Save outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
