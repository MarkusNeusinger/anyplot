""" anyplot.ai
line-multi: Multi-Line Comparison Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-06
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

# Okabe-Ito palette (first series always #009E73)
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
        "grid.alpha": 0.10,
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

# Create long-format DataFrame for seaborn
df = pd.DataFrame(
    {
        "Month": np.tile(months, 4),
        "Sales (thousands USD)": np.concatenate([electronics, apparel, home_garden, sports]),
        "Product Line": (["Electronics"] * 12 + ["Apparel"] * 12 + ["Home & Garden"] * 12 + ["Sports"] * 12),
    }
)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

sns.lineplot(
    data=df,
    x="Month",
    y="Sales (thousands USD)",
    hue="Product Line",
    style="Product Line",
    markers=True,
    dashes=False,
    linewidth=3,
    markersize=12,
    palette=IMPRINT,
    ax=ax,
)

# Styling
ax.set_title("line-multi · seaborn · anyplot.ai", fontsize=24, fontweight="medium", pad=20, color=INK)
ax.set_xlabel("Month", fontsize=20, color=INK)
ax.set_ylabel("Sales (thousands USD)", fontsize=20, color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Set x-ticks to month names
ax.set_xticks(months)
ax.set_xticklabels(month_labels, fontsize=16)

# Subtle grid
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8)
ax.xaxis.grid(False)

# Legend styling
ax.legend(title="Product Line", title_fontsize=18, fontsize=16, loc="upper left", framealpha=0.95)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
