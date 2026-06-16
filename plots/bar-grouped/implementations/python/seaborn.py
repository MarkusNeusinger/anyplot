""" anyplot.ai
bar-grouped: Grouped Bar Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-06
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

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data: Customer satisfaction across departments and regions
data = {
    "Region": ["North", "North", "North", "South", "South", "South", "East", "East", "East", "West", "West", "West"],
    "Department": ["IT", "HR", "Operations"] * 4,
    "Score": [82, 78, 75, 88, 84, 80, 85, 81, 79, 90, 86, 83],
}
df = pd.DataFrame(data)

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
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Plot grouped bars
sns.barplot(
    data=df, x="Region", y="Score", hue="Department", palette=IMPRINT, ax=ax, edgecolor="white", linewidth=1.5
)

# Styling
ax.set_xlabel("Region", fontsize=20, color=INK)
ax.set_ylabel("Satisfaction Score", fontsize=20, color=INK)
ax.set_title("bar-grouped · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.set_ylim(0, 100)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Legend - positioned outside to avoid overlap
ax.legend(
    title="Department",
    fontsize=16,
    title_fontsize=16,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.12),
    ncol=3,
    frameon=True,
    fancybox=False,
    edgecolor=INK_SOFT,
)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
