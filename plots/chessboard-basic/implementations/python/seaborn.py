"""anyplot.ai
chessboard-basic: Chess Board Grid Visualization
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-05-17
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Chess colors - distinct from other libraries (cornsilk and sienna)
LIGHT_SQUARE = "#FFF8DC"  # Cornsilk
DARK_SQUARE = "#A0522D"  # Sienna

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

# Set seaborn theme
sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
    },
)

# Create figure with 1:1 aspect ratio for square format
fig, ax = plt.subplots(figsize=(12, 12), facecolor=PAGE_BG)

# Plot heatmap using seaborn
sns.heatmap(
    board,
    ax=ax,
    cmap=[DARK_SQUARE, LIGHT_SQUARE],
    cbar=False,
    square=True,
    linewidths=2,
    linecolor=INK_SOFT,
    xticklabels=columns,
    yticklabels=rows,
)

# Style adjustments
ax.set_xlabel("File", fontsize=20, color=INK)
ax.set_ylabel("Rank", fontsize=20, color=INK)
ax.set_title("chessboard-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=20)

# Make tick labels larger and position them correctly
ax.tick_params(axis="both", labelsize=16, length=0, colors=INK_SOFT)
ax.xaxis.set_ticks_position("bottom")
ax.xaxis.set_label_position("bottom")

# Move x-axis ticks to center of squares
ax.set_xticks([i + 0.5 for i in range(8)])
ax.set_xticklabels(columns)
ax.set_yticks([i + 0.5 for i in range(8)])
ax.set_yticklabels(rows)

# Set spine colors for theme
for spine in ax.spines.values():
    spine.set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
