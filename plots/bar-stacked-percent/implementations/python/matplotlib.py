""" anyplot.ai
bar-stacked-percent: 100% Stacked Bar Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-08
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series is ALWAYS position 1)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data: Energy mix by country (percentage of total electricity generation)
categories = ["Germany", "France", "UK", "Spain", "Italy", "Poland"]
components = ["Renewables", "Nuclear", "Natural Gas", "Coal", "Other"]

# Raw values (TWh) - will be normalized to 100%
data = np.array(
    [
        [250, 70, 85, 110, 30],  # Germany
        [120, 380, 45, 5, 25],  # France
        [180, 55, 140, 15, 35],  # UK
        [220, 60, 90, 10, 25],  # Spain
        [130, 0, 180, 25, 40],  # Italy
        [50, 0, 25, 200, 20],  # Poland
    ]
)

# Normalize to percentages
percentages = data / data.sum(axis=1, keepdims=True) * 100

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Calculate cumulative percentages for stacking
x = np.arange(len(categories))
bar_width = 0.6
bottom = np.zeros(len(categories))

# Create stacked bars
for i, (component, color) in enumerate(zip(components, IMPRINT, strict=True)):
    bars = ax.bar(
        x, percentages[:, i], bar_width, bottom=bottom, label=component, color=color, edgecolor=PAGE_BG, linewidth=1.5
    )

    # Add percentage labels within segments if large enough
    for j, (bar, pct) in enumerate(zip(bars, percentages[:, i], strict=True)):
        if pct >= 8:  # Only show label if segment is at least 8%
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bottom[j] + pct / 2,
                f"{pct:.0f}%",
                ha="center",
                va="center",
                fontsize=14,
                fontweight="bold",
                color=INK,
            )

    bottom += percentages[:, i]

# Style
ax.set_xlabel("Country", fontsize=20, color=INK)
ax.set_ylabel("Percentage (%)", fontsize=20, color=INK)
ax.set_title("bar-stacked-percent · matplotlib · anyplot.ai", fontsize=24, color=INK, fontweight="medium")

ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=16, color=INK_SOFT)
ax.tick_params(axis="y", labelsize=16, colors=INK_SOFT)

ax.set_ylim(0, 100)
ax.set_yticks([0, 25, 50, 75, 100])

# Legend
leg = ax.legend(fontsize=16, loc="upper left", bbox_to_anchor=(1.02, 1))
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    leg.get_frame().set_linewidth(0.8)
    plt.setp(leg.get_texts(), color=INK_SOFT)

# Grid
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

# Spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
