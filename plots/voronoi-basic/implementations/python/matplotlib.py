"""anyplot.ai
voronoi-basic: Voronoi Diagram for Spatial Partitioning
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import PolyCollection
from scipy.spatial import Voronoi


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per cell in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
X = "X coordinate"  # role: x
Y = "Y coordinate"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("seeds.csv")
np.random.seed(42)
n_points = 15
df = pd.DataFrame({X: np.random.uniform(1, 9, n_points), Y: np.random.uniform(1, 9, n_points)})

# Plot: reads only df and the constants above
points = df[[X, Y]].dropna().to_numpy(dtype=float)
n_points = len(points)

# Visible bounding box: the seed extent padded by one unit
pad = 1.0
x_min, x_max = points[:, 0].min() - pad, points[:, 0].max() + pad
y_min, y_max = points[:, 1].min() - pad, points[:, 1].max() + pad

# Mirror every seed across each box edge so all original cells are finite
x, y = points[:, 0], points[:, 1]
mirrored = np.vstack(
    [
        points,
        np.column_stack([x, 2 * y_min - y]),
        np.column_stack([x, 2 * y_max - y]),
        np.column_stack([2 * x_min - x, y]),
        np.column_stack([2 * x_max - x, y]),
    ]
)
vor = Voronoi(mirrored)

# Greedy coloring: each cell takes the first palette color none of its neighbors uses
neighbors = {i: set() for i in range(n_points)}
for a, b in vor.ridge_points:
    if a < n_points and b < n_points:
        neighbors[a].add(b)
        neighbors[b].add(a)
cell_color = {}
for idx in range(n_points):
    taken = {cell_color[n] for n in neighbors[idx] if n in cell_color}
    cell_color[idx] = next((c for c in range(len(IMPRINT_PALETTE)) if c not in taken), idx % len(IMPRINT_PALETTE))

polygons = []
poly_colors = []
for idx in range(n_points):
    region = vor.regions[vor.point_region[idx]]
    if not region or -1 in region:
        continue
    polygon = vor.vertices[region].copy()
    polygon[:, 0] = np.clip(polygon[:, 0], x_min, x_max)
    polygon[:, 1] = np.clip(polygon[:, 1], y_min, y_max)
    polygons.append(polygon)
    poly_colors.append(IMPRINT_PALETTE[cell_color[idx]])

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

collection = PolyCollection(polygons, facecolors=poly_colors, edgecolors=INK_SOFT, linewidths=1.2, alpha=0.6)
ax.add_collection(collection)
ax.scatter(x, y, s=70, c=IMPRINT_PALETTE[0], edgecolors="white", linewidths=1.5, zorder=5)

# Style
ax.set_xlim(x_min - 0.02 * (x_max - x_min), x_max + 0.02 * (x_max - x_min))
ax.set_ylim(y_min - 0.02 * (y_max - y_min), y_max + 0.02 * (y_max - y_min))
ax.set_xlabel(X, fontsize=10, color=INK)
ax.set_ylabel(Y, fontsize=10, color=INK)
ax.set_title("voronoi-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.set_aspect("equal")
ax.yaxis.grid(True, alpha=0.12, linewidth=0.8, color=INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
