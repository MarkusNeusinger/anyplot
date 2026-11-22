""" anyplot.ai
voronoi-basic: Voronoi Diagram for Spatial Partitioning
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 79/100 | Updated: 2026-11-22
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_polygon,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_manual,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
X = "X Coordinate"  # role: x
Y = "Y Coordinate"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("seeds.csv")
np.random.seed(42)
n_points = 20
df = pd.DataFrame(
    {
        X: np.concatenate([np.random.normal(25, 8, n_points // 2), np.random.normal(75, 8, n_points // 2)]),
        Y: np.concatenate([np.random.normal(40, 10, n_points // 2), np.random.normal(60, 10, n_points // 2)]),
    }
)

# Plot: reads only df and the constants above
CELL = "Cell"
seeds = df.dropna(subset=[X, Y]).reset_index(drop=True)
pts = seeds[[X, Y]].to_numpy(dtype=float)

# Square bounding box around the seeds, so equal axes keep every bisector perpendicular
center = (pts.min(axis=0) + pts.max(axis=0)) / 2
half = (pts.max(axis=0) - pts.min(axis=0)).max() / 2 * 1.3
box = np.array(
    [
        [center[0] - half, center[1] - half],
        [center[0] + half, center[1] - half],
        [center[0] + half, center[1] + half],
        [center[0] - half, center[1] + half],
    ]
)


def clip_half_plane(poly, normal, offset):
    """Keep the part of a convex polygon where normal . p <= offset (Sutherland-Hodgman)."""
    out = []
    for cur, prev in zip(poly, np.roll(poly, 1, axis=0), strict=True):
        d_cur, d_prev = normal @ cur - offset, normal @ prev - offset
        if (d_cur <= 0) != (d_prev <= 0):
            out.append(prev + (cur - prev) * d_prev / (d_prev - d_cur))
        if d_cur <= 0:
            out.append(cur)
    return np.array(out)


# Each cell is the box cut by the perpendicular bisector against every other seed
cells = []
for i, p in enumerate(pts):
    poly = box
    for j, q in enumerate(pts):
        if i != j and len(poly) >= 3:
            poly = clip_half_plane(poly, q - p, (q @ q - p @ p) / 2)
    cells.append(poly)

# Cells that share an edge share two vertices; color them greedily so neighbours differ
tol = half * 1e-6
neighbours = [
    [
        j
        for j in range(len(cells))
        if j != i
        and len(cells[i]) >= 3
        and len(cells[j]) >= 3
        and sum(np.isclose(cells[j], v, atol=tol).all(axis=1).any() for v in cells[i]) >= 2
    ]
    for i in range(len(cells))
]
slot = {}
for i in sorted(range(len(cells)), key=lambda k: -len(neighbours[k])):
    taken = {slot[j] for j in neighbours[i] if j in slot}
    slot[i] = next((k for k in range(len(IMPRINT_PALETTE)) if k not in taken), i % len(IMPRINT_PALETTE))

df_cells = pd.DataFrame(
    [{X: vx, Y: vy, CELL: f"Cell {i + 1}"} for i, poly in enumerate(cells) if len(poly) >= 3 for vx, vy in poly]
)
cell_colors = [IMPRINT_PALETTE[slot[i]] for i, poly in enumerate(cells) if len(poly) >= 3]

# Cells with seeds marked at their exact coordinates (dark ring, light core)
plot = (
    ggplot()
    + geom_polygon(data=df_cells, mapping=aes(x=X, y=Y, fill=CELL), color=INK_SOFT, size=0.75, alpha=0.7)
    + geom_point(data=seeds, mapping=aes(x=X, y=Y), color=INK, size=4)
    + geom_point(data=seeds, mapping=aes(x=X, y=Y), color=PAGE_BG, size=2)
    + scale_fill_manual(values=cell_colors)
    + coord_fixed(xlim=[box[0, 0], box[2, 0]], ylim=[box[0, 1], box[2, 1]])
    + labs(x=X, y=Y, title="voronoi-basic · python · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        plot_title=element_text(size=16, color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        legend_position="none",
    )
    + ggsize(600, 600)
)

# Save outputs with theme suffix
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
