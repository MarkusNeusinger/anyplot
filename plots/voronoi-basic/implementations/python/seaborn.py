""" pyplots.ai
voronoi-basic: Voronoi Diagram for Spatial Partitioning
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Polygon
from scipy.spatial import Voronoi


# Data - generate seed points for store locations
np.random.seed(42)
n_points = 20
x = np.random.uniform(10, 90, n_points)
y = np.random.uniform(10, 90, n_points)
points = np.column_stack([x, y])

# Bounding box
bbox = [0, 100, 0, 100]  # xmin, xmax, ymin, ymax

# Add mirror points outside bounding box to handle infinite regions
margin = 200
mirror_points = []
for px, py in points:
    mirror_points.append([px, -margin])  # bottom
    mirror_points.append([px, 100 + margin])  # top
    mirror_points.append([-margin, py])  # left
    mirror_points.append([100 + margin, py])  # right
all_points = np.vstack([points, mirror_points])

# Compute Voronoi tessellation with mirror points
vor = Voronoi(all_points)

# Create figure with seaborn styling
sns.set_style("white")
sns.set_context("talk", font_scale=1.2)
fig, ax = plt.subplots(figsize=(16, 9))

# Color palette for regions
colors = sns.color_palette("husl", n_points)

# Draw Voronoi regions (only for original points, not mirrors)
for i in range(n_points):
    region_idx = vor.point_region[i]
    region = vor.regions[region_idx]
    if not region or -1 in region:
        continue

    # Get vertices for this region
    polygon_vertices = vor.vertices[region].copy()

    # Clip to bounding box
    polygon_vertices[:, 0] = np.clip(polygon_vertices[:, 0], bbox[0], bbox[1])
    polygon_vertices[:, 1] = np.clip(polygon_vertices[:, 1], bbox[2], bbox[3])

    # Draw polygon with distinct color
    poly = Polygon(polygon_vertices, facecolor=colors[i], edgecolor="white", linewidth=2.5, alpha=0.7)
    ax.add_patch(poly)

# Draw Voronoi edges for visual clarity
for ridge_idx, (p1, p2) in enumerate(vor.ridge_points):
    # Only draw if both points are original (not mirror)
    if p1 < n_points and p2 < n_points:
        v1, v2 = vor.ridge_vertices[ridge_idx]
        if v1 >= 0 and v2 >= 0:
            x_coords = [vor.vertices[v1, 0], vor.vertices[v2, 0]]
            y_coords = [vor.vertices[v1, 1], vor.vertices[v2, 1]]
            # Clip to bounding box
            x_coords = np.clip(x_coords, bbox[0], bbox[1])
            y_coords = np.clip(y_coords, bbox[2], bbox[3])
            ax.plot(x_coords, y_coords, "white", linewidth=2.5, alpha=0.9)

# Plot seed points using seaborn scatterplot
df = pd.DataFrame({"x": x, "y": y})
sns.scatterplot(data=df, x="x", y="y", s=350, color="#306998", edgecolor="white", linewidth=2.5, ax=ax, zorder=10)

# Labels and styling
ax.set_xlabel("X Coordinate (km)", fontsize=20)
ax.set_ylabel("Y Coordinate (km)", fontsize=20)
ax.set_title("voronoi-basic · seaborn · pyplots.ai", fontsize=24, fontweight="bold")
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim(bbox[0], bbox[1])
ax.set_ylim(bbox[2], bbox[3])
ax.set_aspect("equal")

# Add subtle border
for spine in ax.spines.values():
    spine.set_edgecolor("#306998")
    spine.set_linewidth(2)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
