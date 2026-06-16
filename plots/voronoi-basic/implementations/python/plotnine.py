""" anyplot.ai
voronoi-basic: Voronoi Diagram for Spatial Partitioning
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-17
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_polygon,
    ggplot,
    labs,
    scale_fill_manual,
    theme,
)
from scipy.spatial import Voronoi


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Seed for reproducibility
np.random.seed(42)

# Generate seed points (20 points for clear visualization)
n_points = 20
x_points = np.random.uniform(1, 9, n_points)
y_points = np.random.uniform(1, 9, n_points)
points = np.column_stack([x_points, y_points])

# Define bounding box for clipping
x_min, x_max = 0, 10
y_min, y_max = 0, 10

# Add mirror points outside bounds to ensure all cells are bounded
margin = 20
mirror_points = []
for px, py in points:
    mirror_points.append([2 * x_min - margin - px, py])
    mirror_points.append([2 * x_max + margin - px, py])
    mirror_points.append([px, 2 * y_min - margin - py])
    mirror_points.append([px, 2 * y_max + margin - py])

all_points = np.vstack([points, mirror_points])

# Compute Voronoi diagram with mirrored points
vor = Voronoi(all_points)

# Build polygon dataframe for Voronoi cells
polygon_data = []

for point_idx in range(n_points):
    region_idx = vor.point_region[point_idx]
    region = vor.regions[region_idx]

    if not region or -1 in region:
        continue

    vertices = [tuple(vor.vertices[v]) for v in region]

    # Sutherland-Hodgman polygon clipping algorithm (inline)
    polygon = list(vertices)

    # Clip left edge
    clipped = []
    for i in range(len(polygon)):
        curr = polygon[i]
        prev = polygon[i - 1]
        curr_in = curr[0] >= x_min
        prev_in = prev[0] >= x_min
        if curr_in:
            if not prev_in:
                x1, y1 = prev
                x2, y2 = curr
                t = (x_min - x1) / (x2 - x1) if x2 != x1 else 0
                clipped.append((x_min, y1 + t * (y2 - y1)))
            clipped.append(curr)
        elif prev_in:
            x1, y1 = prev
            x2, y2 = curr
            t = (x_min - x1) / (x2 - x1) if x2 != x1 else 0
            clipped.append((x_min, y1 + t * (y2 - y1)))
    polygon = clipped

    # Clip right edge
    clipped = []
    for i in range(len(polygon)):
        curr = polygon[i]
        prev = polygon[i - 1]
        curr_in = curr[0] <= x_max
        prev_in = prev[0] <= x_max
        if curr_in:
            if not prev_in:
                x1, y1 = prev
                x2, y2 = curr
                t = (x_max - x1) / (x2 - x1) if x2 != x1 else 0
                clipped.append((x_max, y1 + t * (y2 - y1)))
            clipped.append(curr)
        elif prev_in:
            x1, y1 = prev
            x2, y2 = curr
            t = (x_max - x1) / (x2 - x1) if x2 != x1 else 0
            clipped.append((x_max, y1 + t * (y2 - y1)))
    polygon = clipped

    # Clip bottom edge
    clipped = []
    for i in range(len(polygon)):
        curr = polygon[i]
        prev = polygon[i - 1]
        curr_in = curr[1] >= y_min
        prev_in = prev[1] >= y_min
        if curr_in:
            if not prev_in:
                x1, y1 = prev
                x2, y2 = curr
                t = (y_min - y1) / (y2 - y1) if y2 != y1 else 0
                clipped.append((x1 + t * (x2 - x1), y_min))
            clipped.append(curr)
        elif prev_in:
            x1, y1 = prev
            x2, y2 = curr
            t = (y_min - y1) / (y2 - y1) if y2 != y1 else 0
            clipped.append((x1 + t * (x2 - x1), y_min))
    polygon = clipped

    # Clip top edge
    clipped = []
    for i in range(len(polygon)):
        curr = polygon[i]
        prev = polygon[i - 1]
        curr_in = curr[1] <= y_max
        prev_in = prev[1] <= y_max
        if curr_in:
            if not prev_in:
                x1, y1 = prev
                x2, y2 = curr
                t = (y_max - y1) / (y2 - y1) if y2 != y1 else 0
                clipped.append((x1 + t * (x2 - x1), y_max))
            clipped.append(curr)
        elif prev_in:
            x1, y1 = prev
            x2, y2 = curr
            t = (y_max - y1) / (y2 - y1) if y2 != y1 else 0
            clipped.append((x1 + t * (x2 - x1), y_max))
    polygon = clipped

    if len(polygon) < 3:
        continue

    for order, (vx, vy) in enumerate(polygon):
        polygon_data.append({"cell_id": str(point_idx), "x": vx, "y": vy, "order": order})

df_polygons = pd.DataFrame(polygon_data)

# Create dataframe for seed points
df_points = pd.DataFrame({"x": x_points, "y": y_points})

# Cell colors - diverse palette starting with Okabe-Ito positions
colors_20 = [
    "#009E73",
    "#C475FD",
    "#4467A3",
    "#BD8233",
    "#AE3030",
    "#2ABCCD",
    "#954477",
    "#306998",
    "#8DD3C7",
    "#BEBADA",
    "#FB8072",
    "#80B1D3",
    "#FDB462",
    "#B3DE69",
    "#FCCDE5",
    "#BC80BD",
    "#CCEBC5",
    "#FFED6F",
    "#A6CEE3",
    "#B2DF8A",
]

# Create the Voronoi diagram plot
plot = (
    ggplot()
    + geom_polygon(df_polygons, aes(x="x", y="y", group="cell_id", fill="cell_id"), color=INK_SOFT, size=1.0, alpha=0.7)
    + geom_point(df_points, aes(x="x", y="y"), color="#009E73", fill="#009E73", size=6, stroke=1.5, shape="o")
    + scale_fill_manual(values=colors_20)
    + coord_fixed(ratio=1.0, xlim=(x_min, x_max), ylim=(y_min, y_max))
    + labs(title="voronoi-basic · plotnine · anyplot.ai", x="X Coordinate", y="Y Coordinate")
    + theme(
        figure_size=(12, 12),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_border=element_rect(color=INK_SOFT, fill=None, size=0.5),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=24, color=INK, weight="bold", margin={"b": 20}),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        legend_position="none",
    )
)

# Save the plot
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
