""" anyplot.ai
voronoi-basic: Voronoi Diagram for Spatial Partitioning
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-17
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
BRAND = "#009E73"

# Okabe-Ito palette (canonical order) — define as seaborn-compatible list
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Data generation with spatial context
np.random.seed(42)
n_points = 20
x = np.random.uniform(10, 90, n_points)
y = np.random.uniform(10, 90, n_points)
points = np.column_stack([x, y])
bbox = [0, 100, 0, 100]

# Mirror points for infinite region handling
margin = 200
mirror_points = []
for px, py in points:
    mirror_points.extend([[px, -margin], [px, 100 + margin], [-margin, py], [100 + margin, py]])
all_points = np.vstack([points, mirror_points])

# Compute Voronoi tessellation
vor = Voronoi(all_points)

# Configure seaborn with sophisticated theming
sns.set_theme(style="ticks")
sns.set_palette(IMPRINT)  # Set global palette to Okabe-Ito
sns.set_context("talk", font_scale=1.1)  # Enhanced font sizing via seaborn context

# Apply theme-adaptive rendering context
plt.rcParams.update(
    {
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
    }
)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Get seaborn's color palette for dynamic color cycling
pal = sns.color_palette(IMPRINT)

# Draw Voronoi regions with dynamic color cycling from seaborn palette
for i in range(n_points):
    region_idx = vor.point_region[i]
    region = vor.regions[region_idx]
    if not region or -1 in region:
        continue

    polygon_vertices = vor.vertices[region].copy()
    polygon_vertices[:, 0] = np.clip(polygon_vertices[:, 0], bbox[0], bbox[1])
    polygon_vertices[:, 1] = np.clip(polygon_vertices[:, 1], bbox[2], bbox[3])

    # Use seaborn's palette cycling for color selection
    color = pal[i % len(pal)]
    poly = Polygon(polygon_vertices, facecolor=color, edgecolor=INK_SOFT, linewidth=2.5, alpha=0.7)
    ax.add_patch(poly)

# Draw Voronoi edges with seaborn-styled aesthetics
for ridge_idx, (p1, p2) in enumerate(vor.ridge_points):
    if p1 < n_points and p2 < n_points:
        v1, v2 = vor.ridge_vertices[ridge_idx]
        if v1 >= 0 and v2 >= 0:
            x_coords = np.clip([vor.vertices[v1, 0], vor.vertices[v2, 0]], bbox[0], bbox[1])
            y_coords = np.clip([vor.vertices[v1, 1], vor.vertices[v2, 1]], bbox[2], bbox[3])
            ax.plot(x_coords, y_coords, color=INK_SOFT, linewidth=2.5, alpha=0.9)

# Plot seed points with enhanced seaborn styling
df = pd.DataFrame({"x": x, "y": y})
sns.scatterplot(data=df, x="x", y="y", s=350, color=BRAND, edgecolor=INK, linewidth=2.5, ax=ax, zorder=10)

# Labels with seaborn-compatible font sizing
ax.set_xlabel("X Coordinate (km)", fontsize=20, color=INK)
ax.set_ylabel("Y Coordinate (km)", fontsize=20, color=INK)
ax.set_title("voronoi-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=20)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.set_xlim(bbox[0], bbox[1])
ax.set_ylim(bbox[2], bbox[3])
ax.set_aspect("equal")

# Spine styling with seaborn theme-adaptive colors
for spine in ax.spines.values():
    spine.set_edgecolor(INK_SOFT)
    spine.set_linewidth(2)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
