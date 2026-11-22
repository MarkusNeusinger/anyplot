""" anyplot.ai
chessboard-basic: Chess Board Grid Visualization
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-22
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

# Board colors (classic two-tone, identical in both themes)
LIGHT_SQUARE = "#FFF8DC"  # Cornsilk
DARK_SQUARE = "#A0522D"  # Sienna

# Library setup
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

# Data: board parameters (generated plot, no table)
N_FILES = 8  # columns, labeled a-h
N_RANKS = 8  # rows, labeled 1-8
files = list("abcdefgh"[:N_FILES])
ranks = [str(r) for r in range(N_RANKS, 0, -1)]  # rank 8 at the top

# Plot
# 1 = light square, 0 = dark square; row 0 is rank 8, so a8 and h1 come out light
row_idx, col_idx = np.indices((N_RANKS, N_FILES))
board = ((row_idx + col_idx) % 2 == 0).astype(int)

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)

sns.heatmap(
    board,
    ax=ax,
    cmap=[DARK_SQUARE, LIGHT_SQUARE],
    cbar=False,
    square=True,
    linewidths=1,
    linecolor=INK_SOFT,
    xticklabels=files,
    yticklabels=ranks,
)

# Style
ax.set_xlabel("File", fontsize=10, color=INK)
ax.set_ylabel("Rank", fontsize=10, color=INK)
ax.set_title("chessboard-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=10)
ax.tick_params(axis="both", labelsize=8, length=0, colors=INK_SOFT)
ax.tick_params(axis="y", labelrotation=0)
for spine in ax.spines.values():
    spine.set_color(INK_SOFT)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
