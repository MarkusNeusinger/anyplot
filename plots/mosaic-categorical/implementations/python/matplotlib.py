""" anyplot.ai
mosaic-categorical: Mosaic Plot for Categorical Association Analysis
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-19
"""

import os
import sys


sys.path = [p for p in sys.path if "implementations" not in p]  # noqa: E402

import matplotlib.patches as mpatches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from statsmodels.graphics.mosaicplot import mosaic  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette — first series always #009E73
CELL_COLORS = {"Survived": "#009E73", "Did Not Survive": "#C475FD"}

# Data: Titanic passenger survival by class (realistic proportions)
counts = {
    ("First", "Survived"): 136,
    ("First", "Did Not Survive"): 64,
    ("Second", "Survived"): 87,
    ("Second", "Did Not Survive"): 93,
    ("Third", "Survived"): 119,
    ("Third", "Did Not Survive"): 381,
}

# Plot: core mosaic via statsmodels
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

fig, rects = mosaic(
    counts,
    ax=ax,
    gap=0.015,
    properties=lambda key: {"facecolor": CELL_COLORS[key[1]], "edgecolor": PAGE_BG, "linewidth": 3},
    labelizer=lambda key: str(counts[key]),
    title="",
    axes_label=True,
    statistic=False,
)

# Style cell count labels (white for contrast against colored cells)
for text in ax.texts:
    text.set_color("white")
    text.set_fontsize(20)
    text.set_fontweight("bold")

# Style
ax.set_title(
    "Titanic Passenger Survival · mosaic-categorical · python · matplotlib · anyplot.ai",
    fontsize=24,
    fontweight="medium",
    color=INK,
    pad=20,
)
ax.set_xlabel("Passenger Class", fontsize=20, color=INK, labelpad=12)
ax.set_ylabel("Survival Status", fontsize=20, color=INK, labelpad=12)
ax.tick_params(length=0, labelcolor=INK_SOFT, labelsize=14)

for spine in ax.spines.values():
    spine.set_color(INK_SOFT)

# Legend
legend_handles = [
    mpatches.Patch(facecolor=color, edgecolor=INK_SOFT, linewidth=1.5, label=label)
    for label, color in CELL_COLORS.items()
]
leg = ax.legend(handles=legend_handles, loc="upper right", fontsize=16)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

# Save
plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
