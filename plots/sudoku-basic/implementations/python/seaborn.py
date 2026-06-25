""" anyplot.ai
sudoku-basic: Basic Sudoku Grid
Library: seaborn 0.13.2 | Python 3.13.14
Quality: 92/100 | Updated: 2026-06-25
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.colors import ListedColormap


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
# Extended tonal palette for alternating box shading (monochrome, warm-toned)
BOX_SHADE = "#EDE8DB" if THEME == "light" else "#242422"  # alternate 3×3 box fill
CLUE_BG = "#DDD8CB" if THEME == "light" else "#2E2D29"  # given-number cell fill

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

# Three-level cell data: 0=empty+even-box, 0.5=empty+odd-box, 1=clue.
# Alternating box parity encodes the checkerboard 3×3 grouping directly in the data.
box_parity = np.array([[(r // 3 + c // 3) % 2 * 0.5 for c in range(9)] for r in range(9)], dtype=float)
cell_data = np.where(clue_mask == 1, 1.0, box_parity)
cmap = ListedColormap([PAGE_BG, BOX_SHADE, CLUE_BG])

# Theme-adaptive seaborn chrome (matches seaborn.md template)
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
        "grid.color": INK,
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Canvas: square 2400×2400 (symmetric 9×9 grid — no preferred horizontal axis)
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)

# Seaborn heatmap: ListedColormap with 3 warm-toned stops maps directly to cell types.
# Alternating box shading (even vs odd 3×3 boxes) reinforces the structural grouping
# without coloring — preserving the monochrome constraint while lifting design quality.
sns.heatmap(
    cell_data,
    annot=annotations,
    fmt="",
    cmap=cmap,
    cbar=False,
    linewidths=0.6,
    linecolor=INK_SOFT,
    square=True,
    xticklabels=False,
    yticklabels=False,
    vmin=0,
    vmax=1,
    annot_kws={"size": 16, "weight": "bold", "color": INK},
    ax=ax,
)

# Thick 3×3 box boundaries at linewidth=3 vs thin 0.6 → sharp thick/thin hierarchy
for k in range(4):
    ax.axhline(y=k * 3, color=INK, linewidth=3, clip_on=False)
    ax.axvline(x=k * 3, color=INK, linewidth=3, clip_on=False)

ax.set_title("sudoku-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=16)
ax.set_xticks([])
ax.set_yticks([])
ax.set_xlim(0, 9)
ax.set_ylim(9, 0)

plt.tight_layout()
# bbox_inches must stay default (None) — 'tight' silently trims the canvas
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
