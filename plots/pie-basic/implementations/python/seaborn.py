"""anyplot.ai
pie-basic: Basic Pie Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 84/100 | Created: 2026-05-28
"""

import os

import matplotlib.pyplot as plt
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# seaborn palette API — set_palette registers the anyplot hues globally; color_palette
# retrieves them as a seaborn ColorPalette object for direct indexing
ANYPLOT_HEX = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "text.color": INK,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)
sns.set_palette(ANYPLOT_HEX)
palette = sns.color_palette(ANYPLOT_HEX)  # ColorPalette object for slice color access

# Data — global cloud computing market share (2024 estimates)
categories = ["Amazon AWS", "Microsoft Azure", "Google Cloud", "Alibaba Cloud", "IBM Cloud", "Others"]
shares = [32, 22, 11, 6, 5, 24]
colors = list(palette[:5]) + [INK_MUTED]  # muted anchor for catch-all "Others"
explode = [0.06, 0, 0, 0, 0, 0]

# Square canvas for symmetric donut chart
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
fig.subplots_adjust(top=0.88, bottom=0.14)

# Donut chart — width=0.65 hollows the center; pctdistance=0.78 centers labels in the ring
wedges, texts, autotexts = ax.pie(
    shares,
    labels=None,
    colors=colors,
    explode=explode,
    autopct="%1.0f%%",
    pctdistance=0.78,
    startangle=90,
    wedgeprops={"edgecolor": PAGE_BG, "linewidth": 2.0, "width": 0.65},
)

for autotext in autotexts:
    autotext.set_fontsize(8)
    autotext.set_color(INK)
    autotext.set_fontweight("medium")

# Center annotation — market context label in the donut hole
ax.text(
    0,
    0,
    "Cloud\nMarket\n2024",
    ha="center",
    va="center",
    fontsize=9,
    color=INK_SOFT,
    fontweight="medium",
    linespacing=1.4,
)

# Title and legend
title = "pie-basic · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="bold", color=INK, pad=14)

legend = ax.legend(
    wedges,
    categories,
    loc="lower center",
    bbox_to_anchor=(0.5, -0.08),
    ncol=3,
    fontsize=8,
    frameon=True,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
)
for text in legend.get_texts():
    text.set_color(INK_SOFT)

# Save — do NOT use bbox_inches='tight' (seaborn canvas contract)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
