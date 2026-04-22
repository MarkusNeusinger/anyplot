""" pyplots.ai
voronoi-basic: Voronoi Diagram for Spatial Partitioning
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
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
# This creates finite Voronoi regions for points near edges
margin = 20
mirror_points = []
for px, py in points:
    mirror_points.append([2 * x_min - margin - px, py])  # Left mirror
    mirror_points.append([2 * x_max + margin - px, py])  # Right mirror
    mirror_points.append([px, 2 * y_min - margin - py])  # Bottom mirror
    mirror_points.append([px, 2 * y_max + margin - py])  # Top mirror

all_points = np.vstack([points, mirror_points])

# Compute Voronoi diagram with mirrored points
vor = Voronoi(all_points)


# Sutherland-Hodgman polygon clipping algorithm
def clip_polygon(vertices, x_min, x_max, y_min, y_max):
    """Clip polygon to bounding box."""

    def inside_left(p):
        return p[0] >= x_min

    def inside_right(p):
        return p[0] <= x_max

    def inside_bottom(p):
        return p[1] >= y_min

    def inside_top(p):
        return p[1] <= y_max

    def intersect(p1, p2, edge):
        x1, y1 = p1
        x2, y2 = p2
        if edge == "left":
            if x2 == x1:
                return (x_min, y1)
            t = (x_min - x1) / (x2 - x1)
            return (x_min, y1 + t * (y2 - y1))
        elif edge == "right":
            if x2 == x1:
                return (x_max, y1)
            t = (x_max - x1) / (x2 - x1)
            return (x_max, y1 + t * (y2 - y1))
        elif edge == "bottom":
            if y2 == y1:
                return (x1, y_min)
            t = (y_min - y1) / (y2 - y1)
            return (x1 + t * (x2 - x1), y_min)
        else:  # top
            if y2 == y1:
                return (x1, y_max)
            t = (y_max - y1) / (y2 - y1)
            return (x1 + t * (x2 - x1), y_max)

    def clip_edge(polygon, inside_fn, edge):
        if not polygon:
            return []
        clipped = []
        for i in range(len(polygon)):
            curr = polygon[i]
            prev = polygon[i - 1]
            curr_in = inside_fn(curr)
            prev_in = inside_fn(prev)
            if curr_in:
                if not prev_in:
                    clipped.append(intersect(prev, curr, edge))
                clipped.append(curr)
            elif prev_in:
                clipped.append(intersect(prev, curr, edge))
        return clipped

    polygon = list(vertices)
    polygon = clip_edge(polygon, inside_left, "left")
    polygon = clip_edge(polygon, inside_right, "right")
    polygon = clip_edge(polygon, inside_bottom, "bottom")
    polygon = clip_edge(polygon, inside_top, "top")
    return polygon


# Build polygon dataframe for Voronoi cells (only for original points)
polygon_data = []

for point_idx in range(n_points):  # Only process original points, not mirrors
    region_idx = vor.point_region[point_idx]
    region = vor.regions[region_idx]

    # Skip empty regions
    if not region or -1 in region:
        continue

    # Get vertices for this region
    vertices = [tuple(vor.vertices[v]) for v in region]

    # Clip to bounding box
    clipped = clip_polygon(vertices, x_min, x_max, y_min, y_max)

    if len(clipped) < 3:
        continue

    # Add vertices to dataframe
    for order, (vx, vy) in enumerate(clipped):
        polygon_data.append({"cell_id": str(point_idx), "x": vx, "y": vy, "order": order})

df_polygons = pd.DataFrame(polygon_data)

# Create dataframe for seed points
df_points = pd.DataFrame({"x": x_points, "y": y_points})

# Define colorblind-friendly palette with enough colors for all cells
colors_20 = [
    "#306998",  # Python Blue
    "#FFD43B",  # Python Yellow
    "#E69F00",  # Orange
    "#56B4E9",  # Sky Blue
    "#009E73",  # Bluish Green
    "#F0E442",  # Yellow
    "#0072B2",  # Blue
    "#D55E00",  # Vermillion
    "#CC79A7",  # Reddish Purple
    "#999999",  # Gray
    "#8DD3C7",  # Mint
    "#BEBADA",  # Lavender
    "#FB8072",  # Salmon
    "#80B1D3",  # Light Blue
    "#FDB462",  # Light Orange
    "#B3DE69",  # Light Green
    "#FCCDE5",  # Pink
    "#BC80BD",  # Purple
    "#CCEBC5",  # Pale Green
    "#FFED6F",  # Light Yellow
]

# Create the Voronoi diagram plot
plot = (
    ggplot()
    # Voronoi cells with colors
    + geom_polygon(
        df_polygons, aes(x="x", y="y", group="cell_id", fill="cell_id"), color="#333333", size=1.0, alpha=0.7
    )
    # Seed points with Python branding colors
    + geom_point(df_points, aes(x="x", y="y"), color="#306998", fill="#FFD43B", size=6, stroke=2, shape="o")
    + scale_fill_manual(values=colors_20)
    + coord_fixed(ratio=1.0, xlim=(x_min, x_max), ylim=(y_min, y_max))
    + labs(title="voronoi-basic · plotnine · pyplots.ai", x="X Coordinate", y="Y Coordinate")
    + theme(
        figure_size=(12, 12),
        plot_title=element_text(size=28, ha="center", weight="bold", margin={"b": 20}),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_background=element_rect(fill="#fafafa"),
        plot_background=element_rect(fill="white"),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        legend_position="none",
    )
)

# Save the plot
plot.save("plot.png", dpi=300, verbose=False)
