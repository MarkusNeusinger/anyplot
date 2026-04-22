""" pyplots.ai
chessboard-basic: Chess Board Grid Visualization
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-08
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data - Create 8x8 chessboard pattern
# 0 = dark square, 1 = light square
# Standard chess: h1 (bottom-right) is light
board = np.zeros((8, 8))
for i in range(8):
    for j in range(8):
        # Light square when (row + col) is even
        if (i + j) % 2 == 0:
            board[i, j] = 1

# Column labels (a-h) and row labels (1-8)
columns = list("abcdefgh")
rows = list("12345678")[::-1]  # Reversed so 8 is at top

# Create figure with 1:1 aspect ratio
fig, ax = plt.subplots(figsize=(12, 12))

# Plot heatmap using seaborn
sns.heatmap(
    board,
    ax=ax,
    cmap=["#8B4513", "#F5DEB3"],  # Brown and cream (classic chess colors)
    cbar=False,
    square=True,
    linewidths=2,
    linecolor="#5D3A1A",
    xticklabels=columns,
    yticklabels=rows,
)

# Style adjustments
ax.set_xlabel("File", fontsize=24)
ax.set_ylabel("Rank", fontsize=24)
ax.set_title("chessboard-basic · seaborn · pyplots.ai", fontsize=28, pad=20)

# Make tick labels larger and position them correctly
ax.tick_params(axis="both", labelsize=20, length=0)
ax.xaxis.set_ticks_position("bottom")
ax.xaxis.set_label_position("bottom")

# Move x-axis ticks to center of squares
ax.set_xticks([i + 0.5 for i in range(8)])
ax.set_xticklabels(columns)
ax.set_yticks([i + 0.5 for i in range(8)])
ax.set_yticklabels(rows)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
