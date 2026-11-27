"""anyplot.ai
density-basic: Basic Density Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-30
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens — Imprint palette + theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1 — always first series

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Columns: set these to your table's column names
BATTERY_LIFE = "Battery life (hours)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("batteries.csv")
rng = np.random.default_rng(42)
df = pd.DataFrame({BATTERY_LIFE: rng.gamma(shape=6, scale=1.5, size=500) + 2})

# Plot: reads only df and the constants above
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# KDE with native seaborn fill; cut=2 lets the tails fall to zero near the data range
sns.kdeplot(data=df, x=BATTERY_LIFE, ax=ax, fill=True, alpha=0.35, color=BRAND, linewidth=2.5, bw_adjust=0.9, cut=2)

# Rug plot showing individual observations
sns.rugplot(data=df, x=BATTERY_LIFE, ax=ax, color=BRAND, alpha=0.3, height=0.04)

title = "density-basic · python · seaborn · anyplot.ai"
n = len(title)
ratio = 67 / n if n > 67 else 1.0
title_fontsize = max(8, round(12 * ratio))

ax.set_ylabel("Density", fontsize=10, color=INK)
ax.set_xlabel(BATTERY_LIFE, fontsize=10, color=INK)
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)
ax.set_ylim(bottom=0)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8)

plt.tight_layout()
# No bbox_inches='tight' — preserves exact 3200×1800 canvas
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
