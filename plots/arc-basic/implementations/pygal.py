"""pyplots.ai
arc-basic: Basic Arc Diagram
Library: pygal 3.1.0 | Python 3.14.3
Quality: 79/100 | Created: 2026-02-23
"""

import math

import numpy as np
import pygal
from pygal.style import Style


# Set seed for reproducibility
np.random.seed(42)

# Data: Character interactions in a story chapter
nodes = ["Alice", "Bob", "Carol", "David", "Eve", "Frank", "Grace", "Henry", "Iris", "Jack"]
n_nodes = len(nodes)

# Edges: pairs of connected nodes with weights (source, target, weight)
edges = [
    (0, 1, 3),  # Alice-Bob (strong connection)
    (0, 3, 2),  # Alice-David
    (1, 2, 2),  # Bob-Carol
    (2, 4, 1),  # Carol-Eve
    (3, 5, 2),  # David-Frank
    (4, 6, 1),  # Eve-Grace
    (0, 7, 1),  # Alice-Henry (long-range)
    (1, 5, 2),  # Bob-Frank
    (2, 3, 3),  # Carol-David (strong)
    (5, 8, 1),  # Frank-Iris
    (6, 9, 2),  # Grace-Jack
    (0, 9, 1),  # Alice-Jack (longest range)
    (3, 7, 2),  # David-Henry
    (7, 8, 1),  # Henry-Iris
    (8, 9, 2),  # Iris-Jack
]

# Node positions along x-axis (1 to 10 range)
x_positions = np.linspace(1, 10, n_nodes)
y_baseline = 0.5

# Color palette: wider range for clear weight differentiation
arc_colors = {1: "#A8D0E6", 2: "#306998", 3: "#0D2137"}

# Thickness: wider range for immediate visual distinction
arc_widths = {1: 3, 2: 8, 3: 14}

# Weight labels for tooltip context
weight_labels = {1: "Weak", 2: "Moderate", 3: "Strong"}

# Build colors tuple: one entry per edge + 3 legend entries + node series
colors = tuple(
    [arc_colors[w] for _, _, w in edges]
    + [arc_colors[3], arc_colors[2], arc_colors[1]]  # Legend entries
    + ["#FFD43B"]  # Node color
)

# Custom style — clean white background, no borders
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#306998",
    foreground_subtle="transparent",
    colors=colors,
    title_font_size=72,
    label_font_size=40,
    major_label_font_size=40,
    legend_font_size=36,
    value_font_size=32,
    stroke_width=3,
    opacity=0.7,
    opacity_hover=1.0,
)

# Create XY chart — fill=False prevents area filling under arcs
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    fill=False,
    title="Character Interactions · arc-basic · pygal · pyplots.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=24,
    x_title="",
    y_title="",
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=True,
    show_y_labels=False,
    stroke=True,
    dots_size=0,
    stroke_style={"width": 3, "linecap": "round"},
    range=(0, 4.6),
    xrange=(0, 11),
    x_labels=[{"value": float(x_positions[i]), "label": nodes[i]} for i in range(n_nodes)],
    truncate_label=-1,
    css=[
        "file://style.css",
        "inline:.plot .background {fill: white; stroke: none !important;}",
        "inline:.axis .line {stroke: none !important;}",
        "inline:.axis .guides .line {stroke: none !important;}",
        "inline:.plot .axis {stroke: none !important;}",
        "inline:.series .line {fill: none !important;}",
        # Hide edge series (1-15) and node series (19) from legend, keep weight legend (16-18)
        "inline:.legends > g:nth-child(-n+15), .legends > g:nth-child(n+19) {display: none !important;}",
    ],
    js=[],
)

# Generate arc points for each edge (empty title hides from legend)
arc_resolution = 50

for start_idx, end_idx, weight in edges:
    x_start = x_positions[start_idx]
    x_end = x_positions[end_idx]

    # Arc center and radius
    x_center = (x_start + x_end) / 2
    arc_radius = abs(x_end - x_start) / 2

    # Arc height proportional to node distance
    distance = abs(end_idx - start_idx)
    height_scale = 0.4 * distance

    # Generate arc points (semi-circle above baseline)
    arc_points = []
    for i in range(arc_resolution + 1):
        theta = math.pi * i / arc_resolution
        x = x_center - arc_radius * math.cos(theta)
        y = y_baseline + height_scale * math.sin(theta)
        arc_points.append(
            {"value": (x, y), "label": f"{nodes[start_idx]} ↔ {nodes[end_idx]} ({weight_labels[weight]})"}
        )

    # Empty title "" hides this series from the legend
    chart.add(
        "", arc_points, stroke=True, show_dots=False, stroke_style={"width": arc_widths[weight], "linecap": "round"}
    )

# Add weight legend entries (visible in legend, minimal data)
for w_val, w_label in [(3, "Strong"), (2, "Moderate"), (1, "Weak")]:
    chart.add(
        f"{w_label} connection",
        [None],
        stroke=True,
        show_dots=False,
        stroke_style={"width": arc_widths[w_val], "linecap": "round"},
    )

# Add nodes as final series (Python Yellow dots)
node_points = [
    {
        "value": (float(x_positions[i]), y_baseline),
        "label": f"{nodes[i]} ({sum(1 for s, t, _ in edges if s == i or t == i)} connections)",
    }
    for i in range(n_nodes)
]
chart.add("Characters", node_points, stroke=False, dots_size=35)

# Save outputs
chart.render_to_file("plot.svg")
chart.render_to_png("plot.png")

# Save HTML for interactive version with hover tooltips
with open("plot.html", "w") as f:
    f.write(
        """<!DOCTYPE html>
<html>
<head>
    <title>Character Interactions · arc-basic · pygal · pyplots.ai</title>
    <style>
        body { margin: 0; padding: 20px; background: #f5f5f5; font-family: sans-serif; }
        .container { max-width: 100%; margin: 0 auto; }
        object { width: 100%; height: auto; }
    </style>
</head>
<body>
    <div class="container">
        <object type="image/svg+xml" data="plot.svg">
            Arc diagram not supported
        </object>
    </div>
</body>
</html>"""
    )
