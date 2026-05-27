""" anyplot.ai
maze-printable: Printable Maze Puzzle
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-16
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Set theme
sns.set_theme(style="white", rc={"figure.facecolor": PAGE_BG, "axes.facecolor": PAGE_BG, "text.color": INK})

# Maze parameters
np.random.seed(123)
WIDTH = 25
HEIGHT = 25

# Initialize maze grid (0=wall, 1=passage)
maze = np.zeros((2 * HEIGHT + 1, 2 * WIDTH + 1), dtype=int)

# Carve passages using DFS
visited = np.zeros((HEIGHT, WIDTH), dtype=bool)
stack = [(0, 0)]
visited[0, 0] = True
maze[1, 1] = 1

directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

while stack:
    y, x = stack[-1]
    neighbors = []

    for dy, dx in directions:
        ny, nx = y + dy, x + dx
        if 0 <= ny < HEIGHT and 0 <= nx < WIDTH and not visited[ny, nx]:
            neighbors.append((ny, nx, dy, dx))

    if neighbors:
        ny, nx, dy, dx = neighbors[np.random.randint(len(neighbors))]
        visited[ny, nx] = True
        maze[2 * ny + 1, 2 * nx + 1] = 1
        maze[2 * y + 1 + dy, 2 * x + 1 + dx] = 1
        stack.append((ny, nx))
    else:
        stack.pop()

# Create figure - square format for maze (3600x3600 px)
fig, ax = plt.subplots(figsize=(12, 12), facecolor=PAGE_BG)

# Create heatmap with theme-aware colors
if THEME == "light":
    colors = ["#000000", "#FFFFFF"]
else:
    colors = ["#FFFFFF", "#000000"]

cmap = sns.color_palette(colors, as_cmap=True)
sns.heatmap(maze, ax=ax, cmap=cmap, cbar=False, square=True, xticklabels=False, yticklabels=False, linewidths=0)

# Mark start position (top-left passage)
start_y, start_x = 1, 1
circle_start = plt.Circle((start_x + 0.5, start_y + 0.5), 0.55, color=IMPRINT[0], zorder=10)
ax.add_patch(circle_start)
ax.text(
    start_x + 0.5,
    start_y + 0.5,
    "S",
    fontsize=22,
    fontweight="bold",
    color="white",
    ha="center",
    va="center",
    zorder=11,
)

# Mark goal position (bottom-right passage)
goal_y, goal_x = 2 * HEIGHT - 1, 2 * WIDTH - 1
circle_goal = plt.Circle((goal_x + 0.5, goal_y + 0.5), 0.55, color=IMPRINT[1], zorder=10)
ax.add_patch(circle_goal)
ax.text(
    goal_x + 0.5, goal_y + 0.5, "G", fontsize=22, fontweight="bold", color="white", ha="center", va="center", zorder=11
)

# Add title
ax.set_title("maze-printable · seaborn · anyplot.ai", fontsize=28, fontweight="bold", pad=20, color=INK)

# Clean up for printing
ax.set_aspect("equal")
sns.despine(left=True, bottom=True)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
