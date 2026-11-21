"""anyplot.ai
histogram-cumulative: Cumulative Histogram
Library: seaborn 0.13.2 | Python 3.14.9
Quality: 89/100 | Updated: 2026-11-21
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: single series uses the first position
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
        "grid.alpha": 0.10,
    },
)

# Columns: set these to your table's column names
AMOUNT = "Transaction amount ($)"  # role: numeric

# Data: replace this block with your own table, for example df = pd.read_csv("transactions.csv")
np.random.seed(42)
amounts = np.concatenate(
    [
        np.random.exponential(scale=25, size=400),  # small purchases (majority)
        np.random.normal(loc=120, scale=25, size=150),  # medium purchases
        np.random.normal(loc=300, scale=60, size=50),  # large purchases
    ]
)
df = pd.DataFrame({AMOUNT: np.clip(amounts, 5, 500)})

# Plot: reads only df and the constants above
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

sns.histplot(
    data=df,
    x=AMOUNT,
    bins=35,
    cumulative=True,
    stat="proportion",
    element="step",
    fill=True,
    color=IMPRINT_PALETTE[0],
    alpha=0.7,
    linewidth=1.4,
    edgecolor=IMPRINT_PALETTE[0],
    ax=ax,
)

# Style
title = "histogram-cumulative · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(AMOUNT, fontsize=10, color=INK)
ax.set_ylabel("Cumulative proportion", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.set_xlim(0, df[AMOUNT].max())
ax.set_ylim(0, 1.05)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8)
sns.despine(ax=ax)
fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
