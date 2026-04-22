""" pyplots.ai
sudoku-basic: Basic Sudoku Grid
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - A partially filled Sudoku puzzle
# 0 represents empty cells
grid = np.array(
    [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9],
    ]
)

# Create figure (square format for symmetric grid, 3600x3600 px at 300 dpi)
fig, ax = plt.subplots(figsize=(12, 12))

# Set equal aspect ratio for square cells
ax.set_aspect("equal")

# Set axis limits
ax.set_xlim(0, 9)
ax.set_ylim(0, 9)

# Draw white background for all cells
for i in range(9):
    for j in range(9):
        rect = plt.Rectangle((j, 8 - i), 1, 1, facecolor="white", edgecolor="none")
        ax.add_patch(rect)

# Draw thin lines for individual cells (monochrome design)
for i in range(10):
    # Horizontal lines
    ax.plot([0, 9], [i, i], color="black", linewidth=1.5, zorder=1)
    # Vertical lines
    ax.plot([i, i], [0, 9], color="black", linewidth=1.5, zorder=1)

# Draw thick lines for 3x3 box boundaries
for i in range(0, 10, 3):
    ax.plot([0, 9], [i, i], color="black", linewidth=5, zorder=2)
    ax.plot([i, i], [0, 9], color="black", linewidth=5, zorder=2)

# Add numbers to cells
for i in range(9):
    for j in range(9):
        value = grid[i, j]
        if value != 0:
            # Center number in cell (j + 0.5 for x, 8-i + 0.5 for y to flip grid)
            ax.text(
                j + 0.5,
                8 - i + 0.5,
                str(value),
                fontsize=42,
                fontweight="bold",
                color="black",
                ha="center",
                va="center",
                zorder=3,
            )

# Remove axes and ticks
ax.set_xticks([])
ax.set_yticks([])
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.spines["left"].set_visible(False)

# Add title
ax.set_title("sudoku-basic · matplotlib · pyplots.ai", fontsize=32, fontweight="bold", color="black", pad=30)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
