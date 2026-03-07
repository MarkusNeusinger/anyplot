"""pyplots.ai
bar-tornado-sensitivity: Tornado Diagram for Sensitivity Analysis
Library: pygal | Python 3.13
Quality: pending | Created: 2026-03-07
"""

import pygal
from pygal.style import Style


# Data - NPV sensitivity analysis for a capital investment project
# Base case NPV = $2.5M; each parameter varied between low and high scenarios
parameters = [
    "Discount Rate",
    "Revenue Growth",
    "Material Cost",
    "Labor Cost",
    "Tax Rate",
    "Salvage Value",
    "Initial Investment",
    "Operating Margin",
    "Inflation Rate",
]
base_value = 2.5  # $2.5M base case NPV

low_values = [3.8, 1.6, 2.9, 2.7, 2.9, 2.3, 2.8, 1.9, 2.3]
high_values = [1.4, 3.6, 2.0, 2.2, 2.1, 2.7, 2.2, 3.2, 2.6]

# Compute deviations from base and sort by total range (widest first)
deviations = []
for i, param in enumerate(parameters):
    low_dev = low_values[i] - base_value
    high_dev = high_values[i] - base_value
    total_range = abs(high_values[i] - low_values[i])
    deviations.append((param, low_dev, high_dev, total_range))

deviations.sort(key=lambda x: x[3], reverse=False)  # Ascending for pygal (bottom-to-top)

sorted_params = [d[0] for d in deviations]
sorted_low_devs = [d[1] for d in deviations]
sorted_high_devs = [d[2] for d in deviations]

# Style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#cccccc",
    colors=("#E07A5F", "#306998"),
    title_font_size=72,
    label_font_size=44,
    major_label_font_size=40,
    legend_font_size=44,
    value_font_size=34,
    value_label_font_size=34,
    tooltip_font_size=36,
)

# Plot
chart = pygal.HorizontalStackedBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="NPV Sensitivity Analysis · bar-tornado-sensitivity · pygal · pyplots.ai",
    x_title="Change in NPV ($M)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
    show_x_guides=True,
    show_y_guides=False,
    print_values=True,
    print_values_position="center",
    value_formatter=lambda x: f"{x:+.1f}" if x else "",
    margin=50,
    spacing=18,
    truncate_label=-1,
)

chart.x_labels = sorted_params
chart.add("Low Scenario", sorted_low_devs)
chart.add("High Scenario", sorted_high_devs)

# Save
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
