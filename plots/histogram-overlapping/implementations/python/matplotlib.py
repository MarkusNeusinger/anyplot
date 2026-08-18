""" anyplot.ai
histogram-overlapping: Overlapping Histograms
Library: matplotlib 3.11.1 | Python 3.13.15
Quality: 86/100 | Updated: 2026-08-18
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

# Imprint palette (first series is always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - Comparing salary distributions across three departments
np.random.seed(42)

# Engineering: higher salaries, tighter distribution
engineering = np.random.normal(95000, 12000, 200)

# Marketing: moderate salaries, wider spread
marketing = np.random.normal(75000, 18000, 180)

# Sales: lower base but high variance due to commissions
sales = np.random.normal(65000, 22000, 220)

groups = [("Engineering", engineering, IMPRINT[0]), ("Marketing", marketing, IMPRINT[1]), ("Sales", sales, IMPRINT[2])]

# Create plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Define consistent bins for all groups
bins = np.linspace(20000, 150000, 35)

# Overlapping histograms as filled steps - a single continuous outline per
# group reads more clearly than per-bar edges once fills stack on top of
# each other, and keeps the silhouette of each distribution legible.
for name, data, color in groups:
    ax.hist(data, bins=bins, alpha=0.5, label=name, color=color, histtype="stepfilled", edgecolor=color, linewidth=1.5)
    ax.axvline(data.mean(), color=color, linestyle=":", linewidth=1.3, alpha=0.9)

# Labels and styling
title = "histogram-overlapping · python · matplotlib · anyplot.ai"
ax.set_xlabel("Annual Salary ($)", fontsize=10, color=INK)
ax.set_ylabel("Number of Employees", fontsize=10, color=INK)
ax.set_title(title, fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

# Grid - subtle on both axes
ax.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Format x-axis with thousands separator
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x / 1000:.0f}k"))

# Legend styling
leg = ax.legend(fontsize=8, loc="upper right")
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    leg.get_frame().set_linewidth(0.8)
    plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
