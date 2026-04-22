""" pyplots.ai
circlepacking-basic: Circle Packing Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import math

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_text,
    geom_polygon,
    geom_text,
    ggplot,
    ggsize,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Hierarchical data - File system storage breakdown (GB)
np.random.seed(42)
hierarchy = [
    # Level 1: Main folders
    {"id": "Documents", "parent": "root", "value": None, "label": "Documents"},
    {"id": "Media", "parent": "root", "value": None, "label": "Media"},
    {"id": "Code", "parent": "root", "value": None, "label": "Code"},
    # Level 2: Subfolders under Documents
    {"id": "Work", "parent": "Documents", "value": 25, "label": "Work"},
    {"id": "Personal", "parent": "Documents", "value": 18, "label": "Personal"},
    {"id": "Archive", "parent": "Documents", "value": 12, "label": "Archive"},
    # Level 2: Subfolders under Media
    {"id": "Photos", "parent": "Media", "value": 45, "label": "Photos"},
    {"id": "Videos", "parent": "Media", "value": 65, "label": "Videos"},
    {"id": "Music", "parent": "Media", "value": 22, "label": "Music"},
    # Level 2: Subfolders under Code
    {"id": "Projects", "parent": "Code", "value": 35, "label": "Projects"},
    {"id": "Libraries", "parent": "Code", "value": 15, "label": "Libraries"},
    {"id": "Backups", "parent": "Code", "value": 8, "label": "Backups"},
]


def create_circle_points(cx, cy, radius, n_points=60):
    """Generate polygon points for a circle."""
    angles = np.linspace(0, 2 * np.pi, n_points, endpoint=False)
    x = cx + radius * np.cos(angles)
    y = cy + radius * np.sin(angles)
    return x.tolist(), y.tolist()


def pack_circles_in_parent(children_radii, parent_radius, parent_cx, parent_cy, iterations=500):
    """Pack circles within a parent circle using force-directed simulation."""
    n = len(children_radii)
    if n == 0:
        return [], []

    radii = np.array(children_radii)

    # Initialize in a ring around center
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    init_r = parent_radius * 0.4
    x = parent_cx + init_r * np.cos(angles)
    y = parent_cy + init_r * np.sin(angles)

    for _iteration in range(iterations):
        # Calculate repulsion between all circle pairs
        for i in range(n):
            for j in range(i + 1, n):
                dx = x[j] - x[i]
                dy = y[j] - y[i]
                dist = math.sqrt(dx * dx + dy * dy)
                min_dist = radii[i] + radii[j] + 1.0

                if dist < min_dist and dist > 0.001:
                    overlap = (min_dist - dist) / 2
                    norm_x = dx / dist
                    norm_y = dy / dist
                    x[i] -= norm_x * overlap * 0.5
                    y[i] -= norm_y * overlap * 0.5
                    x[j] += norm_x * overlap * 0.5
                    y[j] += norm_y * overlap * 0.5

        # Constrain to parent boundary
        for i in range(n):
            dx = x[i] - parent_cx
            dy = y[i] - parent_cy
            dist = math.sqrt(dx * dx + dy * dy)
            max_dist = parent_radius - radii[i] - 1.0

            if dist > max_dist and dist > 0.001:
                scale = max_dist / dist
                x[i] = parent_cx + dx * scale
                y[i] = parent_cy + dy * scale

        # Gentle attraction to center
        x = parent_cx + (x - parent_cx) * 0.998
        y = parent_cy + (y - parent_cy) * 0.998

    return x.tolist(), y.tolist()


# Calculate parent values by summing children
df = pd.DataFrame(hierarchy)
for idx, row in df[df["value"].isna()].iterrows():
    children = df[df["parent"] == row["id"]]
    df.loc[idx, "value"] = children["value"].sum()

# Root circle
root_radius = 90
root_cx, root_cy = 0, 0
total_value = df[df["parent"] == "root"]["value"].sum()

# Color scheme
colors = {
    "root": "#1a1a2e",
    "Documents": "#306998",  # Python Blue
    "Media": "#FFD43B",  # Python Yellow
    "Code": "#4CAF50",  # Green
    # Document children - blue shades
    "Work": "#4a89c2",
    "Personal": "#5a99d2",
    "Archive": "#6aa9e2",
    # Media children - yellow shades
    "Photos": "#ffe066",
    "Videos": "#ffeb99",
    "Music": "#fff0b3",
    # Code children - green shades
    "Projects": "#66bb6a",
    "Libraries": "#81c784",
    "Backups": "#a5d6a7",
}

polygon_rows = []
label_rows = []
circle_id = 0

# Draw root circle (background)
x_pts, y_pts = create_circle_points(root_cx, root_cy, root_radius)
for x, y in zip(x_pts, y_pts, strict=True):
    polygon_rows.append({"x": x, "y": y, "circle_id": circle_id, "depth": 0, "color": "root"})
circle_id += 1

# Level 1 circles
level1 = df[df["parent"] == "root"].copy()

# Calculate radii based on area proportion
level1["radius"] = np.sqrt(level1["value"] / total_value) * root_radius * 0.95

# Sort by radius descending for better packing
level1 = level1.sort_values("radius", ascending=False).reset_index(drop=True)

level1_radii = level1["radius"].tolist()
level1_x, level1_y = pack_circles_in_parent(level1_radii, root_radius, root_cx, root_cy, iterations=800)

# Store positions for level 1
level1_positions = {}
for i, (_, row) in enumerate(level1.iterrows()):
    level1_positions[row["id"]] = {"x": level1_x[i], "y": level1_y[i], "radius": row["radius"]}

    # Draw circle
    x_pts, y_pts = create_circle_points(level1_x[i], level1_y[i], row["radius"])
    for x, y in zip(x_pts, y_pts, strict=True):
        polygon_rows.append({"x": x, "y": y, "circle_id": circle_id, "depth": 1, "color": row["id"]})

    # Label at top of circle
    label_rows.append(
        {"x": level1_x[i], "y": level1_y[i] + row["radius"] * 0.65, "label": row["label"], "depth": 1, "size": 12}
    )
    circle_id += 1

# Level 2 circles (children of level 1)
for parent_id, pos in level1_positions.items():
    children = df[df["parent"] == parent_id].copy()
    if children.empty:
        continue

    # Get parent's total value for proportional sizing
    parent_value = children["value"].sum()

    # Calculate children radii to fit inside parent
    children["radius"] = np.sqrt(children["value"] / parent_value) * pos["radius"] * 0.75

    # Sort by radius descending
    children = children.sort_values("radius", ascending=False).reset_index(drop=True)

    children_radii = children["radius"].tolist()
    children_x, children_y = pack_circles_in_parent(
        children_radii, pos["radius"] * 0.92, pos["x"], pos["y"], iterations=600
    )

    for i, (_, row) in enumerate(children.iterrows()):
        # Draw circle
        x_pts, y_pts = create_circle_points(children_x[i], children_y[i], row["radius"])
        for x, y in zip(x_pts, y_pts, strict=True):
            polygon_rows.append({"x": x, "y": y, "circle_id": circle_id, "depth": 2, "color": row["id"]})

        # Label (only if circle large enough)
        if row["radius"] > 6:
            label_rows.append({"x": children_x[i], "y": children_y[i], "label": row["label"], "depth": 2, "size": 9})
        circle_id += 1

polygon_df = pd.DataFrame(polygon_rows)
label_df = pd.DataFrame(label_rows)

# Color mapping
unique_colors = polygon_df["color"].unique()
color_values = [colors.get(c, "#888888") for c in unique_colors]

# Plot
plot = (
    ggplot(polygon_df)
    + geom_polygon(aes(x="x", y="y", fill="color", group="circle_id"), color="white", size=0.8, alpha=0.92)
    + geom_text(
        aes(x="x", y="y", label="label"), data=label_df[label_df["depth"] == 1], size=12, color="white", fontface="bold"
    )
    + geom_text(aes(x="x", y="y", label="label"), data=label_df[label_df["depth"] == 2], size=9, color="#333333")
    + scale_fill_manual(values=color_values)
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=(-105, 105))
    + scale_y_continuous(limits=(-105, 105))
    + labs(title="Storage Breakdown · circlepacking-basic · letsplot · pyplots.ai")
    + ggsize(1200, 1200)  # Square format for radial chart
    + theme(
        plot_title=element_text(size=24, hjust=0.5),
        legend_position="none",
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
    )
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
