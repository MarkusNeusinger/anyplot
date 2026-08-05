"""anyplot.ai
line-multi: Multi-Line Comparison Plot
Library: seaborn 0.13.2 | Python 3.13.14
Quality: 49/100 | Updated: 2026-08-05
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

# Imprint palette (first series always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Configure seaborn theme
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

# Data: Monthly sales for 4 product lines over 12 months
np.random.seed(42)
months = np.arange(1, 13)
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Generate realistic sales patterns for different product categories
# Electronics: Strong growth with holiday spike
electronics = 50 + np.cumsum(np.random.randn(12) * 5 + 3)
electronics[10:] += 30  # Holiday boost

# Apparel: Seasonal with summer and winter peaks
apparel = 40 + 15 * np.sin(np.linspace(0, 2 * np.pi, 12)) + np.random.randn(12) * 3

# Home & Garden: Spring/summer peak
home_garden = 30 + 20 * np.sin(np.linspace(-np.pi / 2, 3 * np.pi / 2, 12)) + np.random.randn(12) * 4

# Sports: Steady with slight seasonal variation
sports = 35 + 5 * np.sin(np.linspace(0, 2 * np.pi, 12) + np.pi / 4) + np.cumsum(np.random.randn(12) * 2)

# April (index 3): Home & Garden and Sports would otherwise sit ~2 units apart on
# a ~140-unit axis, hiding one marker behind the other — nudge them apart
home_garden[3] -= 6
sports[3] += 4

# Create long-format DataFrame for seaborn
df = pd.DataFrame(
    {
        "Month": np.tile(months, 4),
        "Sales (thousands USD)": np.concatenate([electronics, apparel, home_garden, sports]),
        "Product Line": (["Electronics"] * 12 + ["Apparel"] * 12 + ["Home & Garden"] * 12 + ["Sports"] * 12),
    }
)

# Plot — canvas fixed at figsize x dpi = 3200x1800px (16:9), no bbox_inches='tight'
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Soft underlay glow behind Electronics to sharpen its lead-series hierarchy
ax.plot(months, electronics, color=IMPRINT[0], linewidth=6, alpha=0.16, solid_capstyle="round", zorder=1)

sns.lineplot(
    data=df,
    x="Month",
    y="Sales (thousands USD)",
    hue="Product Line",
    style="Product Line",
    markers=True,
    dashes=False,
    linewidth=2.5,
    markersize=8,
    markeredgecolor=PAGE_BG,
    markeredgewidth=1.3,
    errorbar=None,
    palette=IMPRINT,
    ax=ax,
    zorder=2,
)

# Callout: the holiday spike is the clearest story beat in the data
ax.annotate(
    "Holiday season lifts\nElectronics sharply",
    xy=(12, electronics[-1]),
    xytext=(9.65, electronics[-1] + 14),
    fontsize=8,
    color=INK_SOFT,
    ha="left",
    arrowprops={"arrowstyle": "-", "color": INK_SOFT, "linewidth": 1},
    bbox={"boxstyle": "round,pad=0.3", "facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "linewidth": 0.8},
)

# Styling
title = "line-multi · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", pad=14, color=INK)
ax.set_xlabel("Month", fontsize=10, color=INK)
ax.set_ylabel("Sales (thousands USD)", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

# Set x-ticks to month names
ax.set_xticks(months)
ax.set_xticklabels(month_labels, fontsize=8)

# Subtle grid
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8)
ax.xaxis.grid(False)

# Refined L-shaped frame
sns.despine(ax=ax, offset=6, trim=False)

# Legend styling — sns.move_legend repositions seaborn's auto-built hue+style legend
sns.move_legend(ax, loc="upper left", title="Product Line", title_fontsize=9, fontsize=8, framealpha=0.95)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
