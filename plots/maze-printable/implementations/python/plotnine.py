""" pyplots.ai
maze-printable: Printable Maze Puzzle
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-07
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_text,
    geom_text,
    geom_tile,
    ggplot,
    labs,
    theme,
    theme_void,
)


# Maze generation using Depth-First Search (Recursive Backtracker)
np.random.seed(42)
width, height = 25, 25

# Initialize maze grid (all walls)
# 0 = passage, 1 = wall
maze = np.ones((height * 2 + 1, width * 2 + 1), dtype=int)

# Starting cell (top-left)
start_cell = (1, 1)
maze[start_cell[0], start_cell[1]] = 0

# DFS maze generation
stack = [start_cell]
visited = {start_cell}

while stack:
    current = stack[-1]
    cy, cx = current

    # Find unvisited neighbors (2 cells away)
    neighbors = []
    for dy, dx in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
        ny, nx = cy + dy, cx + dx
        if 1 <= ny < height * 2 and 1 <= nx < width * 2:
            if (ny, nx) not in visited:
                neighbors.append((ny, nx, dy // 2, dx // 2))

    if neighbors:
        # Choose random neighbor
        ny, nx, wy, wx = neighbors[np.random.randint(len(neighbors))]
        # Remove wall between current and neighbor
        maze[cy + wy, cx + wx] = 0
        maze[ny, nx] = 0
        visited.add((ny, nx))
        stack.append((ny, nx))
    else:
        stack.pop()

# Create DataFrame for plotting
rows = []
for y in range(maze.shape[0]):
    for x in range(maze.shape[1]):
        if maze[y, x] == 1:  # Wall
            rows.append({"x": x, "y": -y, "type": "wall"})

walls_df = pd.DataFrame(rows)

# Start and goal positions
start_y, start_x = 1, 1
goal_y, goal_x = height * 2 - 1, width * 2 - 1

markers_df = pd.DataFrame(
    {"x": [start_x, goal_x], "y": [-start_y, -goal_y], "label": ["S", "G"], "type": ["marker", "marker"]}
)

# Create the plot
plot = (
    ggplot()
    + geom_tile(data=walls_df, mapping=aes(x="x", y="y"), fill="black", width=1, height=1)
    + geom_text(data=markers_df, mapping=aes(x="x", y="y", label="label"), size=36, color="#306998", fontweight="bold")
    + coord_fixed(ratio=1)
    + labs(title="maze-printable · plotnine · pyplots.ai")
    + theme_void()
    + theme(
        figure_size=(12, 12),
        plot_title=element_text(size=24, ha="center", weight="bold"),
        plot_background=element_blank(),
        panel_background=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300)
