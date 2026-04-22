""" pyplots.ai
bar-diverging: Diverging Bar Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import pygal
from pygal.style import Style


# Data - Customer satisfaction survey scores by department
# Positive = satisfied, Negative = dissatisfied (scale -100 to +100)
departments = [
    "Customer Support",
    "Product Quality",
    "Shipping Speed",
    "Website Experience",
    "Return Process",
    "Price Value",
    "Mobile App",
    "Documentation",
    "Response Time",
    "Overall Experience",
]

# Survey scores (positive = satisfied, negative = dissatisfied)
scores = [72, 45, -23, 58, -45, 31, -12, -38, 64, 52]

# Sort by value for better pattern recognition
sorted_data = sorted(zip(departments, scores, strict=True), key=lambda x: x[1])
sorted_departments = [d[0] for d in sorted_data]
sorted_scores = [d[1] for d in sorted_data]

# Custom style for pyplots
# Using blue for positive and red/coral for negative (better contrast for diverging)
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#E07A5F"),  # Python Blue for positive, Coral for negative
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=42,
    value_font_size=36,
    value_label_font_size=36,
    tooltip_font_size=36,
)

# Create horizontal bar chart (better for long labels)
chart = pygal.HorizontalBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="Customer Satisfaction Survey · bar-diverging · pygal · pyplots.ai",
    x_title="Satisfaction Score",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
    show_x_guides=True,
    show_y_guides=False,
    print_values=True,
    print_values_position="center",
    value_formatter=lambda x: f"{x:+.0f}" if x else "",
    range=(-100, 100),
    margin=50,
    spacing=20,
)

# Add data with color based on positive/negative
# Separate positive and negative for legend clarity
positive_scores = [s if s >= 0 else None for s in sorted_scores]
negative_scores = [s if s < 0 else None for s in sorted_scores]

chart.add("Satisfied", positive_scores)
chart.add("Dissatisfied", negative_scores)

# Set category labels
chart.x_labels = sorted_departments

# Save outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
