""" anyplot.ai
line-stepwise: Step Line Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-13
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

# Set seaborn theme BEFORE creating figure
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

# Data - Stock price stepping over trading days
np.random.seed(42)
days = np.arange(0, 31)
# Simulate intraday price with discrete closing steps
base_price = np.array(
    [
        150.00,
        150.00,
        150.00,
        152.50,
        152.50,
        152.50,
        155.00,
        155.00,
        155.00,
        153.25,
        153.25,
        153.25,
        156.75,
        156.75,
        156.75,
        158.50,
        158.50,
        159.25,
        159.25,
        159.25,
        161.00,
        161.00,
        161.00,
        159.50,
        159.50,
        162.00,
        162.00,
        162.00,
        164.50,
        164.50,
        163.75,
    ]
)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Step line plot using seaborn lineplot with drawstyle
sns.lineplot(
    x=days,
    y=base_price,
    ax=ax,
    drawstyle="steps-post",
    linewidth=3,
    color=BRAND,
    marker="o",
    markersize=8,
    markerfacecolor=BRAND,
    markeredgecolor=PAGE_BG,
    markeredgewidth=1,
)

# Style
ax.set_xlabel("Trading Day", fontsize=20, color=INK)
ax.set_ylabel("Stock Price ($)", fontsize=20, color=INK)
ax.set_title("line-stepwise · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Set axis limits
ax.set_xlim(-1, 30)
ax.set_ylim(145, 170)

# Remove spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Grid - subtle y-axis only
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
