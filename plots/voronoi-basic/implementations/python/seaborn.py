""" anyplot.ai
voronoi-basic: Voronoi Diagram for Spatial Partitioning
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-22
"""

import os
import sys


if sys.path[0] == os.path.dirname(os.path.abspath(__file__)):
    sys.path.pop(0)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Polygon, Rectangle
from scipy.spatial import Voronoi


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

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
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Constants
BOX = (0, 100)  # visible bounding box, same range on both axes

# Columns: set these to your table's column names
X = "X coordinate (km)"  # role: x
Y = "Y coordinate (km)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("seeds.csv")
rng = np.random.default_rng(42)
n_seeds = 20
df = pd.DataFrame({X: rng.uniform(10, 90, n_seeds), Y: rng.uniform(10, 90, n_seeds)})

# Plot: reads only df and the constants above
seeds = df[[X, Y]].dropna().to_numpy(dtype=float)
lo, hi = BOX
span = hi - lo

# Distant helper seeds above, below and beside every seed make all real cells finite
far = 2 * span
helpers = np.vstack(
    [
        np.column_stack([seeds[:, 0], np.full(len(seeds), lo - far)]),
        np.column_stack([seeds[:, 0], np.full(len(seeds), hi + far)]),
        np.column_stack([np.full(len(seeds), lo - far), seeds[:, 1]]),
        np.column_stack([np.full(len(seeds), hi + far), seeds[:, 1]]),
    ]
)
vor = Voronoi(np.vstack([seeds, helpers]))

# Neighbouring cells share an edge: give each cell the first palette color its neighbours do not use
neighbours = {i: set() for i in range(len(seeds))}
for a, b in vor.ridge_points:
    if a < len(seeds) and b < len(seeds):
        neighbours[a].add(b)
        neighbours[b].add(a)
cell_color = {}
for i in range(len(seeds)):
    used = {cell_color[j] for j in neighbours[i] if j in cell_color}
    cell_color[i] = next(k for k in range(len(IMPRINT_PALETTE)) if k not in used)

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
frame = Rectangle((lo, lo), span, span, transform=ax.transData)

for i in range(len(seeds)):
    cell = Polygon(
        vor.vertices[vor.regions[vor.point_region[i]]],
        facecolor=IMPRINT_PALETTE[cell_color[i]],
        edgecolor=INK_SOFT,
        linewidth=1.2,
        alpha=0.75,
        joinstyle="round",
    )
    ax.add_patch(cell)
    cell.set_clip_path(frame)  # outer cells are cut at the bounding box

sns.scatterplot(data=df, x=X, y=Y, s=60, color=INK, edgecolor=PAGE_BG, linewidth=1.0, ax=ax, zorder=5)

# Style
ax.set_title("voronoi-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(X, fontsize=10)
ax.set_ylabel(Y, fontsize=10)
ax.tick_params(axis="both", labelsize=8)
ax.set_xlim(lo, hi)
ax.set_ylim(lo, hi)
ax.set_aspect("equal")
for spine in ax.spines.values():
    spine.set_linewidth(1.2)

fig.subplots_adjust(left=0.12, right=0.95, top=0.93, bottom=0.1)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
