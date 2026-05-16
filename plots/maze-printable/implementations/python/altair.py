""" anyplot.ai
maze-printable: Printable Maze Puzzle
Library: altair 6.1.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-16
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


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

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

# Create markers for Start and Goal (positioned closer to entrances)
markers = pd.DataFrame(
    [
        {"x": -0.5, "y": 1.5, "label": "S"},  # Start marker at entrance
        {"x": WIDTH * 2 + 0.5, "y": HEIGHT * 2 - 0.5, "label": "G"},  # Goal marker at exit
    ]
)

# Create the maze walls using mark_rect
maze_chart = (
    alt.Chart(df_walls)
    .mark_rect(color=INK)
    .encode(x=alt.X("x:Q", axis=None), x2="x2:Q", y=alt.Y("y:Q", axis=None, scale=alt.Scale(reverse=True)), y2="y2:Q")
)

# Create start/goal markers
marker_chart = (
    alt.Chart(markers)
    .mark_text(fontSize=56, fontWeight="bold", color=BRAND)
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None, scale=alt.Scale(reverse=True)), text="label:N")
)

# Create title text
title_df = pd.DataFrame([{"x": (WIDTH * 2 + 1) / 2, "y": -3, "text": "maze-printable · altair · anyplot.ai"}])

title_chart = (
    alt.Chart(title_df)
    .mark_text(fontSize=32, fontWeight="bold", color=INK)
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None, scale=alt.Scale(reverse=True)), text="text:N")
)

# Combine layers
chart = (
    alt.layer(maze_chart, marker_chart, title_chart)
    .properties(width=1600, height=1600, background=PAGE_BG)
    .configure_view(strokeWidth=0)
)

# Save with theme-suffixed filenames
output_dir = os.path.dirname(os.path.abspath(__file__))
chart.save(os.path.join(output_dir, f"plot-{THEME}.png"), scale_factor=3.0)
chart.save(os.path.join(output_dir, f"plot-{THEME}.html"))
