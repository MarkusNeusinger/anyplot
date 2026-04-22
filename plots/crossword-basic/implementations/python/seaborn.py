""" pyplots.ai
crossword-basic: Crossword Puzzle Grid
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-15
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Set style
sns.set_style("white")

# Data: 15x15 crossword grid with 180-degree rotational symmetry
np.random.seed(42)
grid_size = 15

# Create symmetric black cell pattern (1 = blocked, 0 = entry)
grid = np.zeros((grid_size, grid_size), dtype=int)

# Define blocked cells for top half (will be mirrored for symmetry)
blocked_positions = [
    (0, 4),
    (0, 10),
    (1, 4),
    (1, 10),
    (2, 7),
    (3, 0),
    (3, 6),
    (3, 11),
    (3, 12),
    (3, 13),
    (3, 14),
    (4, 3),
    (4, 8),
    (5, 5),
    (5, 9),
    (5, 14),
    (6, 2),
    (6, 6),
    (6, 10),
    (7, 7),
]

# Apply blocked cells with 180-degree rotational symmetry
for r, c in blocked_positions:
    grid[r, c] = 1
    grid[grid_size - 1 - r, grid_size - 1 - c] = 1

# Calculate clue numbers for cells that start across or down words
numbers = {}
clue_num = 1
for r in range(grid_size):
    for c in range(grid_size):
        if grid[r, c] == 1:
            continue
        # Check if starts across word (left edge or blocked cell to left, and has room)
        starts_across = (c == 0 or grid[r, c - 1] == 1) and (c < grid_size - 1 and grid[r, c + 1] == 0)
        # Check if starts down word (top edge or blocked cell above, and has room)
        starts_down = (r == 0 or grid[r - 1, c] == 1) and (r < grid_size - 1 and grid[r + 1, c] == 0)

        if starts_across or starts_down:
            numbers[(r, c)] = clue_num
            clue_num += 1

# Plot using seaborn heatmap
fig, ax = plt.subplots(figsize=(12, 12))

# Create color map: 0 (white cells) = white, 1 (blocked) = black
cmap = sns.color_palette(["white", "#1a1a1a"])

# Plot heatmap without annotations
sns.heatmap(
    grid,
    ax=ax,
    cmap=cmap,
    cbar=False,
    square=True,
    linewidths=2,
    linecolor="#306998",
    xticklabels=False,
    yticklabels=False,
)

# Add clue numbers to appropriate cells
for (r, c), num in numbers.items():
    # Position numbers in top-left corner of cell
    ax.text(c + 0.15, r + 0.25, str(num), fontsize=11, fontweight="bold", color="#306998", ha="left", va="top")

# Style
ax.set_title("crossword-basic · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20)

# Remove axis spines and add outer border
for spine in ax.spines.values():
    spine.set_visible(True)
    spine.set_color("#306998")
    spine.set_linewidth(3)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
