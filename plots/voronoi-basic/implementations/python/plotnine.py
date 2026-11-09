"""anyplot.ai
voronoi-basic: Voronoi Diagram for Spatial Partitioning
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
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
    scale_fill_identity,
    theme,
)
from scipy.spatial import Voronoi


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, assigned so neighbouring cells differ
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
BOX_PAD = 0.12  # bounding box margin around the seeds, as a share of their spread

# Columns: set these to your table's column names
X = "X Coordinate"  # role: x
Y = "Y Coordinate"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("facilities.csv")
np.random.seed(42)
n_points = 20
df = pd.DataFrame({X: np.random.uniform(1, 9, n_points), Y: np.random.uniform(1, 9, n_points)})

# Plot: reads only df and the constants above
seeds = df[[X, Y]].dropna().to_numpy(dtype=float)
n_seeds = len(seeds)
pad_x = BOX_PAD * np.ptp(seeds[:, 0])
pad_y = BOX_PAD * np.ptp(seeds[:, 1])
x_min, x_max = seeds[:, 0].min() - pad_x, seeds[:, 0].max() + pad_x
y_min, y_max = seeds[:, 1].min() - pad_y, seeds[:, 1].max() + pad_y

# Mirror the seeds far outside the box so every real cell is bounded
margin = 2 * max(x_max - x_min, y_max - y_min)
mirrors = np.vstack(
    [
        np.column_stack([2 * x_min - margin - seeds[:, 0], seeds[:, 1]]),
        np.column_stack([2 * x_max + margin - seeds[:, 0], seeds[:, 1]]),
        np.column_stack([seeds[:, 0], 2 * y_min - margin - seeds[:, 1]]),
        np.column_stack([seeds[:, 0], 2 * y_max + margin - seeds[:, 1]]),
    ]
)
vor = Voronoi(np.vstack([seeds, mirrors]))

# Greedy colouring over the cell adjacency, so cells sharing an edge never share a hue
neighbours = {i: set() for i in range(n_seeds)}
for a, b in vor.ridge_points:
    if a < n_seeds and b < n_seeds:
        neighbours[a].add(b)
        neighbours[b].add(a)
slot = {}
usage = [0] * len(IMPRINT_PALETTE)
for i in sorted(neighbours, key=lambda k: -len(neighbours[k])):
    taken = {slot[j] for j in neighbours[i] if j in slot}
    free = [c for c in range(len(IMPRINT_PALETTE)) if c not in taken]
    slot[i] = min(free, key=lambda c: (usage[c], c))  # least-used free hue spreads the palette
    usage[slot[i]] += 1

# Sutherland-Hodgman clipping against the four box edges: (axis, bound, keep side)
edges = [(0, x_min, 1), (0, x_max, -1), (1, y_min, 1), (1, y_max, -1)]
polygon_rows = []
for i in range(n_seeds):
    polygon = [tuple(vor.vertices[v]) for v in vor.regions[vor.point_region[i]]]
    for axis, bound, side in edges:
        clipped = []
        for k in range(len(polygon)):
            curr, prev = polygon[k], polygon[k - 1]
            curr_in = side * (curr[axis] - bound) >= 0
            prev_in = side * (prev[axis] - bound) >= 0
            if curr_in != prev_in:
                t = (bound - prev[axis]) / (curr[axis] - prev[axis])
                clipped.append(tuple(p + t * (c - p) for p, c in zip(prev, curr, strict=True)))
            if curr_in:
                clipped.append(curr)
        polygon = clipped
    for vx, vy in polygon:
        polygon_rows.append({"cell": i, X: vx, Y: vy, "fill": IMPRINT_PALETTE[slot[i]]})
cells = pd.DataFrame(polygon_rows)

plot = (
    ggplot(cells, aes(x=X, y=Y))
    + geom_polygon(aes(group="cell", fill="fill"), color=PAGE_BG, size=0.8)
    + geom_point(df, aes(x=X, y=Y), fill=INK, color=PAGE_BG, size=3, stroke=0.8, shape="o")
    + scale_fill_identity()
    + coord_fixed(ratio=1.0, xlim=(x_min, x_max), ylim=(y_min, y_max), expand=False)
    + labs(title="voronoi-basic · python · plotnine · anyplot.ai")
    + theme(
        figure_size=(6, 6),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_border=element_rect(color=INK_SOFT, fill=None, size=0.5),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        axis_ticks=element_line(color=INK_SOFT),
        plot_title=element_text(size=12, color=INK, weight="bold", margin={"b": 10}),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        legend_position="none",
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in", verbose=False)
