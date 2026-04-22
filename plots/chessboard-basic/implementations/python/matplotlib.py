""" pyplots.ai
chessboard-basic: Chess Board Grid Visualization
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 95/100 | Created: 2026-01-08
"""

import matplotlib.pyplot as plt


# Board configuration
rows = 8
cols = 8
column_labels = ["a", "b", "c", "d", "e", "f", "g", "h"]
row_labels = ["1", "2", "3", "4", "5", "6", "7", "8"]

# Classic chess colors (cream and brown)
light_color = "#F0D9B5"
dark_color = "#B58863"

# Create figure (square aspect ratio for chess board)
fig, ax = plt.subplots(figsize=(12, 12))

# Draw the chess board squares
for row in range(rows):
    for col in range(cols):
        # h1 (col=7, row=0) should be light, so (row + col) even = light
        color = light_color if (row + col) % 2 == 1 else dark_color
        rect = plt.Rectangle((col, row), 1, 1, facecolor=color, edgecolor="#5D4037", linewidth=1)
        ax.add_patch(rect)

# Set axis limits
ax.set_xlim(0, 8)
ax.set_ylim(0, 8)

# Set column labels (a-h) at the bottom
ax.set_xticks([i + 0.5 for i in range(8)])
ax.set_xticklabels(column_labels, fontsize=20, fontweight="bold")

# Set row labels (1-8) on the left side
ax.set_yticks([i + 0.5 for i in range(8)])
ax.set_yticklabels(row_labels, fontsize=20, fontweight="bold")

# Style the axis
ax.tick_params(axis="both", length=0, pad=10)
ax.set_aspect("equal")

# Remove spines and add a border
for spine in ax.spines.values():
    spine.set_visible(True)
    spine.set_linewidth(3)
    spine.set_color("#5D4037")

# Title
ax.set_title("chessboard-basic · matplotlib · pyplots.ai", fontsize=24, fontweight="bold", pad=20)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
