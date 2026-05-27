""" anyplot.ai
bar-stacked-labeled: Stacked Bar Chart with Total Labels
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-18
"""

import sys


# Remove the script's directory from sys.path to avoid shadowing installed packages
if sys.path and sys.path[0] and "implementations" in sys.path[0]:
    sys.path.pop(0)

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme configuration
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette (positions 1-4)
COLORS = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Quarterly revenue by product category (in millions $)
np.random.seed(42)
categories = ["Q1", "Q2", "Q3", "Q4"]
components = ["Software", "Hardware", "Services", "Support"]

# Revenue data (realistic quarterly figures in millions)
data = {
    "Software": [45, 52, 58, 62],
    "Hardware": [30, 28, 35, 42],
    "Services": [25, 32, 38, 45],
    "Support": [15, 18, 22, 28],
}

# Create figure with theme-adaptive background
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Create stacked bars
x = np.arange(len(categories))
width = 0.6
bottom = np.zeros(len(categories))

bars_list = []
for i, (component, values) in enumerate(data.items()):
    bars = ax.bar(x, values, width, bottom=bottom, label=component, color=COLORS[i], edgecolor="white", linewidth=1.5)
    bars_list.append(bars)
    bottom += values

# Calculate totals for labels
totals = np.sum([data[comp] for comp in components], axis=0)

# Add total labels above each bar stack
for i, total in enumerate(totals):
    ax.text(x[i], total + 3, f"${total}M", ha="center", va="bottom", fontsize=20, fontweight="bold", color=INK)

# Add segment labels inside bars for larger segments
for i, (_component, values) in enumerate(data.items()):
    cumulative = np.zeros(len(categories))
    for j in range(i):
        cumulative += list(data.values())[j]
    for j, val in enumerate(values):
        if val >= 20:  # Only label segments >= 20
            y_pos = cumulative[j] + val / 2
            ax.text(x[j], y_pos, f"{val}", ha="center", va="center", fontsize=14, color="white", fontweight="bold")

# Styling with theme-adaptive colors
ax.set_xlabel("Quarter", fontsize=20, color=INK)
ax.set_ylabel("Revenue ($ Millions)", fontsize=20, color=INK)
ax.set_title("bar-stacked-labeled · matplotlib · pyplots.ai", fontsize=24, color=INK)
ax.set_xticks(x)
ax.set_xticklabels(categories)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT, labelcolor=INK_SOFT)

# Legend with theme-adaptive styling
leg = ax.legend(fontsize=16, loc="upper left", framealpha=0.9)
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    for text in leg.get_texts():
        text.set_color(INK_SOFT)

ax.set_ylim(0, max(totals) * 1.15)  # Space for labels

# Grid with theme-adaptive styling
ax.yaxis.grid(True, alpha=0.1, linestyle="-", color=INK, linewidth=0.8)

# Spines with theme-adaptive colors
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
