"""anyplot.ai
waffle-basic: Basic Waffle Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 91/100 | Updated: 2026-07-26
"""

import os

import matplotlib.patches as mpatches
import matplotlib.patheffects as patheffects
import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (canonical order)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Survey responses (sums to 100%)
categories = ["Strongly Agree", "Agree", "Neutral", "Disagree"]
values = [48, 32, 15, 5]
dominant = int(np.argmax(values))

# Build a 10x10 grid (100 squares, each = 1%), filled category by category
grid_size = 10
grid = np.zeros(grid_size * grid_size, dtype=int)
start = 0
for i, val in enumerate(values):
    grid[start : start + val] = i
    start += val
grid = grid.reshape((grid_size, grid_size))

# Square canvas (2400x2400) - waffle charts are grid-based/symmetric, no preferred axis
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
# Pin the axes to a literal square in figure-inch space so set_aspect("equal")
# never has to auto-shrink the box, keeping title/subtitle/legend placement predictable.
ax.set_position([0.13, 0.14, 0.74, 0.74])

# Draw squares with a soft drop shadow for depth; the dominant category gets an
# ink-toned outline instead of a background-blended one, a quiet emphasis cue
# that draws the eye to the largest segment without adding overlapping text.
square_size = 0.86
gap = (1 - square_size) / 2
for row in range(grid_size):
    for col in range(grid_size):
        cat = int(grid[row, col])
        emphasize = cat == dominant
        rect = mpatches.FancyBboxPatch(
            (col + gap, row + gap),
            square_size,
            square_size,
            boxstyle="round,pad=0.015,rounding_size=0.09",
            facecolor=IMPRINT[cat],
            edgecolor=INK_SOFT if emphasize else PAGE_BG,
            linewidth=2.2 if emphasize else 1.3,
        )
        rect.set_path_effects(
            [patheffects.withSimplePatchShadow(offset=(1.0, -1.0), shadow_rgbFace=INK, alpha=0.2), patheffects.Normal()]
        )
        ax.add_patch(rect)

ax.set_xlim(0, grid_size)
ax.set_ylim(0, grid_size)
ax.set_aspect("equal")
ax.axis("off")

# Legend with percentage labels, centered under the grid
legend_patches = [
    mpatches.Patch(facecolor=IMPRINT[i], label=f"{categories[i]} ({values[i]}%)") for i in range(len(categories))
]
leg = fig.legend(
    handles=legend_patches,
    loc="center",
    bbox_to_anchor=(0.5, 0.06),
    ncol=2,
    fontsize=8,
    frameon=True,
    fancybox=True,
    columnspacing=1.4,
    handletextpad=0.6,
)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.8)
plt.setp(leg.get_texts(), color=INK_SOFT)

# Title and subtitle (figure-level text, independent of the aspect-locked axes box)
fig.text(
    0.5,
    0.95,
    "waffle-basic · python · matplotlib · anyplot.ai",
    fontsize=12,
    fontweight="medium",
    color=INK,
    ha="center",
)
fig.text(0.5, 0.915, "Survey Response Distribution", fontsize=10, color=INK_SOFT, ha="center")

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
