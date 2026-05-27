""" anyplot.ai
line-markers: Line Plot with Markers
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 95/100 | Updated: 2026-05-12
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

# Okabe-Ito palette - first series always #009E73
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - Stock price tracking with different patterns
np.random.seed(42)
days = np.arange(0, 60)

# Three stocks with distinct patterns:
# Stock A - steady upward trend (growth stock)
stock_a = 100 + 0.5 * days + np.random.normal(0, 1, 60)

# Stock B - high volatility (volatile stock)
stock_b = 95 + np.cumsum(np.random.normal(0, 2, 60))

# Stock C - relatively stable (dividend stock)
stock_c = 110 + 0.1 * days + np.random.normal(0, 0.8, 60)

df = pd.DataFrame(
    {
        "Day": np.tile(days, 3),
        "Price ($)": np.concatenate([stock_a, stock_b, stock_c]),
        "Stock": ["Stock A"] * 60 + ["Stock B"] * 60 + ["Stock C"] * 60,
    }
)

# Set theme-adaptive styling
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

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)

sns.lineplot(
    data=df,
    x="Day",
    y="Price ($)",
    hue="Stock",
    style="Stock",
    markers=True,
    dashes=False,
    markersize=10,
    linewidth=2.5,
    palette=IMPRINT,
    ax=ax,
)

# Styling
ax.set_title("line-markers · seaborn · anyplot.ai", fontsize=24, fontweight="medium")
ax.set_xlabel("Day", fontsize=20, color=INK)
ax.set_ylabel("Price ($)", fontsize=20, color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

# Subtle grid on y-axis
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Legend with lower framealpha for visual appeal
ax.legend(fontsize=16, framealpha=0.5, loc="upper left", frameon=True)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
