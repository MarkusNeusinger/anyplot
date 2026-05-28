"""anyplot.ai
pie-basic: Basic Pie Chart
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-05-28
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

ANYPLOT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]

sns.set_theme(style="ticks", rc={"figure.facecolor": PAGE_BG, "axes.facecolor": PAGE_BG, "text.color": INK})

# Data — global cloud computing market share (2024 estimates)
categories = ["Amazon AWS", "Microsoft Azure", "Google Cloud", "Alibaba Cloud", "IBM Cloud", "Others"]
shares = [32, 22, 11, 6, 5, 24]
colors = ANYPLOT_PALETTE[:5] + [INK_MUTED]  # muted for "Others" (semantic anchor)

# Explode the largest slice (Amazon AWS at 32%)
explode = [0.06, 0, 0, 0, 0, 0]

# Plot — square canvas for symmetric pie chart
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
fig.subplots_adjust(top=0.90, bottom=0.18)

wedges, texts, autotexts = ax.pie(
    shares,
    labels=None,
    colors=colors,
    explode=explode,
    autopct="%1.0f%%",
    pctdistance=0.72,
    startangle=90,
    wedgeprops={"edgecolor": PAGE_BG, "linewidth": 2.0},
)

for autotext in autotexts:
    autotext.set_fontsize(8)
    autotext.set_color(INK)
    autotext.set_fontweight("medium")

# Style
title = "pie-basic · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK, pad=16)

legend = ax.legend(
    wedges,
    categories,
    loc="lower center",
    bbox_to_anchor=(0.5, -0.14),
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
