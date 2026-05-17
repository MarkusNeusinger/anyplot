"""anyplot.ai
voronoi-basic: Voronoi Diagram for Spatial Partitioning
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-05-17
"""

import os
import sys


if sys.path[0] == os.path.dirname(os.path.abspath(__file__)):
    sys.path.pop(0)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Polygon
from scipy.spatial import Voronoi


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

# Okabe-Ito palette (canonical order)
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

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

# Apply seaborn theme with theme-adaptive colors
sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Draw Voronoi regions with Okabe-Ito colors
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

    # Draw polygon with Okabe-Ito color
    color = OKABE_ITO[i % len(OKABE_ITO)]
    poly = Polygon(polygon_vertices, facecolor=color, edgecolor=INK_SOFT, linewidth=2.5, alpha=0.7)
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
            ax.plot(x_coords, y_coords, color=INK_SOFT, linewidth=2.5, alpha=0.9)

# Plot seed points
df = pd.DataFrame({"x": x, "y": y})
sns.scatterplot(data=df, x="x", y="y", s=350, color=BRAND, edgecolor=INK, linewidth=2.5, ax=ax, zorder=10)

# Labels and styling
ax.set_xlabel("X Coordinate (km)", fontsize=20, color=INK)
ax.set_ylabel("Y Coordinate (km)", fontsize=20, color=INK)
ax.set_title("voronoi-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.set_xlim(bbox[0], bbox[1])
ax.set_ylim(bbox[2], bbox[3])
ax.set_aspect("equal")

# Theme-adaptive spine styling
for spine in ax.spines.values():
    spine.set_edgecolor(INK_SOFT)
    spine.set_linewidth(2)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
