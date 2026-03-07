"""pyplots.ai
bar-tornado-sensitivity: Tornado Diagram for Sensitivity Analysis
Library: pygal 3.1.0 | Python 3.14.3
Quality: 80/100 | Created: 2026-03-07
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

# Style - refined palette with prominent zero reference line
custom_style = Style(
    background="white",
    plot_background="#fafafa",
    foreground="#2d2d2d",
    foreground_strong="#1a1a1a",
    foreground_subtle="#e0e0e0",
    colors=("#E07A5F", "#4A7C96"),
    title_font_size=72,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=42,
    value_font_size=34,
    value_label_font_size=34,
    tooltip_font_size=36,
    guide_stroke_color="#e0e0e0",
    guide_stroke_dasharray="4,4",
    major_guide_stroke_color="#555555",
    major_guide_stroke_dasharray="",
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
    legend_box_size=30,
    show_x_guides=True,
    show_y_guides=False,
    y_labels_major=[0],
    print_values=True,
    print_values_position="center",
    value_formatter=lambda x: f"{x:+.1f}" if x else "",
    margin=40,
    margin_bottom=100,
    spacing=20,
    truncate_label=-1,
    rounded_bars=6,
)

chart.x_labels = sorted_params

# Use dict-based values for custom tooltips (distinctive pygal feature)
low_series = [
    {"value": v, "label": f"{p}: NPV ${base_value + v:.1f}M (base ${base_value}M)"}
    for v, p in zip(sorted_low_devs, sorted_params, strict=True)
]
high_series = [
    {"value": v, "label": f"{p}: NPV ${base_value + v:.1f}M (base ${base_value}M)"}
    for v, p in zip(sorted_high_devs, sorted_params, strict=True)
]

chart.add("Low Input Effect", low_series)
chart.add("High Input Effect", high_series)

# Save (SVG with interactive tooltips + PNG for static preview)
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
