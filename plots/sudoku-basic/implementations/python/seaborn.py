""" anyplot.ai
sudoku-basic: Basic Sudoku Grid
Library: seaborn 0.13.2 | Python 3.14.4
Quality: 90/100 | Updated: 2026-04-24
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data (classic Sudoku puzzle; 0 = empty cell)
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
clue_mask = (grid > 0).astype(float)
annotations = np.where(grid == 0, "", grid.astype(str))

# Theme-adaptive seaborn chrome
sns.set_theme(
    style="white",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
    },
)

# Plot
fig, ax = plt.subplots(figsize=(12, 12), facecolor=PAGE_BG)

# Seaborn renders the full grid: cell fills (subtle clue vs. empty contrast),
# thin cell separators, and the digits themselves via `annot`.
sns.heatmap(
    clue_mask,
    annot=annotations,
    fmt="",
    cmap=[PAGE_BG, ELEVATED_BG],
    cbar=False,
    linewidths=1.2,
    linecolor=INK_SOFT,
    square=True,
    xticklabels=False,
    yticklabels=False,
    vmin=0,
    vmax=1,
    annot_kws={"size": 34, "weight": "bold", "color": INK},
    ax=ax,
)

# Thick 3x3 box boundaries (full outer frame + interior dividers)
for k in range(4):
    ax.axhline(y=k * 3, color=INK, linewidth=5, clip_on=False)
    ax.axvline(x=k * 3, color=INK, linewidth=5, clip_on=False)

# Style
ax.set_title("sudoku-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=24)
ax.set_xticks([])
ax.set_yticks([])
ax.set_xlim(0, 9)
ax.set_ylim(9, 0)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
