""" anyplot.ai
histogram-overlapping: Overlapping Histograms
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-08
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

# Okabe-Ito colors (first series is always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - Comparing salary distributions across three departments
np.random.seed(42)

# Engineering: higher salaries, tighter distribution
engineering = np.random.normal(95000, 12000, 200)

# Marketing: moderate salaries, wider spread
marketing = np.random.normal(75000, 18000, 180)

# Sales: lower base but high variance due to commissions
sales = np.random.normal(65000, 22000, 220)

# Create plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Define consistent bins for all groups
bins = np.linspace(20000, 150000, 35)

# Plot overlapping histograms with transparency
ax.hist(engineering, bins=bins, alpha=0.5, label="Engineering", color=IMPRINT[0], edgecolor=INK_SOFT, linewidth=1.5)
ax.hist(marketing, bins=bins, alpha=0.5, label="Marketing", color=IMPRINT[1], edgecolor=INK_SOFT, linewidth=1.5)
ax.hist(sales, bins=bins, alpha=0.5, label="Sales", color=IMPRINT[2], edgecolor=INK_SOFT, linewidth=1.5)

# Labels and styling
ax.set_xlabel("Annual Salary ($)", fontsize=20, color=INK)
ax.set_ylabel("Number of Employees", fontsize=20, color=INK)
ax.set_title("histogram-overlapping · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Grid - subtle on both axes
ax.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Format x-axis with thousands separator
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x / 1000:.0f}k"))

# Legend styling
leg = ax.legend(fontsize=16, loc="upper right")
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    leg.get_frame().set_linewidth(0.8)
    plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
