"""anyplot.ai
maze-printable: Printable Maze Puzzle
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 73/100 | Updated: 2026-05-16
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"

# Constants
CELLS_WIDE = 25
CELLS_HIGH = 25
SEED = 42
KIND_WALL = "wall"
KIND_MARKER = "marker"

# Columns
XMIN = "xmin"  # role: extra
XMAX = "xmax"  # role: extra
YMIN = "ymin"  # role: extra
YMAX = "ymax"  # role: extra
KIND = "kind"  # role: extra
LABEL = "label"  # role: extra

# Data
rng = np.random.default_rng(SEED)
grid_rows, grid_cols = 2 * CELLS_HIGH + 1, 2 * CELLS_WIDE + 1
maze = np.ones((grid_rows, grid_cols), dtype=int)  # 1 = wall, 0 = passage
visited = np.zeros((CELLS_HIGH, CELLS_WIDE), dtype=bool)

# Iterative depth-first carving: exactly one route between any two cells
stack = [(0, 0)]
visited[0, 0] = True
maze[1, 1] = 0
for_directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
while stack:
    cy, cx = stack[-1]
    options = [
        (cy + dy, cx + dx, dy, dx)
        for dy, dx in for_directions
        if 0 <= cy + dy < CELLS_HIGH and 0 <= cx + dx < CELLS_WIDE and not visited[cy + dy, cx + dx]
    ]
    if options:
        ny, nx, dy, dx = options[rng.integers(len(options))]
        visited[ny, nx] = True
        maze[2 * cy + 1 + dy, 2 * cx + 1 + dx] = 0
        maze[2 * ny + 1, 2 * nx + 1] = 0
        stack.append((ny, nx))
    else:
        stack.pop()

# Entrance in the top wall above the first cell, exit in the bottom wall below the last cell
maze[0, 1] = 0
maze[grid_rows - 1, grid_cols - 2] = 0

wall_rows, wall_cols = np.nonzero(maze == 1)
walls = pd.DataFrame(
    {
        XMIN: wall_cols,
        XMAX: wall_cols + 1,
        YMIN: grid_rows - wall_rows - 1,
        YMAX: grid_rows - wall_rows,
        KIND: KIND_WALL,
        LABEL: "",
    }
)
markers = pd.DataFrame(
    {
        XMIN: [1.0, grid_cols - 2.0],
        XMAX: [2.0, grid_cols - 1.0],
        YMIN: [grid_rows + 0.0, -1.0],
        YMAX: [grid_rows + 1.0, 0.0],
        KIND: KIND_MARKER,
        LABEL: ["S", "G"],
    }
)
df = pd.concat([walls, markers], ignore_index=True)

# Plot
wall_df = df[df[KIND] == KIND_WALL]
marker_df = df[df[KIND] == KIND_MARKER].assign(x=lambda d: (d[XMIN] + d[XMAX]) / 2, y=lambda d: (d[YMIN] + d[YMAX]) / 2)
margin = 2.0
plot = (
    ggplot()
    + geom_rect(aes(xmin=XMIN, xmax=XMAX, ymin=YMIN, ymax=YMAX), data=wall_df, fill=INK, color=INK, size=0.3)
    + geom_text(aes(x="x", y="y", label=LABEL), data=marker_df, size=9, fontface="bold", color=INK)
    + coord_fixed(
        ratio=1,
        xlim=(df[XMIN].min() - margin, df[XMAX].max() + margin),
        ylim=(df[YMIN].min() - margin, df[YMAX].max() + margin),
    )
    + theme_void()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=14, hjust=0.5, color=INK),
        plot_margin=[15, 15, 15, 15],
    )
    + labs(title="maze-printable · python · letsplot · anyplot.ai")
    + ggsize(600, 600)
)

# Save
ggsave(plot, f"plot-{THEME}.png", scale=4)
ggsave(plot, f"plot-{THEME}.html")
