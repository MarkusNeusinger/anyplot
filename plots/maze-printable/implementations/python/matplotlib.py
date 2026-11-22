"""anyplot.ai
maze-printable: Printable Maze Puzzle
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 75/100 | Updated: 2026-05-16
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"

# Imprint palette: position 1 marks the start, position 5 the goal
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data: maze parameters, replace width, height and seed to get another puzzle
width = 25  # number of cells horizontally
height = 25  # number of cells vertically
seed = 42  # random seed for a reproducible maze

# Grid of 2*size+1 so walls get cells of their own: 0 = wall, 1 = passage
np.random.seed(seed)
maze = np.zeros((2 * height + 1, 2 * width + 1), dtype=int)
visited = np.zeros((height, width), dtype=bool)
visited[0, 0] = True
maze[1, 1] = 1
stack = [(0, 0)]
directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

# Depth-first search carves exactly one route between any two cells
while stack:
    cy, cx = stack[-1]
    neighbors = [
        (cy + dy, cx + dx, dy, dx)
        for dy, dx in directions
        if 0 <= cy + dy < height and 0 <= cx + dx < width and not visited[cy + dy, cx + dx]
    ]
    if neighbors:
        ny, nx, dy, dx = neighbors[np.random.randint(len(neighbors))]
        maze[2 * cy + 1 + dy, 2 * cx + 1 + dx] = 1
        maze[2 * ny + 1, 2 * nx + 1] = 1
        visited[ny, nx] = True
        stack.append((ny, nx))
    else:
        stack.pop()

# Plot
maze_rows, maze_cols = maze.shape
start = (1, 1)  # top-left cell, as (row, column)
goal = (maze_rows - 2, maze_cols - 2)  # bottom-right cell

# Open the outer wall next to the start (entrance) and the goal (exit)
maze[start[0], 0] = 1
maze[goal[0], maze_cols - 1] = 1

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
fig.subplots_adjust(left=0.07, right=0.93, bottom=0.07, top=0.88)
ax.set_facecolor(PAGE_BG)

# Walls in ink, passages in the page color: black on white in light, the reverse in dark
ax.imshow(maze, cmap=ListedColormap([INK, PAGE_BG]), interpolation="nearest", aspect="equal", vmin=0, vmax=1)

# Start and goal: colored discs with a letter, told apart by hue and letter
for (row, col), letter, color in [(start, "S", IMPRINT_PALETTE[0]), (goal, "G", IMPRINT_PALETTE[4])]:
    ax.scatter(col, row, s=170, color=color, edgecolor=PAGE_BG, linewidth=0.8, zorder=3)
    ax.text(col, row, letter, fontsize=7, fontweight="bold", ha="center", va="center", color="#FFFFFF", zorder=4)

# Style
ax.set_axis_off()
ax.set_title("maze-printable · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=14)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
