""" anyplot.ai
line-markers: Line Plot with Markers
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-21
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

# Imprint palette - first series always #009E73
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
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Columns: set these to your table's column names
DAY = "Day"  # role: x
Y = ["Price ($)"]  # role: y
STOCK = "Stock"  # role: series

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
days = np.arange(0, 60)
stock_a = 100 + 0.5 * days + np.random.normal(0, 1, 60)  # steady growth
stock_b = 95 + np.cumsum(np.random.normal(0, 2, 60))  # high volatility
stock_c = 110 + 0.1 * days + np.random.normal(0, 0.8, 60)  # stable

df = pd.DataFrame(
    {
        DAY: np.tile(days, 3),
        Y[0]: np.concatenate([stock_a, stock_b, stock_c]),
        STOCK: ["Stock A"] * 60 + ["Stock B"] * 60 + ["Stock C"] * 60,
    }
)

# Plot: reads only df and the constants above
n_series = df[STOCK].nunique()

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

sns.lineplot(
    data=df,
    x=DAY,
    y=Y[0],
    hue=STOCK,
    style=STOCK,
    markers=True,
    dashes=False,
    markersize=5,
    linewidth=1.3,
    markeredgecolor=PAGE_BG,
    markeredgewidth=0.5,
    palette=IMPRINT_PALETTE[:n_series],
    ax=ax,
)

# Style
ax.set_title("line-markers · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(DAY, fontsize=10, color=INK)
ax.set_ylabel(Y[0], fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
sns.despine(ax=ax)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.5, color=INK)
ax.legend(title=STOCK, fontsize=8, title_fontsize=8, framealpha=0.8, loc="upper left")

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
