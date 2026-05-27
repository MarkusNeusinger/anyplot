""" anyplot.ai
bar-stacked-labeled: Stacked Bar Chart with Total Labels
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-18
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

# Okabe-Ito palette - first series is always #009E73
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

# Data - Quarterly revenue by product category (varied growth patterns)
np.random.seed(42)

categories = ["Q1", "Q2", "Q3", "Q4"]
components = ["Electronics", "Software", "Services", "Hardware"]

# Create data with realistic revenue values (in millions) with varied patterns
data = {
    "Electronics": [45, 52, 48, 61],
    "Software": [32, 38, 42, 55],
    "Services": [28, 31, 35, 40],
    "Hardware": [18, 22, 19, 28],
}

# Create stacked bar data
df_wide = pd.DataFrame(data, index=categories)

# Calculate totals for each quarter
totals = df_wide.sum(axis=1)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Create stacked bars
bottom = np.zeros(len(categories))
bars_list = []

for idx, comp in enumerate(components):
    bars = ax.bar(
        categories, df_wide[comp], bottom=bottom, label=comp, color=IMPRINT[idx], edgecolor=PAGE_BG, linewidth=1.5
    )
    bars_list.append(bars)
    bottom += df_wide[comp].values

# Add total labels above each bar stack
for i, total in enumerate(totals):
    ax.annotate(
        f"${total:.0f}M",
        xy=(i, total),
        xytext=(0, 12),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=18,
        fontweight="bold",
        color=INK,
    )

# Styling
ax.set_xlabel("Quarter", fontsize=20, color=INK)
ax.set_ylabel("Revenue (Millions USD)", fontsize=20, color=INK)
ax.set_title("bar-stacked-labeled · Python · seaborn · anyplot.ai", fontsize=24, pad=20, color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Legend - positioned to avoid overlap with bars
ax.legend(
    title="Product Category",
    title_fontsize=16,
    fontsize=14,
    loc="upper right",
    framealpha=1.0,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
)

# Grid - subtle horizontal only
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8)
ax.set_axisbelow(True)

# Adjust y-axis limit to accommodate labels
ax.set_ylim(0, max(totals) * 1.15)

# Remove top and right spines for cleaner look
sns.despine(ax=ax)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
