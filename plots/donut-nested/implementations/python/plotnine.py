""" pyplots.ai
donut-nested: Nested Donut Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import sys


sys.path = [p for p in sys.path if not p.endswith("implementations")]

import math  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    coord_fixed,
    element_blank,
    element_text,
    geom_polygon,
    geom_text,
    ggplot,
    labs,
    scale_fill_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


# Data - Budget allocation: departments (inner) and expense categories (outer)
# Structure: parent category -> list of (child name, value) tuples
data = {
    "Engineering": [("Salaries", 450), ("Equipment", 120), ("Training", 80)],
    "Marketing": [("Advertising", 280), ("Events", 95), ("Content", 75)],
    "Operations": [("Facilities", 180), ("IT Infrastructure", 150), ("Utilities", 70)],
    "Sales": [("Commissions", 220), ("Travel", 110), ("Tools", 50)],
}

# Color families - each parent has a base color, children get lighter shades
color_families = {
    "Engineering": ("#306998", ["#306998", "#4A83AB", "#6B9DBE"]),  # Python Blue family
    "Marketing": ("#FFD43B", ["#FFD43B", "#FFE066", "#FFEB99"]),  # Python Yellow family
    "Operations": ("#2ECC71", ["#2ECC71", "#58D68D", "#82E0A8"]),  # Green family
    "Sales": ("#E74C3C", ["#E74C3C", "#EC7063", "#F1948A"]),  # Red family
}

# Calculate totals for each parent
parent_totals = {parent: sum(v for _, v in children) for parent, children in data.items()}
grand_total = sum(parent_totals.values())

# Ring dimensions
inner_ring_inner = 60  # Inner donut hole
inner_ring_outer = 100  # Inner ring outer radius
outer_ring_inner = 110  # Outer ring inner radius (gap for separation)
outer_ring_outer = 150  # Outer ring outer radius


def create_annular_segment(start_angle, end_angle, inner_radius, outer_radius, n_points=50):
    """Create polygon points for an annular (donut) segment."""
    # Add small gap between segments
    gap = 0.02
    start_angle += gap
    end_angle -= gap

    points = []
    # Inner arc (from start to end)
    inner_angles = np.linspace(start_angle, end_angle, n_points)
    for angle in inner_angles:
        points.append((inner_radius * math.cos(angle), inner_radius * math.sin(angle)))

    # Outer arc (from end back to start)
    outer_angles = np.linspace(end_angle, start_angle, n_points)
    for angle in outer_angles:
        points.append((outer_radius * math.cos(angle), outer_radius * math.sin(angle)))

    # Close the polygon
    points.append(points[0])
    return points


# Build polygon data for inner ring (parents)
inner_rows = []
current_angle = math.pi / 2  # Start at top (12 o'clock)

parent_angles = {}  # Track start/end angles for each parent

for parent in data.keys():
    parent_total = parent_totals[parent]
    sweep = (parent_total / grand_total) * 2 * math.pi
    end_angle = current_angle - sweep  # Clockwise

    parent_angles[parent] = (current_angle, end_angle)

    # Create segment polygon
    points = create_annular_segment(end_angle, current_angle, inner_ring_inner, inner_ring_outer)

    for order, (x, y) in enumerate(points):
        inner_rows.append({"x": x, "y": y, "segment": parent, "order": order, "fill": color_families[parent][0]})

    current_angle = end_angle

inner_df = pd.DataFrame(inner_rows)

# Build polygon data for outer ring (children)
outer_rows = []

for parent, children in data.items():
    parent_start, parent_end = parent_angles[parent]
    parent_total = parent_totals[parent]

    child_current_angle = parent_start
    child_colors = color_families[parent][1]

    for i, (child_name, child_value) in enumerate(children):
        child_sweep = (child_value / parent_total) * (parent_start - parent_end)
        child_end_angle = child_current_angle - child_sweep

        # Create segment polygon
        points = create_annular_segment(child_end_angle, child_current_angle, outer_ring_inner, outer_ring_outer)

        segment_id = f"{parent}_{child_name}"
        color = child_colors[i % len(child_colors)]

        for order, (x, y) in enumerate(points):
            outer_rows.append({"x": x, "y": y, "segment": segment_id, "order": order, "fill": color})

        child_current_angle = child_end_angle

outer_df = pd.DataFrame(outer_rows)

# Create labels for inner ring (parent names)
inner_labels = []
for parent in data.keys():
    start_angle, end_angle = parent_angles[parent]
    mid_angle = (start_angle + end_angle) / 2
    label_radius = (inner_ring_inner + inner_ring_outer) / 2
    inner_labels.append(
        {
            "x": label_radius * math.cos(mid_angle),
            "y": label_radius * math.sin(mid_angle),
            "label": parent,
            "value": f"${parent_totals[parent]:,}K",
        }
    )

inner_label_df = pd.DataFrame(inner_labels)

# Create labels for outer ring (larger segments only)
outer_labels = []
for parent, children in data.items():
    parent_start, parent_end = parent_angles[parent]
    parent_total = parent_totals[parent]

    child_current_angle = parent_start

    for child_name, child_value in children:
        child_sweep = (child_value / parent_total) * (parent_start - parent_end)
        child_end_angle = child_current_angle - child_sweep

        # Only label segments that are large enough
        if child_value >= 80:  # Threshold for labeling
            mid_angle = (child_current_angle + child_end_angle) / 2
            label_radius = (outer_ring_inner + outer_ring_outer) / 2
            outer_labels.append(
                {"x": label_radius * math.cos(mid_angle), "y": label_radius * math.sin(mid_angle), "label": child_name}
            )

        child_current_angle = child_end_angle

outer_label_df = pd.DataFrame(outer_labels)

# Plot
plot = (
    ggplot()
    # Inner ring (parents)
    + geom_polygon(
        aes(x="x", y="y", group="segment", fill="fill"), data=inner_df, color="#FFFFFF", size=0.5, alpha=0.95
    )
    # Outer ring (children)
    + geom_polygon(aes(x="x", y="y", group="segment", fill="fill"), data=outer_df, color="#FFFFFF", size=0.5, alpha=0.9)
    # Inner ring labels (parent names)
    + geom_text(aes(x="x", y="y", label="label"), data=inner_label_df, size=11, fontweight="bold", color="#FFFFFF")
    # Outer ring labels (child names for large segments)
    + geom_text(aes(x="x", y="y", label="label"), data=outer_label_df, size=9, color="#333333")
    # Use fill colors directly
    + scale_fill_identity()
    # Fixed aspect ratio for proper circles
    + coord_fixed(ratio=1)
    # Axis limits with padding
    + scale_x_continuous(limits=(-180, 180))
    + scale_y_continuous(limits=(-180, 180))
    # Title
    + labs(title="Budget Allocation by Department · donut-nested · plotnine · pyplots.ai")
    # Clean theme
    + theme(
        figure_size=(12, 12),
        plot_title=element_text(size=22, ha="center"),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_blank(),
        legend_position="none",
    )
)

# Save
plot.save("plot.png", dpi=300)
