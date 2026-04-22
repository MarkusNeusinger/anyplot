""" pyplots.ai
sudoku-basic: Basic Sudoku Grid
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Sudoku puzzle data (0 = empty cell)
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

# Set seaborn style for clean aesthetic
sns.set_style("white")
sns.set_context("talk", font_scale=1.5)

# Create square figure (3600x3600 px at 300 dpi = 12x12 inches)
fig, ax = plt.subplots(figsize=(12, 12))

# Create heatmap data for visual structure (all white for clean look)
display_grid = np.ones((9, 9))

# Use seaborn heatmap as the base grid structure
sns.heatmap(
    display_grid,
    ax=ax,
    cmap=["white"],
    cbar=False,
    linewidths=1,
    linecolor="#CCCCCC",
    square=True,
    xticklabels=False,
    yticklabels=False,
    vmin=0,
    vmax=1,
)

# Add numbers to the grid
for i in range(9):
    for j in range(9):
        if grid[i, j] != 0:
            ax.text(
                j + 0.5,
                i + 0.5,
                str(grid[i, j]),
                ha="center",
                va="center",
                fontsize=32,
                fontweight="bold",
                color="#306998",
            )

# Draw thick lines for 3x3 box boundaries
for i in range(4):
    # Horizontal thick lines
    ax.axhline(y=i * 3, color="black", linewidth=4)
    # Vertical thick lines
    ax.axvline(x=i * 3, color="black", linewidth=4)

# Add border rectangle for clean edges
border = patches.Rectangle((0, 0), 9, 9, linewidth=4, edgecolor="black", facecolor="none")
ax.add_patch(border)

# Title
ax.set_title("sudoku-basic · seaborn · pyplots.ai", fontsize=28, fontweight="bold", pad=20, color="#306998")

# Remove axis ticks
ax.set_xticks([])
ax.set_yticks([])

# Set axis limits
ax.set_xlim(0, 9)
ax.set_ylim(9, 0)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
