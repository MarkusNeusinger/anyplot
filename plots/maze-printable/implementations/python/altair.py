"""anyplot.ai
maze-printable: Printable Maze Puzzle
Library: altair 6.1.0 | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-16
"""

import os
import sys


if "" in sys.path:
    sys.path.remove("")
if "." in sys.path:
    sys.path.remove(".")
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir in sys.path:
    sys.path.remove(current_dir)

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"

# Imprint palette: position 1 marks start and goal
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

# Data: replace this block with your own maze, for example df = pd.read_csv("walls.csv")
WIDTH = 25  # cells horizontally
HEIGHT = 25  # cells vertically
rng = np.random.default_rng(42)

# Grid of blocks: 1 = wall, 0 = passage; cell (cx, cy) sits at block (2cy + 1, 2cx + 1)
grid = np.ones((HEIGHT * 2 + 1, WIDTH * 2 + 1), dtype=int)
grid[1, 1] = 0
stack = [(0, 0)]
while stack:
    cx, cy = stack[-1]
    moves = [(0, -1), (0, 1), (-1, 0), (1, 0)]
    rng.shuffle(moves)
    for dx, dy in moves:
        nx, ny = cx + dx, cy + dy
        if 0 <= nx < WIDTH and 0 <= ny < HEIGHT and grid[ny * 2 + 1, nx * 2 + 1] == 1:
            grid[cy * 2 + 1 + dy, cx * 2 + 1 + dx] = 0
            grid[ny * 2 + 1, nx * 2 + 1] = 0
            stack.append((nx, ny))
            break
    else:
        stack.pop()

# Entrance on the left of the top-left cell, exit on the right of the bottom-right cell
grid[1, 0] = 0
grid[-2, -1] = 0

# Plot: reads only the grid and the parameters above
n_cols = grid.shape[1]
n_rows = grid.shape[0]
wall_rows, wall_cols = np.nonzero(grid)
walls = pd.DataFrame({"col": wall_cols, "row": wall_rows, "col_end": wall_cols + 1, "row_end": wall_rows + 1})

# One wide margin of empty blocks around the maze keeps markers and walls off the image edge
x_scale = alt.Scale(domain=[-3, n_cols + 3], nice=False)
y_scale = alt.Scale(domain=[n_rows + 1, -1], nice=False)

wall_layer = (
    alt.Chart(walls)
    .mark_rect(color=INK, stroke=INK, strokeWidth=0.6)
    .encode(
        x=alt.X("col:Q", scale=x_scale, axis=None),
        x2="col_end:Q",
        y=alt.Y("row:Q", scale=y_scale, axis=None),
        y2="row_end:Q",
    )
)

# Start and goal letters sit just outside the openings
marks = pd.DataFrame({"mark_x": [-1.2, n_cols + 1.2], "mark_y": [1.5, n_rows - 1.5], "label": ["S", "G"]})
mark_layer = (
    alt.Chart(marks)
    .mark_text(fontSize=22, fontWeight="bold", color=BRAND)
    .encode(
        x=alt.X("mark_x:Q", scale=x_scale, axis=None), y=alt.Y("mark_y:Q", scale=y_scale, axis=None), text="label:N"
    )
)

chart = (
    alt.layer(wall_layer, mark_layer)
    .properties(
        width=540,
        height=540,
        background=PAGE_BG,
        title=alt.Title("maze-printable · python · altair · anyplot.ai", fontSize=18, color=INK, anchor="middle"),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
)

# Save: PNG padded (never cropped) to the 2400 x 2400 square canvas
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

TARGET = 2400
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET or img.height > TARGET:
    raise SystemExit(f"altair rendered {img.width}x{img.height}, exceeds {TARGET}x{TARGET}; shrink width/height")
canvas = Image.new("RGB", (TARGET, TARGET), PAGE_BG)
canvas.paste(img, ((TARGET - img.width) // 2, (TARGET - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
