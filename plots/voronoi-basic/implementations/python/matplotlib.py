""" anyplot.ai
voronoi-basic: Voronoi Diagram for Spatial Partitioning
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-17
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PolyCollection
from scipy.spatial import Voronoi


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette for Voronoi regions
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

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
        np.column_stack([x, 2 * y_min - y]),
        np.column_stack([x, 2 * y_max - y]),
        np.column_stack([2 * x_min - x, y]),
        np.column_stack([2 * x_max - x, y]),
    ]
)
vor = Voronoi(mirror_points)

# Create figure with theme-aware background
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

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
    poly_colors.append(IMPRINT[idx % len(IMPRINT)])

# Draw all Voronoi regions at once
collection = PolyCollection(polygons, facecolors=poly_colors, edgecolors=INK_SOFT, linewidths=2.5, alpha=0.6)
ax.add_collection(collection)

# Plot seed points prominently with brand green
ax.scatter(x, y, s=350, c="#009E73", edgecolors="white", linewidths=3, zorder=5)

# Set bounds and styling
ax.set_xlim(-0.2, 10.2)
ax.set_ylim(-0.2, 10.2)
ax.set_xlabel("X Coordinate", fontsize=20, color=INK)
ax.set_ylabel("Y Coordinate", fontsize=20, color=INK)
ax.set_title("voronoi-basic · matplotlib · anyplot.ai", fontsize=24, color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.set_aspect("equal")
ax.yaxis.grid(True, alpha=0.12, linewidth=0.8, color=INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
