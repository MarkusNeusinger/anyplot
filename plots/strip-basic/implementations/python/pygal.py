""" pyplots.ai
strip-basic: Basic Strip Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import random

import pygal
from pygal.style import Style


# Set seed for reproducibility
random.seed(42)

# Data - Survey response scores by department
categories = ["Engineering", "Marketing", "Sales", "Support"]
n_per_category = 40

# Generate realistic survey scores (1-10 scale) with different distributions
data = {
    "Engineering": [random.gauss(7.5, 1.2) for _ in range(n_per_category)],
    "Marketing": [random.gauss(6.8, 1.5) for _ in range(n_per_category)],
    "Sales": [random.gauss(7.2, 1.0) for _ in range(n_per_category)],
    "Support": [random.gauss(6.5, 1.8) for _ in range(n_per_category)],
}

# Clip values to realistic 1-10 range
for cat in data:
    data[cat] = [max(1, min(10, v)) for v in data[cat]]

# Custom style for 4800x2700 output
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#4B8BBE", "#FFE873"),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=42,
    value_font_size=36,
    opacity=0.65,
    stroke_width=0,
)

# Create XY chart for strip plot
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="strip-basic · pygal · pyplots.ai",
    x_title="Department",
    y_title="Survey Score",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    show_x_guides=False,
    show_y_guides=True,
    stroke=False,
    dots_size=12,
    x_label_rotation=0,
)

# Set x-axis range and labels
chart.x_labels = ["", "Engineering", "Marketing", "Sales", "Support", ""]
chart.xrange = (0, 5)

# Add jittered points for each category
for i, cat in enumerate(categories, start=1):
    # Create jittered x-positions around the category index
    points = [(i + random.uniform(-0.25, 0.25), val) for val in data[cat]]
    chart.add(cat, points)

# Save outputs
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
