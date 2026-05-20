""" anyplot.ai
crossword-basic: Crossword Puzzle Grid
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-20
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

# Data: 15x15 crossword grid with 180-degree rotational symmetry
grid_size = 15
grid = np.zeros((grid_size, grid_size), dtype=int)

blocked_positions = [
    (0, 4),
    (0, 10),
    (1, 4),
    (1, 10),
    (2, 7),
    (3, 0),
    (3, 6),
    (3, 11),
    (3, 12),
    (3, 13),
    (3, 14),
    (4, 3),
    (4, 8),
    (5, 5),
    (5, 9),
    (5, 14),
    (6, 2),
    (6, 6),
    (6, 10),
    (7, 7),
]

for r, c in blocked_positions:
    grid[r, c] = 1
    grid[grid_size - 1 - r, grid_size - 1 - c] = 1

# Calculate clue numbers for cells that start across or down words
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

# Cell colors: open cells are warm white, blocked cells near-black (data encoding)
# Dark mode: use pure black for blocked cells so they contrast with #1A1A17 background
cell_open = "#FFFFFF" if THEME == "light" else "#FAF8F1"
cell_blocked = "#1A1A17" if THEME == "light" else "#000000"
NUMBER_INK = "#1A1A17"

# Plot
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)

cmap = sns.color_palette([cell_open, cell_blocked])
sns.heatmap(
    grid,
    ax=ax,
    cmap=cmap,
    cbar=False,
    square=True,
    linewidths=1.0,
    linecolor=INK_SOFT,
    xticklabels=False,
    yticklabels=False,
)

# Add clue numbers to top-left corner of numbered cells
for (r, c), num in numbers.items():
    ax.text(c + 0.12, r + 0.28, str(num), fontsize=9, fontweight="bold", color=NUMBER_INK, ha="left", va="top")

# Style
ax.set_title("crossword-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=14)

for spine in ax.spines.values():
    spine.set_visible(True)
    spine.set_color(INK_SOFT)
    spine.set_linewidth(1.5)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, bbox_inches="tight", facecolor=PAGE_BG)
