""" pyplots.ai
polar-bar: Polar Bar Chart (Wind Rose)
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_text,
    geom_path,
    geom_polygon,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


# Data - Wind direction frequencies (8 compass directions)
np.random.seed(42)
directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
direction_angles = [0, 45, 90, 135, 180, 225, 270, 315]  # Degrees from North, clockwise
frequencies = [15, 8, 12, 5, 18, 22, 10, 7]

# Create polygons for each bar (wedge shape)
# Each bar spans ±22.5 degrees (45 degrees total width for 8 directions)
bar_half_width = 18  # degrees, slightly less than 22.5 for visual gap
bar_rows = []
bar_id = 0

for direction, angle, freq in zip(directions, direction_angles, frequencies, strict=True):
    # Create wedge polygon points (from center outward)
    # Start angle and end angle
    start_angle = angle - bar_half_width
    end_angle = angle + bar_half_width

    # Create polygon vertices: center -> arc at radius -> back to center
    # Convert to math convention: 0° at East, CCW positive
    # Polar convention: 0° at North (top), CW positive

    # Center point
    points = [(0, 0)]

    # Arc points at the outer radius
    arc_angles = np.linspace(start_angle, end_angle, 10)
    for a in arc_angles:
        # Convert from compass (N=0, CW) to math (E=0, CCW)
        theta = np.radians(90 - a)
        x = freq * np.cos(theta)
        y = freq * np.sin(theta)
        points.append((x, y))

    # Close back to center
    points.append((0, 0))

    # Add all points to dataframe
    for i, (x, y) in enumerate(points):
        bar_rows.append({"x": x, "y": y, "direction": direction, "bar_id": bar_id, "order": i})

    bar_id += 1

bar_df = pd.DataFrame(bar_rows)

# Create circular gridlines (concentric circles at magnitude intervals)
grid_rows = []
grid_angles = np.linspace(0, 2 * np.pi, 101)
max_radius = max(frequencies) + 5
grid_radii = [5, 10, 15, 20, 25]

for radius in grid_radii:
    if radius <= max_radius:
        for angle in grid_angles:
            grid_rows.append({"x": radius * np.cos(angle), "y": radius * np.sin(angle), "radius": radius})

grid_df = pd.DataFrame(grid_rows)

# Create radial spokes (8 compass directions)
spoke_rows = []
for deg in direction_angles:
    angle = np.radians(90 - deg)
    spoke_rows.append(
        {"x1": 0, "y1": 0, "x2": (max_radius + 2) * np.cos(angle), "y2": (max_radius + 2) * np.sin(angle)}
    )

spoke_df = pd.DataFrame(spoke_rows)

# Create compass direction labels
label_rows = []
label_radius = max_radius + 5
for deg, lbl in zip(direction_angles, directions, strict=True):
    angle = np.radians(90 - deg)
    label_rows.append({"label": lbl, "x": label_radius * np.cos(angle), "y": label_radius * np.sin(angle)})

label_df = pd.DataFrame(label_rows)

# Create radius labels (frequency values) - positioned along NNE axis
radius_labels = []
label_angle = np.radians(90 - 22.5)  # NNE direction
for r in [5, 10, 15, 20]:
    if r <= max_radius:
        radius_labels.append({"label": f"{r}", "x": r * np.cos(label_angle) + 1.5, "y": r * np.sin(label_angle)})

radius_label_df = pd.DataFrame(radius_labels)

# Color palette - alternating Python Blue and Yellow
colors = {
    "N": "#306998",
    "NE": "#FFD43B",
    "E": "#306998",
    "SE": "#FFD43B",
    "S": "#306998",
    "SW": "#FFD43B",
    "W": "#306998",
    "NW": "#FFD43B",
}

# Plot
plot = (
    ggplot()
    # Circular gridlines (frequency circles)
    + geom_path(
        aes(x="x", y="y", group="radius"), data=grid_df, color="#CCCCCC", size=0.5, alpha=0.5, linetype="dashed"
    )
    # Radial spokes (direction lines)
    + geom_segment(aes(x="x1", y="y1", xend="x2", yend="y2"), data=spoke_df, color="#CCCCCC", size=0.5, alpha=0.5)
    # Bar wedges (wind rose bars)
    + geom_polygon(
        aes(x="x", y="y", group="bar_id", fill="direction"),
        data=bar_df,
        color="#333333",
        size=0.5,
        alpha=0.85,
        show_legend=False,
    )
    # Compass direction labels
    + geom_text(aes(x="x", y="y", label="label"), data=label_df, size=16, color="#333333", fontweight="bold")
    # Frequency labels
    + geom_text(aes(x="x", y="y", label="label"), data=radius_label_df, size=10, color="#666666", ha="left")
    # Custom colors for directions
    + scale_fill_manual(values=colors)
    # Equal coordinate system for proper circles
    + coord_fixed(ratio=1)
    # Axis scaling with padding
    + scale_x_continuous(limits=(-35, 35))
    + scale_y_continuous(limits=(-35, 35))
    # Title
    + labs(title="Wind Direction Frequency · polar-bar · plotnine · pyplots.ai")
    # Clean polar-style theme
    + theme(
        figure_size=(12, 12),
        plot_title=element_text(size=24, ha="center"),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_blank(),
        plot_background=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
