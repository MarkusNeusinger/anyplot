""" pyplots.ai
crossword-basic: Crossword Puzzle Grid
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-15
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - 15x15 crossword grid with symmetric black cell pattern
np.random.seed(42)
grid_size = 15

# Create symmetric black cell pattern (180-degree rotational symmetry)
# Start with empty grid (0 = white/entry cell, 1 = black/blocked cell)
grid = np.zeros((grid_size, grid_size), dtype=int)

# Define black cell positions for upper-left quadrant + center row/col
# These will be mirrored for symmetry
black_positions = [
    (0, 4),
    (0, 10),
    (1, 4),
    (1, 10),
    (2, 7),
    (3, 0),
    (3, 6),
    (3, 11),
    (3, 12),
    (4, 3),
    (4, 8),
    (4, 13),
    (4, 14),
    (5, 5),
    (5, 9),
    (6, 2),
    (6, 7),
    (6, 12),
    (7, 2),
    (7, 7),
    (7, 12),
]

# Apply black cells with 180-degree rotational symmetry
for r, c in black_positions:
    grid[r, c] = 1
    grid[grid_size - 1 - r, grid_size - 1 - c] = 1

# Determine numbered cells (start of across or down words)
numbers = {}
clue_num = 1

for r in range(grid_size):
    for c in range(grid_size):
        if grid[r, c] == 1:  # Skip black cells
            continue

        # Check if this starts an across word (left edge or black cell to left, white to right)
        starts_across = (c == 0 or grid[r, c - 1] == 1) and (c < grid_size - 1 and grid[r, c + 1] == 0)

        # Check if this starts a down word (top edge or black cell above, white below)
        starts_down = (r == 0 or grid[r - 1, c] == 1) and (r < grid_size - 1 and grid[r + 1, c] == 0)

        if starts_across or starts_down:
            numbers[(r, c)] = clue_num
            clue_num += 1

# Build dataframe for grid cells
cells_data = []
for r in range(grid_size):
    for c in range(grid_size):
        cells_data.append(
            {"row": r, "col": c, "is_black": grid[r, c] == 1, "color": "#1a1a1a" if grid[r, c] == 1 else "#ffffff"}
        )

cells_df = pd.DataFrame(cells_data)

# Build dataframe for clue numbers
numbers_data = []
for (r, c), num in numbers.items():
    numbers_data.append({"row": r, "col": c, "number": str(num)})

numbers_df = pd.DataFrame(numbers_data)

# Create grid cells chart
cells = (
    alt.Chart(cells_df)
    .mark_rect(stroke="#333333", strokeWidth=2)
    .encode(x=alt.X("col:O", axis=None), y=alt.Y("row:O", axis=None), color=alt.Color("color:N", scale=None))
    .properties(width=900, height=900)
)

# Create clue numbers overlay
clue_numbers = (
    alt.Chart(numbers_df)
    .mark_text(align="left", baseline="top", dx=-12, dy=-12, fontSize=14, fontWeight="bold", color="#333333")
    .encode(x=alt.X("col:O", axis=None), y=alt.Y("row:O", axis=None), text="number:N")
)

# Combine layers and add title
chart = (
    (cells + clue_numbers)
    .properties(title=alt.Title("crossword-basic · altair · pyplots.ai", fontSize=32, anchor="middle", offset=20))
    .configure_view(strokeWidth=0)
)

# Save outputs
chart.save("plot.png", scale_factor=4.0)
chart.save("plot.html")
