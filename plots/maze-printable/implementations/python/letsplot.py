""" pyplots.ai
maze-printable: Printable Maze Puzzle
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-07
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Maze parameters
np.random.seed(42)
width = 25
height = 25

# Initialize maze grid (walls = 1, passages = 0)
# We use a (2*height+1) x (2*width+1) grid to represent walls between cells
maze = np.ones((2 * height + 1, 2 * width + 1), dtype=int)

# Initialize visited array for cells
visited = np.zeros((height, width), dtype=bool)

# DFS maze generation with iterative approach
stack = [(0, 0)]
visited[0, 0] = True
maze[1, 1] = 0  # Start cell is passage

directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

while stack:
    cy, cx = stack[-1]
    neighbors = []
    for dy, dx in directions:
        ny, nx = cy + dy, cx + dx
        if 0 <= ny < height and 0 <= nx < width and not visited[ny, nx]:
            neighbors.append((ny, nx, dy, dx))

    if neighbors:
        ny, nx, dy, dx = neighbors[np.random.randint(len(neighbors))]
        visited[ny, nx] = True
        # Remove wall between current and next cell
        maze[2 * cy + 1 + dy, 2 * cx + 1 + dx] = 0
        # Mark next cell as passage
        maze[2 * ny + 1, 2 * nx + 1] = 0
        stack.append((ny, nx))
    else:
        stack.pop()

# Create entrance and exit openings in the outer wall
# Entrance: remove wall at maze[0, 1] (top of first passage cell)
# Exit: remove wall at maze[2*height, 2*width-1] (bottom of last passage cell)
maze[0, 1] = 0  # Entrance opening
maze[2 * height, 2 * width - 1] = 0  # Exit opening

# Create data for plotting walls as rectangles
wall_data = []
maze_rows = maze.shape[0]
for y in range(maze_rows):
    for x in range(maze.shape[1]):
        if maze[y, x] == 1:
            wall_data.append({"xmin": x, "xmax": x + 1, "ymin": maze_rows - y - 1, "ymax": maze_rows - y})

df_walls = pd.DataFrame(wall_data)

# Start and goal positions (outside the maze at entrance/exit)
# Entrance opening is at maze[0, 1] -> display (1, 50) to (2, 51), center (1.5, 50.5)
# Exit opening is at maze[50, 49] -> display (49, 0) to (50, 1), center (49.5, 0.5)
# Place markers just outside these openings
start_x = 1.5
start_y = maze_rows + 0.5  # Just above the entrance
goal_x = 2 * width - 1 + 0.5  # = 49.5
goal_y = -0.5  # Just below the exit

df_markers = pd.DataFrame({"x": [start_x, goal_x], "y": [start_y, goal_y], "label": ["S", "G"]})

# Create plot with axis limits to include markers fully
plot = (
    ggplot()
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"), data=df_walls, fill="black", color="black", size=0
    )
    + geom_text(aes(x="x", y="y", label="label"), data=df_markers, size=10, fontface="bold", color="#306998")
    + coord_fixed(ratio=1, xlim=(-1.5, maze.shape[1] + 0.5), ylim=(-1.5, maze_rows + 1.5))
    + theme_void()
    + theme(plot_title=element_text(size=24, hjust=0.5), plot_margin=[40, 40, 40, 40])
    + labs(title="maze-printable \u00b7 letsplot \u00b7 pyplots.ai")
    + ggsize(1200, 1200)
)

# Save as PNG and HTML
ggsave(plot, "plot.png", scale=3)
ggsave(plot, "plot.html")
