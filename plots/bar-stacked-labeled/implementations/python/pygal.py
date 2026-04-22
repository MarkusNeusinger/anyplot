""" pyplots.ai
bar-stacked-labeled: Stacked Bar Chart with Total Labels
Library: pygal 3.1.0 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-09
"""

import pygal
from pygal.style import Style


# Data - Quarterly revenue by product category (in thousands)
# Shows diverse proportions across quarters to demonstrate stacking
categories = ["Q1", "Q2", "Q3", "Q4"]
products = {
    "Electronics": [180, 95, 140, 220],  # Variable - strong in Q4
    "Furniture": [45, 130, 85, 75],  # Peak in Q2
    "Clothing": [55, 60, 145, 90],  # Strong in Q3 (seasonal)
    "Accessories": [32, 45, 38, 115],  # Growth trend, peak in Q4
}

# Calculate totals for labels
totals = [sum(products[product][i] for product in products) for i in range(len(categories))]

# Custom style for large canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#4ECDC4", "#E74C3C"),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=42,
    value_font_size=44,
    value_label_font_size=44,
    tooltip_font_size=36,
    stroke_width=2,
)

# Create stacked bar chart
chart = pygal.StackedBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="bar-stacked-labeled · pygal · pyplots.ai",
    x_title="Quarter",
    y_title="Revenue ($K)",
    show_y_guides=True,
    show_x_guides=False,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,  # Display legend in a single row to prevent truncation
    legend_box_size=28,
    print_values=True,
    print_values_position="top",
    value_formatter=lambda x: "",  # Hide default values, use per-series formatter
    margin=80,  # Increased margin for legend space
    margin_bottom=300,  # Significantly increased for full legend visibility
    spacing=80,
    truncate_legend=-1,
    x_label_rotation=0,
    range=(0, max(totals) * 1.15),  # Extra headroom for total labels
)

# Set x-axis labels
chart.x_labels = categories

# Add data series - only show labels on the top (last) series
product_list = list(products.items())
for idx, (product, values) in enumerate(product_list):
    is_top = idx == len(product_list) - 1
    if is_top:
        # Top series: show total labels above each bar
        data = [{"value": v, "formatter": lambda x, i=i: f"Total: ${totals[i]}K"} for i, v in enumerate(values)]
    else:
        # Other series: no labels
        data = values
    chart.add(product, data)

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
