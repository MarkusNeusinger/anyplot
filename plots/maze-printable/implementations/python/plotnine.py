"""anyplot.ai
maze-printable: Printable Maze Puzzle
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-16
"""

import os

import numpy as np
import pandas as pd
from plotnine import aes, coord_fixed, element_rect, element_text, geom_text, geom_tile, ggplot, labs, theme, theme_void


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
BRAND = "#009E73"  # Imprint palette position 1

# Constants
WIDTH = 25  # role: width
HEIGHT = 25  # role: height
SEED = 42  # role: seed

# Columns
X = "x"
Y = "y"
WALL = "wall"
LABEL = "label"

# Data
rng = np.random.default_rng(SEED)
rows, cols = HEIGHT * 2 + 1, WIDTH * 2 + 1
maze = np.ones((rows, cols), dtype=int)  # 1 = wall, 0 = passage
start_cell = (1, 1)
maze[start_cell] = 0
stack = [start_cell]
visited = {start_cell}
while stack:
    cy, cx = stack[-1]
    neighbors = [
        (cy + dy, cx + dx, dy // 2, dx // 2)
        for dy, dx in [(-2, 0), (2, 0), (0, -2), (0, 2)]
        if 1 <= cy + dy < rows - 1 and 1 <= cx + dx < cols - 1 and (cy + dy, cx + dx) not in visited
    ]
    if neighbors:
        ny, nx, wy, wx = neighbors[rng.integers(len(neighbors))]
        maze[cy + wy, cx + wx] = 0
        maze[ny, nx] = 0
        visited.add((ny, nx))
        stack.append((ny, nx))
    else:
        stack.pop()

yy, xx = np.indices(maze.shape)
df = pd.DataFrame({X: xx.ravel(), Y: -yy.ravel(), WALL: maze.ravel().astype(bool), LABEL: None})
df.loc[(df[X] == 1) & (df[Y] == -1), LABEL] = "S"
df.loc[(df[X] == df[X].max() - 1) & (df[Y] == df[Y].min() + 1), LABEL] = "G"

# Plot
walls = df[df[WALL]]
markers = df[df[LABEL].notna()]

plot = (
    ggplot()
    + geom_tile(data=walls, mapping=aes(x=X, y=Y), fill=INK, width=1, height=1)
    + geom_text(data=markers, mapping=aes(x=X, y=Y, label=LABEL), size=9, color=BRAND, fontweight="bold")
    + coord_fixed(ratio=1)
    + labs(title="maze-printable · python · plotnine · anyplot.ai")
    + theme_void()
    + theme(
        figure_size=(6, 6),
        plot_title=element_text(size=12, ha="center", weight="bold", color=INK, margin={"b": 12, "t": 12}),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in")
