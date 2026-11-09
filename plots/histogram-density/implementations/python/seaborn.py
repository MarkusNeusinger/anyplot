"""anyplot.ai
histogram-density: Density Histogram
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-09
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: histogram bars take position 1, the KDE curve position 2
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

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
TEST_SCORE = "Test Score (points)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
np.random.seed(42)
group1 = np.random.normal(loc=65, scale=10, size=300)  # Average performers
group2 = np.random.normal(loc=85, scale=5, size=200)  # High performers
df = pd.DataFrame({TEST_SCORE: np.clip(np.concatenate([group1, group2]), 0, 100)})

# Plot: reads only df and the constants above
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

sns.histplot(
    data=df,
    x=TEST_SCORE,
    stat="density",
    bins=25,
    color=IMPRINT_PALETTE[0],
    alpha=0.75,
    edgecolor=PAGE_BG,
    linewidth=0.8,
    ax=ax,
    label="Density histogram",
)
sns.kdeplot(
    data=df, x=TEST_SCORE, cut=0, ax=ax, color=IMPRINT_PALETTE[1], linewidth=2.5, label="Kernel density estimate (KDE)"
)

# Style
title = "histogram-density · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=round(12 * min(1.0, 67 / len(title))), fontweight="medium", color=INK)
ax.set_xlabel(TEST_SCORE, fontsize=10)
ax.set_ylabel("Probability Density", fontsize=10)
ax.tick_params(axis="both", labelsize=8)
ax.yaxis.grid(True, linewidth=0.8)
ax.set_axisbelow(True)
sns.despine(ax=ax)
ax.legend(fontsize=8, loc="upper left")

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
