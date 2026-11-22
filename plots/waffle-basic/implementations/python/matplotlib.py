""" anyplot.ai
waffle-basic: Basic Waffle Chart
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-22
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
GRID_SIZE = 10  # standard waffle grid: 10 x 10 squares, each square = 1% of the whole

# Columns: set these to your table's column names
CATEGORY = "Response"  # role: category
VALUE = "Share of respondents (%)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("survey.csv")
df = pd.DataFrame({CATEGORY: ["Strongly Agree", "Agree", "Neutral", "Disagree"], VALUE: [48, 32, 15, 5]})

# Plot: reads only df and the constants above
# Whole squares per category: largest-remainder rounding so the grid is exactly full
n_squares = GRID_SIZE * GRID_SIZE
exact = df[VALUE] / df[VALUE].sum() * n_squares
counts = np.floor(exact).astype(int)
extra = n_squares - counts.sum()
counts.iloc[np.argsort(-(exact - counts).to_numpy(), kind="stable")[:extra]] += 1

# Fill the grid block by block, one direction (row by row)
cell_category = np.repeat(np.arange(len(df)), counts.to_numpy())

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

square_size = 0.9  # slightly smaller than 1 for even gaps
for idx, category_idx in enumerate(cell_category):
    row, col = divmod(idx, GRID_SIZE)
    ax.add_patch(
        mpatches.FancyBboxPatch(
            (col + 0.05, GRID_SIZE - 1 - row + 0.05),
            square_size,
            square_size,
            boxstyle="round,pad=0.02,rounding_size=0.1",
            facecolor=IMPRINT_PALETTE[category_idx % len(IMPRINT_PALETTE)],
            edgecolor=PAGE_BG,
            linewidth=1.0,
        )
    )

ax.set_xlim(0, GRID_SIZE)
ax.set_ylim(0, GRID_SIZE)
ax.set_aspect("equal")
ax.axis("off")

# Legend below the grid, with percentages
legend_patches = [
    mpatches.Patch(color=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)], label=f"{name} ({value:g}%)")
    for i, (name, value) in enumerate(zip(df[CATEGORY], df[VALUE], strict=True))
]
leg = ax.legend(
    handles=legend_patches,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.03),
    ncol=2,
    fontsize=10,
    frameon=True,
    fancybox=True,
    title=f"{CATEGORY} (1 square = 1%)",
    title_fontsize=10,
)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.8)
plt.setp(leg.get_texts(), color=INK_SOFT)
leg.get_title().set_color(INK)

# Title scaled to its length
title = "Survey Response Distribution · waffle-basic · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(11 * 67 / len(title))) if len(title) > 67 else 11
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=14)

fig.subplots_adjust(left=0.06, right=0.94, top=0.92, bottom=0.17)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
