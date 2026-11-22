"""anyplot.ai
crossword-basic: Crossword Puzzle Grid
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-20
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

# Imprint palette (not needed for the monochrome grid; cell colors below are theme-adaptive)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

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
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Data: a 15x15 pinwheel layout; "#" marks a blocked cell, "." an entry cell.
# The pattern is 4-fold rotational (so also 180-degree symmetric) but not mirror-symmetric.
LAYOUT = [
    "...###....#....",
    "...#...........",
    "...#...........",
    "......##....###",
    "#...#.....#...#",
    "..............#",
    "...........#...",
    "...#.......#...",
    "...#...........",
    "#..............",
    "#...#.....#...#",
    "###....##......",
    "...........#...",
    "...........#...",
    "....#....###...",
]
grid = np.array([[1 if ch == "#" else 0 for ch in row] for row in LAYOUT])

# Plot: everything below derives from the grid
grid_size = len(grid)

# Clue numbers for cells that start an across or a down word, in reading order
numbers = {}
clue_num = 1
for r in range(grid_size):
    for c in range(grid_size):
        if grid[r, c] == 1:
            continue
        starts_across = (c == 0 or grid[r, c - 1] == 1) and (c < grid_size - 1 and grid[r, c + 1] == 0)
        starts_down = (r == 0 or grid[r - 1, c] == 1) and (r < grid_size - 1 and grid[r + 1, c] == 0)
        if starts_across or starts_down:
            numbers[(r, c)] = clue_num
            clue_num += 1

# Open cells are white, blocked cells solid black (pure black on dark so they stay darker than the page)
cell_open = "#FFFFFF" if THEME == "light" else "#FAF8F1"
cell_blocked = "#1A1A17" if THEME == "light" else "#000000"
NUMBER_INK = "#1A1A17"

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)

sns.heatmap(
    grid,
    ax=ax,
    cmap=sns.color_palette([cell_open, cell_blocked]),
    cbar=False,
    square=True,
    linewidths=1.0,
    linecolor=INK_SOFT,
    xticklabels=False,
    yticklabels=False,
)

# Clue numbers in the top-left corner of numbered cells
for (r, c), num in numbers.items():
    ax.text(c + 0.12, r + 0.28, str(num), fontsize=9, fontweight="bold", color=NUMBER_INK, ha="left", va="top")

# Style
ax.set_title("crossword-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=14)

for spine in ax.spines.values():
    spine.set_visible(True)
    spine.set_color(INK_SOFT)
    spine.set_linewidth(1.5)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
