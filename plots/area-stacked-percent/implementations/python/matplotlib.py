""" anyplot.ai
area-stacked-percent: 100% Stacked Area Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-12
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

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data - Renewable energy evolution (2014-2024)
years = np.arange(2014, 2025)
solar = np.array([0.8, 1.2, 1.8, 2.5, 3.3, 4.2, 5.4, 6.8, 8.2, 9.8, 11.5])
wind = np.array([2.1, 2.5, 3.0, 3.8, 4.6, 5.5, 6.8, 8.2, 9.6, 11.2, 13.0])
hydro = np.array([15.2, 15.5, 15.8, 16.2, 16.5, 16.8, 17.0, 17.1, 17.2, 17.3, 17.4])
natural_gas = np.array([42.1, 41.8, 41.2, 40.5, 39.8, 39.0, 37.5, 35.8, 34.0, 32.5, 31.0])
coal = np.array([39.8, 38.5, 37.2, 36.0, 35.8, 34.5, 33.3, 32.1, 31.0, 29.0, 27.1])

# Stack and normalize
data = np.vstack([solar, wind, hydro, natural_gas, coal])
totals = data.sum(axis=0)
data_percent = data / totals * 100

# Create plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Labels
labels = ["Solar", "Wind", "Hydro", "Natural Gas", "Coal"]

# Create stacked area
ax.stackplot(years, data_percent, labels=labels, colors=IMPRINT, alpha=0.85, edgecolor=PAGE_BG, linewidth=1.5)

# Styling
ax.set_xlabel("Year (2014–2024)", fontsize=20, color=INK)
ax.set_ylabel("Electricity Generation (%)", fontsize=20, color=INK)
ax.set_title("area-stacked-percent · matplotlib · anyplot.ai", fontsize=24, color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Axis limits
ax.set_xlim(years[0], years[-1])
ax.set_ylim(0, 100)

# Y-axis ticks with percentage labels
ax.set_yticks([0, 25, 50, 75, 100])
ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"], color=INK_SOFT)

# X-axis ticks
ax.set_xticks(years)
ax.set_xticklabels(years, color=INK_SOFT)

# Grid
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

# Spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Legend - positioned outside plot area
leg = ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), fontsize=16, frameon=True)
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    leg.get_frame().set_linewidth(0.8)
    for text in leg.get_texts():
        text.set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
