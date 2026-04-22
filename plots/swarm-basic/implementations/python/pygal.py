""" pyplots.ai
swarm-basic: Basic Swarm Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Employee performance scores by department
np.random.seed(42)
categories = ["Engineering", "Marketing", "Sales", "Operations"]
data = {
    "Engineering": np.random.normal(82, 8, 45),
    "Marketing": np.random.normal(75, 12, 50),
    "Sales": np.random.normal(78, 15, 40),
    "Operations": np.random.normal(70, 10, 55),
}

# Custom style for 4800x2700 px canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#4CAF50", "#FF5722"),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=42,
    tooltip_font_size=36,
    opacity=0.8,
    opacity_hover=1.0,
)

# Create XY chart for swarm plot
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="swarm-basic · pygal · pyplots.ai",
    x_title="Department",
    y_title="Performance Score",
    show_legend=True,
    legend_at_bottom=True,
    stroke=False,
    dots_size=12,
    show_x_guides=False,
    show_y_guides=True,
    xrange=(0, 5),
    range=(30, 120),
    margin=50,
)

# Beeswarm algorithm - spreads points horizontally to avoid overlap
# Process each category
for cat_idx, (category, values) in enumerate(data.items()):
    center_x = cat_idx + 1
    point_radius = 0.1
    spacing = 0.05

    # Sort by value to place similar values near each other
    sorted_indices = np.argsort(values)
    placed = []
    swarm_points = []

    for idx in sorted_indices:
        y = values[idx]
        x = center_x
        offset = 0
        direction = 1

        # Find non-overlapping x position
        while True:
            test_x = center_x + offset * direction
            overlap = False
            for px, py in placed:
                dist_y = abs(y - py)
                dist_x = abs(test_x - px)
                min_dist = 2 * point_radius + spacing
                if dist_y < min_dist and dist_x < min_dist:
                    overlap = True
                    break
            if not overlap:
                x = test_x
                break
            if direction == 1:
                direction = -1
            else:
                direction = 1
                offset += point_radius + spacing / 2

        placed.append((x, y))
        swarm_points.append((x, y))

    chart.add(category, swarm_points)

# Add mean markers for each category
for i, (_category, values) in enumerate(data.items()):
    center_x = i + 1
    mean_val = float(np.mean(values))
    mean_segment = [(center_x - 0.15, mean_val), (center_x + 0.15, mean_val)]
    label = "Mean" if i == 0 else None
    chart.add(label, mean_segment, stroke=True, fill=False, show_dots=False, stroke_style={"width": 8})

# Configure x-axis to show category names
chart.x_labels = ["", "Engineering", "Marketing", "Sales", "Operations", ""]
chart.x_labels_major_count = 4

# Save outputs
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
