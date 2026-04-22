""" pyplots.ai
maze-printable: Printable Maze Puzzle
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-07
"""

import altair as alt
import numpy as np
import pandas as pd


# Maze parameters
np.random.seed(42)
WIDTH = 25
HEIGHT = 25

# Initialize maze grid (0 = path, 1 = wall)
maze = np.ones((HEIGHT * 2 + 1, WIDTH * 2 + 1), dtype=int)

# Generate maze using iterative DFS with explicit stack (no recursion)
stack = [(0, 0)]
maze[1, 1] = 0  # Mark starting cell as path

while stack:
    x, y = stack[-1]
    directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
    np.random.shuffle(directions)

    found = False
    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        if 0 <= nx < WIDTH and 0 <= ny < HEIGHT and maze[ny * 2 + 1, nx * 2 + 1] == 1:
            # Carve wall between current and next cell
            maze[y * 2 + 1 + dy, x * 2 + 1 + dx] = 0
            maze[ny * 2 + 1, nx * 2 + 1] = 0
            stack.append((nx, ny))
            found = True
            break

    if not found:
        stack.pop()

# Create openings for start (top-left) and goal (bottom-right)
maze[1, 0] = 0  # Start entrance
maze[HEIGHT * 2 - 1, WIDTH * 2] = 0  # Goal exit

# Convert maze to rectangle data for Altair
rectangles = []
for row in range(maze.shape[0]):
    for col in range(maze.shape[1]):
        if maze[row, col] == 1:
            rectangles.append({"x": col, "x2": col + 1, "y": row, "y2": row + 1})

df_walls = pd.DataFrame(rectangles)

# Create markers for Start and Goal
# Position markers at the entrance/exit openings
markers = pd.DataFrame(
    [
        {"x": -1.5, "y": 1.5, "label": "S"},  # Start marker outside left entrance
        {"x": WIDTH * 2 + 2.5, "y": HEIGHT * 2 - 0.5, "label": "G"},  # Goal marker outside right exit
    ]
)

# Create the maze walls using mark_rect
maze_chart = (
    alt.Chart(df_walls)
    .mark_rect(color="black")
    .encode(x=alt.X("x:Q", axis=None), x2="x2:Q", y=alt.Y("y:Q", axis=None, scale=alt.Scale(reverse=True)), y2="y2:Q")
)

# Create start/goal markers
marker_chart = (
    alt.Chart(markers)
    .mark_text(fontSize=56, fontWeight="bold", color="#306998")
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None, scale=alt.Scale(reverse=True)), text="label:N")
)

# Create title text
title_df = pd.DataFrame([{"x": (WIDTH * 2 + 1) / 2, "y": -3, "text": "maze-printable · altair · pyplots.ai"}])

title_chart = (
    alt.Chart(title_df)
    .mark_text(fontSize=32, fontWeight="bold", color="black")
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None, scale=alt.Scale(reverse=True)), text="text:N")
)

# Combine layers
chart = (
    alt.layer(maze_chart, marker_chart, title_chart).properties(width=1600, height=1600).configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=2.25)
chart.save("plot.html")
