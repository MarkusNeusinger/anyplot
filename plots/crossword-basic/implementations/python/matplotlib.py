""" pyplots.ai
crossword-basic: Crossword Puzzle Grid
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-15
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle


# Data: 15x15 crossword grid with 180-degree rotational symmetry
# 0 = white (entry cell), 1 = black (blocked cell)
np.random.seed(42)

grid_size = 15

# Create symmetric black cell pattern (traditional newspaper style)
# Start with empty grid
grid = np.zeros((grid_size, grid_size), dtype=int)

# Define black cell positions for one half (will mirror for symmetry)
black_cells = [
    (0, 4),
    (0, 10),
    (1, 4),
    (1, 10),
    (2, 7),
    (3, 0),
    (3, 5),
    (3, 6),
    (3, 11),
    (4, 0),
    (4, 1),
    (4, 8),
    (4, 9),
    (4, 14),
    (5, 3),
    (5, 12),
    (6, 6),
    (6, 7),
    (6, 8),
    (7, 2),
    (7, 4),
    (7, 10),
    (7, 12),
]

# Set black cells and their symmetric counterparts
for r, c in black_cells:
    grid[r, c] = 1
    # 180-degree rotational symmetry
    grid[grid_size - 1 - r, grid_size - 1 - c] = 1

# Calculate clue numbers (cells that start words across or down)
numbers = {}
clue_num = 1

for row in range(grid_size):
    for col in range(grid_size):
        if grid[row, col] == 1:
            continue  # Skip black cells

        starts_across = (col == 0 or grid[row, col - 1] == 1) and (col < grid_size - 1 and grid[row, col + 1] == 0)
        starts_down = (row == 0 or grid[row - 1, col] == 1) and (row < grid_size - 1 and grid[row + 1, col] == 0)

        if starts_across or starts_down:
            numbers[(row, col)] = clue_num
            clue_num += 1

# Create plot (square format for crossword)
fig, ax = plt.subplots(figsize=(12, 12))

# Draw the grid
cell_size = 1.0

for row in range(grid_size):
    for col in range(grid_size):
        x = col * cell_size
        y = (grid_size - 1 - row) * cell_size  # Flip y-axis for proper orientation

        if grid[row, col] == 1:
            # Black cell
            rect = Rectangle((x, y), cell_size, cell_size, facecolor="#1a1a1a", edgecolor="#333333", linewidth=1.5)
        else:
            # White entry cell
            rect = Rectangle((x, y), cell_size, cell_size, facecolor="white", edgecolor="#333333", linewidth=1.5)
        ax.add_patch(rect)

        # Add clue number if this cell starts a word
        if (row, col) in numbers:
            ax.text(
                x + 0.08,
                y + cell_size - 0.08,
                str(numbers[(row, col)]),
                fontsize=11,
                fontweight="bold",
                color="#306998",
                ha="left",
                va="top",
            )

# Set axis properties
ax.set_xlim(0, grid_size * cell_size)
ax.set_ylim(0, grid_size * cell_size)
ax.set_aspect("equal")
ax.axis("off")

# Title
ax.set_title("crossword-basic · matplotlib · pyplots.ai", fontsize=24, fontweight="bold", pad=20, color="#306998")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
