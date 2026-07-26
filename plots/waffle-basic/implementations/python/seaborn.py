""" anyplot.ai
waffle-basic: Basic Waffle Chart
Library: seaborn 0.13.2 | Python 3.13.14
Quality: 89/100 | Updated: 2026-07-26
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import ListedColormap


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

sns.set_theme(
    style="white",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "text.color": INK,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Data - customer satisfaction survey (n=500 respondents)
categories = ["Very Satisfied", "Satisfied", "Neutral", "Dissatisfied", "Very Dissatisfied"]
values = [42, 31, 15, 8, 4]  # Percentages, sum to 100

# Imprint categorical palette — canonical order, first series always #009E73 (brand)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]
colors = IMPRINT_PALETTE[: len(categories)]

# Grid dimensions (10x10 = 100 squares, each square = 1%)
grid_size = 10
total_squares = grid_size * grid_size

# Fill bottom-to-top, left-to-right within each row (like filling a glass)
grid = np.zeros((grid_size, grid_size), dtype=int)
square_idx = 0
for cat_idx, value in enumerate(values):
    for _ in range(value):
        row = grid_size - 1 - (square_idx // grid_size)
        col = square_idx % grid_size
        grid[row, col] = cat_idx
        square_idx += 1

rows, cols = np.meshgrid(range(grid_size), range(grid_size), indexing="ij")
df = pd.DataFrame({"row": rows.flatten(), "col": cols.flatten(), "category": grid.flatten()})
pivot_data = df.pivot(index="row", columns="col", values="category")

# Square canvas (10x10 grid is symmetric) — 6in x 6in @ dpi=400 -> 2400x2400 px.
# No bbox_inches='tight' / tight_layout(): manual axes placement keeps the canvas exact.
fig = plt.figure(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)

# Square axes, centered horizontally, room reserved above for title/caption and
# below for the legend.
ax = fig.add_axes([0.19, 0.20, 0.62, 0.62])
ax.set_facecolor(PAGE_BG)

cmap = ListedColormap(colors)
sns.heatmap(
    pivot_data,
    cmap=cmap,
    vmin=0,
    vmax=len(categories) - 1,
    cbar=False,
    linewidths=2.5,
    linecolor=PAGE_BG,
    square=True,
    ax=ax,
)

ax.set_xlabel("")
ax.set_ylabel("")
ax.set_xticks([])
ax.set_yticks([])
sns.despine(ax=ax, left=True, bottom=True, top=True, right=True)  # clean floating grid, no frame

# Title
fig.text(0.5, 0.95, "waffle-basic · seaborn · anyplot.ai", ha="center", fontsize=12, fontweight="bold", color=INK)

# Caption — spells out the waffle-chart metaphor (each square = one unit of the whole)
fig.text(0.5, 0.885, "Each square = 1% of 500 survey respondents", ha="center", fontsize=8, color=INK_MUTED)

# Legend with category names and percentages
legend_handles = [
    mpatches.Patch(facecolor=colors[i], edgecolor=PAGE_BG, label=f"{categories[i]} ({values[i]}%)")
    for i in range(len(categories))
]
fig.legend(
    handles=legend_handles,
    loc="lower center",
    bbox_to_anchor=(0.5, 0.03),
    ncol=3,
    fontsize=8,
    frameon=False,
    labelcolor=INK,
)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
