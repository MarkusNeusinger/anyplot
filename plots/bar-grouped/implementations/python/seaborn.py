"""anyplot.ai
bar-grouped: Grouped Bar Chart
Library: seaborn 0.13.2 | Python 3.13.12
Quality: pending | Updated: 2026-08-05
"""

import os
import sys


# Fix sys.path to avoid importing local matplotlib.py file
if sys.path and sys.path[0] == os.path.dirname(__file__):
    sys.path.pop(0)

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (canonical order, positions 1-3)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data: Customer satisfaction across departments and regions
data = {
    "Region": ["North", "North", "North", "South", "South", "South", "East", "East", "East", "West", "West", "West"],
    "Department": ["IT", "HR", "Operations"] * 4,
    "Score": [82, 78, 75, 88, 84, 80, 85, 81, 79, 90, 86, 83],
}
df = pd.DataFrame(data)
region_order = df.groupby("Region")["Score"].mean().sort_values(ascending=False).index

# Set theme
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

# Create figure — 3200x1800 px canvas (Step 0 hard contract)
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

# Plot grouped bars, ordered by mean score and dodged with a seaborn 0.13 `gap`
# for cleaner within-group separation than the matplotlib default
sns.barplot(
    data=df,
    x="Region",
    y="Score",
    hue="Department",
    order=region_order,
    palette=IMPRINT,
    ax=ax,
    edgecolor="white",
    linewidth=1,
    gap=0.1,
)

# Value labels for precise comparisons
for container in ax.containers:
    ax.bar_label(container, fontsize=8, color=INK_SOFT, padding=2, fmt="%.0f")

# Styling
ax.set_xlabel("Region", fontsize=10, color=INK)
ax.set_ylabel("Satisfaction Score", fontsize=10, color=INK)
ax.set_title("bar-grouped · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.set_ylim(0, 100)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

# Legend - positioned below to avoid overlap with the bars
ax.legend(
    title="Department",
    fontsize=8,
    title_fontsize=8,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.14),
    ncol=3,
    frameon=True,
    fancybox=False,
    edgecolor=INK_SOFT,
)

# Remove top and right spines, idiomatic seaborn cleanup
sns.despine(ax=ax)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
