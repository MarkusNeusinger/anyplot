""" anyplot.ai
area-stacked-percent: 100% Stacked Area Chart
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-21
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import PercentFormatter


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
YEAR = "Year"  # role: time
SOURCE = "Source"  # role: category
GENERATION = "Electricity generation (TWh)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("generation.csv")
years = np.arange(2014, 2025)
mix = {
    "Solar": [0.8, 1.2, 1.8, 2.5, 3.3, 4.2, 5.4, 6.8, 8.2, 9.8, 11.5],
    "Wind": [2.1, 2.5, 3.0, 3.8, 4.6, 5.5, 6.8, 8.2, 9.6, 11.2, 13.0],
    "Hydro": [15.2, 15.5, 15.8, 16.2, 16.5, 16.8, 17.0, 17.1, 17.2, 17.3, 17.4],
    "Natural Gas": [42.1, 41.8, 41.2, 40.5, 39.8, 39.0, 37.5, 35.8, 34.0, 32.5, 31.0],
    "Coal": [39.8, 38.5, 37.2, 36.0, 35.8, 34.5, 33.3, 32.1, 31.0, 29.0, 27.1],
}
df = pd.DataFrame(
    {
        YEAR: np.tile(years, len(mix)),
        SOURCE: np.repeat(list(mix), len(years)),
        GENERATION: np.concatenate(list(mix.values())),
    }
)

# Plot: reads only df and the constants above
table = df.pivot_table(index=YEAR, columns=SOURCE, values=GENERATION, sort=False)
share = table.div(table.sum(axis=1), axis=0) * 100

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.stackplot(
    table.index,
    share.to_numpy().T,
    labels=share.columns,
    colors=IMPRINT_PALETTE,
    alpha=0.85,
    edgecolor=PAGE_BG,
    linewidth=0.8,
)

# Style
title = "area-stacked-percent · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK)
ax.set_xlabel(YEAR, fontsize=10, color=INK)
ax.set_ylabel("Share of electricity generation", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)

ax.set_xlim(table.index.min(), table.index.max())
ax.set_ylim(0, 100)
ax.set_xticks(table.index)
ax.yaxis.set_major_formatter(PercentFormatter(decimals=0))

ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Legend outside the plot area, listed top-to-bottom in stack order
handles, labels = ax.get_legend_handles_labels()
leg = ax.legend(
    handles[::-1], labels[::-1], title=SOURCE, loc="upper left", bbox_to_anchor=(1.02, 1), fontsize=8, title_fontsize=9
)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.8)
plt.setp(leg.get_texts(), color=INK_SOFT)
leg.get_title().set_color(INK)

fig.subplots_adjust(left=0.09, right=0.82, top=0.92, bottom=0.12)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
