""" pyplots.ai
voronoi-basic: Voronoi Diagram for Spatial Partitioning
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PolyCollection
from scipy.spatial import Voronoi


# Data - Generate seed points for Voronoi diagram
np.random.seed(42)
n_points = 15
x = np.random.uniform(1, 9, n_points)
y = np.random.uniform(1, 9, n_points)
points = np.column_stack([x, y])

# Create Voronoi tessellation with mirror points for bounded regions
# Add mirror points outside the boundary to ensure all regions are finite
x_min, x_max, y_min, y_max = 0, 10, 0, 10
mirror_points = np.vstack(
    [
        points,
        np.column_stack([x, 2 * y_min - y]),  # Bottom mirror
        np.column_stack([x, 2 * y_max - y]),  # Top mirror
        np.column_stack([2 * x_min - x, y]),  # Left mirror
        np.column_stack([2 * x_max - x, y]),  # Right mirror
    ]
)
vor = Voronoi(mirror_points)

# Define colorblind-safe colors for Voronoi regions
colors = [
    "#306998",
    "#FFD43B",
    "#4ECDC4",
    "#FF6B6B",
    "#95E1D3",
    "#F38181",
    "#AA96DA",
    "#FCBAD3",
    "#A8D8EA",
    "#FFDAC1",
    "#E2F0CB",
    "#B5EAD7",
    "#C7CEEA",
    "#FFB7B2",
    "#957DAD",
]

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Collect polygons for original points only (first n_points)
polygons = []
poly_colors = []

for idx in range(n_points):
    region_idx = vor.point_region[idx]
    region = vor.regions[region_idx]

    if not region or -1 in region:
        continue

    # Get polygon vertices
    polygon = np.array([vor.vertices[v] for v in region])

    # Clip polygon to bounding box
    polygon[:, 0] = np.clip(polygon[:, 0], x_min, x_max)
    polygon[:, 1] = np.clip(polygon[:, 1], y_min, y_max)

    polygons.append(polygon)
    poly_colors.append(colors[idx % len(colors)])

# Draw all Voronoi regions at once
collection = PolyCollection(polygons, facecolors=poly_colors, edgecolors="#333333", linewidths=2.5, alpha=0.6)
ax.add_collection(collection)

# Plot seed points prominently
ax.scatter(x, y, s=350, c="#306998", edgecolors="white", linewidths=3, zorder=5)

# Set bounds and styling
ax.set_xlim(-0.2, 10.2)
ax.set_ylim(-0.2, 10.2)
ax.set_xlabel("X Coordinate", fontsize=20)
ax.set_ylabel("Y Coordinate", fontsize=20)
ax.set_title("voronoi-basic · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.set_aspect("equal")
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
