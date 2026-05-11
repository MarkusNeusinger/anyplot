"""anyplot.ai
histogram-cumulative: Cumulative Histogram
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-05-11
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data - Financial transaction amounts (realistic e-commerce scenario)
np.random.seed(42)
transactions = np.concatenate(
    [
        np.random.exponential(scale=25, size=400),  # Small purchases (majority)
        np.random.normal(loc=120, scale=25, size=150),  # Medium purchases
        np.random.normal(loc=300, scale=60, size=50),  # Large purchases
    ]
)
transactions = np.clip(transactions, 5, 500)

# Plot
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

fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)

sns.histplot(
    transactions,
    bins=35,
    cumulative=True,
    stat="proportion",
    element="step",
    fill=True,
    color=BRAND,
    alpha=0.7,
    linewidth=2.5,
    edgecolor=BRAND,
    ax=ax,
)

# Style
ax.set_xlabel("Transaction Amount ($)", fontsize=20, color=INK)
ax.set_ylabel("Cumulative Proportion", fontsize=20, color=INK)
ax.set_title("histogram-cumulative · seaborn · anyplot.ai", fontsize=24, color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.set_xlim(0, 500)
ax.set_ylim(0, 1.05)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
