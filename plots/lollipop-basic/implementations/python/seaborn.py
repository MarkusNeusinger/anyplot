""" anyplot.ai
lollipop-basic: Basic Lollipop Chart
Library: seaborn 0.13.2 | Python 3.13.14
Quality: 90/100 | Updated: 2026-07-01
"""

import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1

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

# Data - Product sales by category
categories = [
    "Electronics",
    "Clothing",
    "Home & Garden",
    "Sports",
    "Books",
    "Toys",
    "Beauty",
    "Automotive",
    "Food & Grocery",
    "Health",
]
values = [85000, 72000, 58000, 45000, 42000, 38000, 35000, 28000, 25000, 18000]

df = pd.DataFrame({"category": categories, "value": values}).sort_values("value", ascending=True)

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Stems: thin lines from baseline to marker
ax.hlines(y=df["category"], xmin=0, xmax=df["value"], color=BRAND, linewidth=2.0, alpha=0.8, zorder=2)

# Markers: size mapped to value via seaborn size aesthetic — larger dots for higher sales
sns.scatterplot(
    data=df,
    x="value",
    y="category",
    size="value",
    sizes=(60, 200),
    color=BRAND,
    edgecolor=PAGE_BG,
    linewidth=1.5,
    ax=ax,
    zorder=3,
    legend=False,
)

# Style
title = "lollipop-basic · python · seaborn · anyplot.ai"
ax.set_xlabel("Sales ($)", fontsize=10, color=INK)
ax.set_ylabel("Product Category", fontsize=10, color=INK)
ax.set_title(title, fontsize=12, fontweight="medium", color=INK, pad=12)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.set_xlim(0, max(values) * 1.08)

ax.xaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.yaxis.grid(False)
ax.set_axisbelow(True)

sns.despine(ax=ax)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
