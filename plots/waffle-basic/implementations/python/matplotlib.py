""" pyplots.ai
waffle-basic: Basic Waffle Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-24
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


# Data - Market share distribution (sums to 100%)
categories = ["Product A", "Product B", "Product C", "Product D"]
values = [42, 28, 18, 12]  # Percentages that sum to 100

# Colors - Python Blue and Yellow first, then colorblind-safe additions
colors = ["#306998", "#FFD43B", "#4DAF4A", "#E377C2"]

# Create 10x10 grid (100 squares, each = 1%)
grid_size = 10
total_squares = grid_size * grid_size

# Build the grid data - fill squares by category
grid = np.zeros(total_squares, dtype=int)
start_idx = 0
for i, val in enumerate(values):
    grid[start_idx : start_idx + val] = i
    start_idx += val

# Reshape to 10x10 grid, fill from bottom-left
grid = grid.reshape((grid_size, grid_size))

# Create plot (4800x2700 px)
fig, ax = plt.subplots(figsize=(16, 9))

# Draw squares
square_size = 0.9  # Slightly smaller than 1 for gaps
for row in range(grid_size):
    for col in range(grid_size):
        category_idx = grid[row, col]
        rect = mpatches.FancyBboxPatch(
            (col + 0.05, row + 0.05),
            square_size,
            square_size,
            boxstyle="round,pad=0.02,rounding_size=0.1",
            facecolor=colors[category_idx],
            edgecolor="white",
            linewidth=2,
        )
        ax.add_patch(rect)

# Set axis limits and remove axes
ax.set_xlim(0, grid_size)
ax.set_ylim(0, grid_size)
ax.set_aspect("equal")
ax.axis("off")

# Create legend with percentage labels
legend_patches = [
    mpatches.Patch(color=colors[i], label=f"{categories[i]} ({values[i]}%)") for i in range(len(categories))
]
ax.legend(
    handles=legend_patches,
    loc="center left",
    bbox_to_anchor=(1.02, 0.5),
    fontsize=18,
    frameon=True,
    fancybox=True,
    shadow=True,
)

# Title
ax.set_title("waffle-basic · matplotlib · pyplots.ai", fontsize=24, pad=20)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
