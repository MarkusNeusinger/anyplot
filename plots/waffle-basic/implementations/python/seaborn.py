""" pyplots.ai
waffle-basic: Basic Waffle Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import ListedColormap


# Data - Budget allocation example
categories = ["Housing", "Food", "Transportation", "Utilities", "Entertainment"]
values = [35, 25, 20, 12, 8]  # Percentages, sum to 100

# Colors - Python Blue first, then additional colors
colors = ["#306998", "#FFD43B", "#4CAF50", "#FF7043", "#9C27B0"]

# Grid dimensions (10x10 = 100 squares for percentage representation)
grid_size = 10
total_squares = grid_size * grid_size

# Create grid data
grid = np.zeros((grid_size, grid_size), dtype=int)
square_idx = 0

for cat_idx, value in enumerate(values):
    for _ in range(value):
        if square_idx < total_squares:
            row = square_idx // grid_size
            col = square_idx % grid_size
            grid[row, col] = cat_idx
            square_idx += 1

# Create DataFrame for seaborn heatmap
rows, cols = np.meshgrid(range(grid_size), range(grid_size), indexing="ij")
df = pd.DataFrame({"row": rows.flatten(), "col": cols.flatten(), "category": grid.flatten()})

# Create plot (square format better for waffle chart)
fig, ax = plt.subplots(figsize=(12, 12))

# Use seaborn to create the visualization
# Create a pivot table for the heatmap-style display
pivot_data = df.pivot(index="row", columns="col", values="category")

# Create custom colormap from our colors
cmap = ListedColormap(colors)

# Plot using seaborn heatmap
sns.heatmap(
    pivot_data,
    cmap=cmap,
    vmin=0,
    vmax=len(categories) - 1,
    cbar=False,
    linewidths=2,
    linecolor="white",
    square=True,
    ax=ax,
)

# Y-axis naturally fills from bottom-left going up (like filling a glass)

# Remove axis labels and ticks
ax.set_xlabel("")
ax.set_ylabel("")
ax.set_xticks([])
ax.set_yticks([])

# Title
ax.set_title("waffle-basic · seaborn · pyplots.ai", fontsize=28, fontweight="bold", pad=20)

# Create legend with category names and percentages
legend_handles = [
    mpatches.Patch(color=colors[i], label=f"{categories[i]} ({values[i]}%)") for i in range(len(categories))
]
ax.legend(handles=legend_handles, loc="upper center", bbox_to_anchor=(0.5, -0.05), ncol=3, fontsize=18, frameon=False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
