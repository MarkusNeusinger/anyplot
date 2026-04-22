""" pyplots.ai
count-basic: Basic Count Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

from collections import Counter

import pygal
from pygal.style import Style


# Data - Survey responses from customer feedback
responses = [
    "Satisfied",
    "Very Satisfied",
    "Satisfied",
    "Neutral",
    "Dissatisfied",
    "Very Satisfied",
    "Satisfied",
    "Satisfied",
    "Very Satisfied",
    "Neutral",
    "Satisfied",
    "Neutral",
    "Very Satisfied",
    "Satisfied",
    "Very Satisfied",
    "Dissatisfied",
    "Satisfied",
    "Very Satisfied",
    "Neutral",
    "Satisfied",
    "Very Satisfied",
    "Satisfied",
    "Satisfied",
    "Very Dissatisfied",
    "Satisfied",
    "Neutral",
    "Very Satisfied",
    "Satisfied",
    "Dissatisfied",
    "Satisfied",
    "Very Satisfied",
    "Satisfied",
    "Neutral",
    "Satisfied",
    "Very Satisfied",
    "Satisfied",
    "Very Satisfied",
    "Neutral",
    "Dissatisfied",
    "Satisfied",
    "Very Satisfied",
    "Satisfied",
    "Satisfied",
    "Very Satisfied",
    "Neutral",
    "Satisfied",
    "Dissatisfied",
    "Very Satisfied",
    "Satisfied",
    "Very Satisfied",
]

# Count occurrences
counts = Counter(responses)

# Define category order (logical satisfaction order)
category_order = ["Very Dissatisfied", "Dissatisfied", "Neutral", "Satisfied", "Very Satisfied"]
ordered_counts = [(cat, counts.get(cat, 0)) for cat in category_order]

# Custom style for large canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#4B8BBE", "#FFE873", "#646464"),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=42,
    value_font_size=36,
    value_label_font_size=36,
    tooltip_font_size=36,
)

# Create chart
chart = pygal.Bar(
    width=4800,
    height=2700,
    style=custom_style,
    title="count-basic · pygal · pyplots.ai",
    x_title="Satisfaction Level",
    y_title="Count",
    show_legend=False,
    show_y_guides=True,
    show_x_guides=False,
    print_values=True,
    print_values_position="top",
    value_formatter=lambda x: str(int(x)),
    margin=60,
    spacing=80,
)

# Set x-axis labels
chart.x_labels = category_order

# Add data as single series (no legend needed for count plot)
chart.add("Responses", [count for _, count in ordered_counts])

# Save outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
