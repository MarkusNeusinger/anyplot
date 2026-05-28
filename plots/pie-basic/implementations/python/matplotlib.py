""" anyplot.ai
pie-basic: Basic Pie Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-28
"""

import os

import matplotlib.pyplot as plt


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# anyplot categorical palette — positions 1→5
ANYPLOT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data — global cloud infrastructure market share (2024)
companies = ["AWS", "Azure", "Google Cloud", "Alibaba Cloud", "Others"]
market_share = [31, 25, 11, 4, 29]

# Explode the largest slice (AWS) for emphasis
explode = [0.06, 0, 0, 0, 0]

# Plot — square canvas, appropriate for pie charts
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

wedges, texts, autotexts = ax.pie(
    market_share,
    labels=companies,
    autopct="%1.1f%%",
    explode=explode,
    colors=ANYPLOT_PALETTE,
    startangle=90,
    textprops={"fontsize": 10, "color": INK},
    wedgeprops={"linewidth": 2, "edgecolor": PAGE_BG},
    pctdistance=0.7,
)

# Percentage labels: bold white for contrast against colored slices
for autotext in autotexts:
    autotext.set_fontsize(9)
    autotext.set_fontweight("bold")
    autotext.set_color("white")

# Title
title = "pie-basic · python · matplotlib · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK, pad=20)

# Legend — category identification
leg = ax.legend(
    wedges,
    companies,
    title="Cloud Providers",
    loc="lower center",
    bbox_to_anchor=(0.5, -0.08),
    fontsize=8,
    title_fontsize=9,
    ncol=3,
)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)
leg.get_title().set_color(INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
