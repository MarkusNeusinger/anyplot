""" anyplot.ai
bar-stacked: Stacked Bar Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-09
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

# Okabe-Ito palette (positions 1-4)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data: Quarterly revenue by product category (in millions USD)
categories = ["Q1", "Q2", "Q3", "Q4"]
products = ["Software", "Hardware", "Services", "Support"]

software = np.array([45, 52, 48, 68])
hardware = np.array([32, 28, 35, 42])
services = np.array([28, 31, 38, 35])
support = np.array([15, 18, 20, 22])

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

x = np.arange(len(categories))
bar_width = 0.6

# Create stacked bars
bottom = np.zeros(len(categories))
for i, (product, values) in enumerate(zip(products, [software, hardware, services, support], strict=True)):
    ax.bar(x, values, bar_width, label=product, bottom=bottom, color=IMPRINT[i], edgecolor=PAGE_BG, linewidth=1.5)
    bottom += values

# Add total labels above each stacked bar
totals = software + hardware + services + support
for i, total in enumerate(totals):
    ax.text(i, total + 3, f"${total}M", ha="center", va="bottom", fontsize=18, fontweight="bold", color=INK)

# Style
ax.set_xlabel("Quarter", fontsize=20, color=INK)
ax.set_ylabel("Revenue (Millions USD)", fontsize=20, color=INK)
ax.set_title("bar-stacked · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.set_xticks(x)
ax.set_xticklabels(categories)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT, labelcolor=INK_SOFT)

# Legend
leg = ax.legend(fontsize=16, loc="upper left", bbox_to_anchor=(1.02, 1))
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)

# Grid (subtle, y-axis only)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

# Spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Y-axis limits with headroom for labels
ax.set_ylim(0, max(totals) + 20)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
