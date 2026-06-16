""" anyplot.ai
scatter-regression-lowess: Scatter Plot with LOWESS Regression
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-14
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

# Okabe-Ito palette
BRAND = "#009E73"  # Position 1 - scatter points
REGRESSION = "#C475FD"  # Position 2 - LOWESS curve

# Configure theme
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

# Data - create non-linear relationship with distinct local variations
np.random.seed(42)
n_points = 200
x = np.linspace(0, 10, n_points)

# Complex pattern: steep rise 0-2, plateau 2-5, sharp dip 5-6, gentle rise 6-10
y = (
    np.where(x < 2, 3 * x, 6)
    + np.where((x >= 2) & (x < 5), 0, 0)
    + np.where((x >= 5) & (x < 6), -4 * (x - 5), 0)
    + np.where(x >= 6, 0.5 * (x - 6), 0)
    + np.random.normal(0, 0.6, n_points)
)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)

# Scatter plot with LOWESS regression
sns.regplot(
    x=x,
    y=y,
    lowess=True,
    scatter_kws={"alpha": 0.6, "s": 100, "color": BRAND, "edgecolors": PAGE_BG, "linewidths": 0.5},
    line_kws={"color": REGRESSION, "linewidth": 4},
    ax=ax,
)

# Styling
ax.set_xlabel("Input Variable (x)", fontsize=20, color=INK)
ax.set_ylabel("Response Variable (y)", fontsize=20, color=INK)
ax.set_title("scatter-regression-lowess · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

# Subtle grid
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
