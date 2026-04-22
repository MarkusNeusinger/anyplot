# ruff: noqa: F405
"""pyplots.ai
voronoi-basic: Voronoi Diagram for Spatial Partitioning
Library: lets-plot | Python 3.13
Quality: pending | Created: 2025-01-09
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from scipy.spatial import Voronoi


LetsPlot.setup_html()

# Data - Generate seed points for spatial partitioning
np.random.seed(42)
n_points = 20

# Generate clustered seed points representing facility locations
x = np.concatenate([np.random.normal(25, 8, n_points // 2), np.random.normal(75, 8, n_points // 2)])
y = np.concatenate([np.random.normal(40, 10, n_points // 2), np.random.normal(60, 10, n_points // 2)])

# Define bounding box for clipping
x_min, x_max = 0, 100
y_min, y_max = 0, 100

# Add boundary points to ensure all regions are clipped
boundary_margin = 200
boundary_points = np.array(
    [
        [x_min - boundary_margin, y_min - boundary_margin],
        [x_min - boundary_margin, y_max + boundary_margin],
        [x_max + boundary_margin, y_min - boundary_margin],
        [x_max + boundary_margin, y_max + boundary_margin],
    ]
)

# Combine seed points with boundary points
all_points = np.column_stack([x, y])
points_with_boundary = np.vstack([all_points, boundary_points])

# Compute Voronoi tessellation
vor = Voronoi(points_with_boundary)

# Build polygon data for each Voronoi region using Sutherland-Hodgman clipping
polygon_data = []
for idx, region_idx in enumerate(vor.point_region[: len(all_points)]):
    region = vor.regions[region_idx]
    if not region or -1 in region:
        continue

    # Get vertices for this region
    vertices = [list(vor.vertices[i]) for i in region]

    # Sutherland-Hodgman polygon clipping to bounding box
    output = vertices
    for edge in ["left", "right", "bottom", "top"]:
        if len(output) == 0:
            break
        input_list = output
        output = []
        for i in range(len(input_list)):
            current = input_list[i]
            previous = input_list[i - 1]

            # Check if point is inside this edge
            if edge == "left":
                curr_inside = current[0] >= x_min
                prev_inside = previous[0] >= x_min
            elif edge == "right":
                curr_inside = current[0] <= x_max
                prev_inside = previous[0] <= x_max
            elif edge == "bottom":
                curr_inside = current[1] >= y_min
                prev_inside = previous[1] >= y_min
            else:  # top
                curr_inside = current[1] <= y_max
                prev_inside = previous[1] <= y_max

            # Compute intersection if crossing edge
            if curr_inside != prev_inside:
                x1, y1 = previous
                x2, y2 = current
                if edge == "left":
                    t = (x_min - x1) / (x2 - x1) if x2 != x1 else 0
                    ix, iy = x_min, y1 + t * (y2 - y1)
                elif edge == "right":
                    t = (x_max - x1) / (x2 - x1) if x2 != x1 else 0
                    ix, iy = x_max, y1 + t * (y2 - y1)
                elif edge == "bottom":
                    t = (y_min - y1) / (y2 - y1) if y2 != y1 else 0
                    ix, iy = x1 + t * (x2 - x1), y_min
                else:  # top
                    t = (y_max - y1) / (y2 - y1) if y2 != y1 else 0
                    ix, iy = x1 + t * (x2 - x1), y_max
                output.append([ix, iy])

            if curr_inside:
                output.append(current)

    # Add clipped polygon vertices to data
    if len(output) >= 3:
        for vx, vy in output:
            polygon_data.append({"x": vx, "y": vy, "region": f"Region {idx + 1}"})

df_polygons = pd.DataFrame(polygon_data)

# Create seed points dataframe
df_seeds = pd.DataFrame({"x": x, "y": y, "label": [f"P{i + 1}" for i in range(len(x))]})

# Color palette for regions - starting with Python colors, then colorblind-safe additions
colors = [
    "#306998",
    "#FFD43B",
    "#4ECDC4",
    "#FF6B6B",
    "#45B7D1",
    "#96CEB4",
    "#FFEAA7",
    "#DDA0DD",
    "#98D8C8",
    "#F7DC6F",
    "#BB8FCE",
    "#85C1E9",
    "#F8B500",
    "#00CED1",
    "#FF7F50",
    "#9370DB",
    "#20B2AA",
    "#FFB6C1",
    "#87CEEB",
    "#DEB887",
]

# Build plot with Voronoi cells and seed points
plot = (
    ggplot()
    + geom_polygon(data=df_polygons, mapping=aes(x="x", y="y", fill="region"), color="white", size=1.5, alpha=0.7)
    + geom_point(data=df_seeds, mapping=aes(x="x", y="y"), color="#1a1a1a", size=6)
    + geom_point(data=df_seeds, mapping=aes(x="x", y="y"), color="white", size=3)
    + scale_fill_manual(values=colors)
    + coord_fixed(xlim=[x_min, x_max], ylim=[y_min, y_max])
    + labs(x="X Coordinate", y="Y Coordinate", title="voronoi-basic · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_position="none",
    )
    + ggsize(1600, 900)
)

# Save outputs to current directory
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
