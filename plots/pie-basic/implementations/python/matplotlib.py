"""anyplot.ai
pie-basic: Basic Pie Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-28
"""

import os

import matplotlib.pyplot as plt
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — positions 1→8
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
EXPLODE_OFFSET = 0.08

# Column names
PROVIDER = "Cloud provider"  # role: category
SHARE = "Market share (%)"  # role: value

# Data — global cloud infrastructure market share (2024)
df = pd.DataFrame({PROVIDER: ["AWS", "Azure", "Google Cloud", "Alibaba Cloud", "Others"], SHARE: [31, 25, 11, 4, 29]})

# Plot — square canvas, appropriate for pie charts
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Pull the largest slice out slightly for emphasis
explode = (df[SHARE] == df[SHARE].max()).astype(float) * EXPLODE_OFFSET

wedges, texts, autotexts = ax.pie(
    df[SHARE],
    labels=df[PROVIDER],
    autopct="%1.1f%%",
    explode=explode,
    colors=IMPRINT_PALETTE[: len(df)],
    startangle=90,
    textprops={"fontsize": 10, "color": INK},
    wedgeprops={"linewidth": 2, "edgecolor": PAGE_BG},
    pctdistance=0.72,
    labeldistance=1.15,
)

# Percentage labels: bold white for contrast against colored slices
for autotext in autotexts:
    autotext.set_fontsize(9)
    autotext.set_fontweight("bold")
    autotext.set_color("white")

ax.set_title("pie-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=10)

# Legend — category identification
leg = ax.legend(
    wedges,
    df[PROVIDER],
    title=PROVIDER,
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
