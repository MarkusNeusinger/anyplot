""" anyplot.ai
bar-basic: Basic Bar Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-28
"""

import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"
ANYPLOT_AMBER = "#DDCC77"

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
    },
)

# Data — average annual sunshine hours for major US cities
data = pd.DataFrame(
    {
        "city": ["Phoenix", "Miami", "Denver", "Boston", "Chicago", "Portland", "Seattle"],
        "sunshine_hours": [3872, 3154, 3110, 2634, 2508, 2341, 2170],
    }
)

# Highlight the Phoenix outlier with amber accent; all other bars stay brand green
palette = {city: (ANYPLOT_AMBER if city == "Phoenix" else BRAND) for city in data["city"]}

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
sns.barplot(data=data, x="city", y="sunshine_hours", hue="city", palette=palette, legend=False, width=0.65, ax=ax)

# Value labels on bars
for container in ax.containers:
    ax.bar_label(container, fmt="%d", fontsize=10, color=INK_SOFT, padding=3)

# Style
ax.set_xlabel("City", fontsize=10, color=INK)
ax.set_ylabel("Sunshine Hours per Year", fontsize=10, color=INK)
title = "Annual Sunshine Hours · bar-basic · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK, pad=12)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
sns.despine(ax=ax, top=True, right=True)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)
ax.set_ylim(0, data["sunshine_hours"].max() * 1.12)

fig.subplots_adjust(left=0.10, right=0.97, top=0.90, bottom=0.12)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
