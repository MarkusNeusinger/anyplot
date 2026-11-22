"""anyplot.ai
mosaic-categorical: Mosaic Plot for Categorical Association Analysis
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-19
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
from statsmodels.graphics.mosaicplot import mosaic


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per outcome level in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
PASSENGER_CLASS = "Passenger Class"  # role: category_1
OUTCOME = "Survival Status"  # role: category_2
PASSENGERS = "Passengers"  # role: frequency

# Data: replace this block with your own table, for example df = pd.read_csv("titanic_counts.csv")
df = pd.DataFrame(
    {
        PASSENGER_CLASS: ["First", "First", "Second", "Second", "Third", "Third"],
        OUTCOME: ["Survived", "Did Not Survive"] * 3,
        PASSENGERS: [136, 64, 87, 93, 119, 381],
    }
)

# Plot
levels = list(df[OUTCOME].unique())
level_colors = {str(level): IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, level in enumerate(levels)}
table = df.groupby([PASSENGER_CLASS, OUTCOME], sort=False)[PASSENGERS].sum()
counts = {(str(c), str(o)): n for (c, o), n in table.items()}

title = "Titanic Passenger Survival · mosaic-categorical · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

mosaic(
    counts,
    ax=ax,
    gap=0.015,
    properties=lambda key: {"facecolor": level_colors[key[1]], "edgecolor": PAGE_BG, "linewidth": 1.5},
    labelizer=lambda key: str(counts.get(key, "")),
    title="",
    axes_label=True,
    statistic=False,
)

# Count labels: white for contrast against the colored cells
for text in ax.texts:
    text.set_color("white")
    text.set_fontsize(10)
    text.set_fontweight("bold")

# Style
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=10)
ax.set_xlabel(PASSENGER_CLASS, fontsize=10, color=INK, labelpad=6)
ax.set_ylabel(OUTCOME, fontsize=10, color=INK, labelpad=6)
ax.tick_params(length=0, labelcolor=INK_SOFT, labelsize=8)
for spine in ax.spines.values():
    spine.set_color(INK_SOFT)

legend_handles = [
    mpatches.Patch(facecolor=color, edgecolor=INK_SOFT, linewidth=0.8, label=level)
    for level, color in level_colors.items()
]
leg = ax.legend(handles=legend_handles, title=OUTCOME, loc="upper right", fontsize=8, title_fontsize=8)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)
leg.get_title().set_color(INK_SOFT)

fig.subplots_adjust(left=0.15, right=0.97, top=0.9, bottom=0.11)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
