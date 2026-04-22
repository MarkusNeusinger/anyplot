""" pyplots.ai
maze-printable: Printable Maze Puzzle
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-07
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Set clean style for printable maze
sns.set_style("white")
sns.set_context("talk", font_scale=1.2)

# Maze parameters
np.random.seed(42)
WIDTH = 25  # cells horizontally
HEIGHT = 25  # cells vertically

# Initialize maze grid (0=wall, 1=passage)
# Start with all walls
maze = np.zeros((2 * HEIGHT + 1, 2 * WIDTH + 1), dtype=int)

# Carve passages using DFS (Depth-First Search) algorithm
visited = np.zeros((HEIGHT, WIDTH), dtype=bool)
stack = [(0, 0)]
visited[0, 0] = True
maze[1, 1] = 1  # Start cell

directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # right, down, left, up

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
        # Carve passage (cell and wall between)
        maze[2 * ny + 1, 2 * nx + 1] = 1  # cell
        maze[2 * y + 1 + dy, 2 * x + 1 + dx] = 1  # wall between
        stack.append((ny, nx))
    else:
        stack.pop()

# Create figure - square format for maze
fig, ax = plt.subplots(figsize=(12, 12))

# Create heatmap using seaborn
# Invert colors: 0 (walls) = black, 1 (passages) = white
cmap = sns.color_palette(["#000000", "#FFFFFF"], as_cmap=True)
sns.heatmap(maze, ax=ax, cmap=cmap, cbar=False, square=True, xticklabels=False, yticklabels=False, linewidths=0)

# Mark start position (top-left passage) with circle background
start_y, start_x = 1, 1
circle_start = plt.Circle((start_x + 0.5, start_y + 0.5), 0.4, color="#306998", zorder=10)
ax.add_patch(circle_start)
ax.text(
    start_x + 0.5,
    start_y + 0.5,
    "S",
    fontsize=18,
    fontweight="bold",
    color="#FFFFFF",
    ha="center",
    va="center",
    zorder=11,
)

# Mark goal position (bottom-right passage) with circle background
goal_y, goal_x = 2 * HEIGHT - 1, 2 * WIDTH - 1
circle_goal = plt.Circle((goal_x + 0.5, goal_y + 0.5), 0.4, color="#FFD43B", zorder=10)
ax.add_patch(circle_goal)
ax.text(
    goal_x + 0.5,
    goal_y + 0.5,
    "G",
    fontsize=18,
    fontweight="bold",
    color="#000000",
    ha="center",
    va="center",
    zorder=11,
)

# Add title
ax.set_title("maze-printable · seaborn · pyplots.ai", fontsize=28, fontweight="bold", pad=20, color="#000000")

# Clean up for printing
ax.set_aspect("equal")
sns.despine(left=True, bottom=True)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
