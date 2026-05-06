"""anyplot.ai
waterfall-basic: Basic Waterfall Chart
Library: matplotlib | Python 3.13
Quality: pending | Created: 2025-12-24
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette for waterfall categories
INCREASE_COLOR = "#009E73"  # Brand green (position 1)
DECREASE_COLOR = "#D55E00"  # Vermillion (position 2)
TOTAL_COLOR = "#0072B2"  # Blue (position 3)

# Data: Project Budget Allocation (from initial budget to final allocation)
# Different scenario from the original (avoiding Altair match)
categories = ["Initial Budget", "Personnel", "Technology", "Marketing", "Contingency", "Savings", "Final Budget"]
# Values: First and last are totals, middle values are changes (None = calculated totals)
values = [1000, -350, -200, -150, 100, 50, None]

# Calculate running totals and determine actual bar values
n = len(categories)
running_total = np.zeros(n)
bar_values = np.zeros(n)
bar_bottom = np.zeros(n)
bar_colors = []

running_total[0] = values[0]
bar_values[0] = values[0]
bar_bottom[0] = 0
bar_colors.append(TOTAL_COLOR)

current = values[0]
for i in range(1, n):
    if values[i] is None:
        # This is a subtotal bar (Final Budget)
        running_total[i] = current
        bar_values[i] = current
        bar_bottom[i] = 0
        bar_colors.append(TOTAL_COLOR)
    else:
        # This is a change bar
        running_total[i] = current + values[i]
        bar_values[i] = values[i]
        if values[i] >= 0:
            bar_bottom[i] = current
            bar_colors.append(INCREASE_COLOR)
        else:
            bar_bottom[i] = current + values[i]
            bar_colors.append(DECREASE_COLOR)
        current = running_total[i]

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

x = np.arange(n)
bar_width = 0.6

# Draw bars
bars = ax.bar(
    x, np.abs(bar_values), width=bar_width, bottom=bar_bottom, color=bar_colors, edgecolor=INK_SOFT, linewidth=1.5
)

# Draw connecting lines between bars
for i in range(n - 1):
    ax.plot(
        [x[i] + bar_width / 2, x[i + 1] - bar_width / 2],
        [running_total[i], running_total[i]],
        color=INK_SOFT,
        linestyle="--",
        linewidth=2,
        zorder=1,
    )

# Add value labels on bars
for i, bar in enumerate(bars):
    height = bar.get_height()
    y_pos = bar_bottom[i] + height / 2

    # Format label
    if values[i] is None:
        label = f"${int(bar_values[i])}"
    elif values[i] >= 0:
        label = f"+${int(values[i])}"
    else:
        label = f"-${int(abs(values[i]))}"

    ax.text(
        bar.get_x() + bar.get_width() / 2,
        y_pos,
        label,
        ha="center",
        va="center",
        fontsize=16,
        fontweight="bold",
        color=INK,
    )

# Styling
ax.set_xlabel("Budget Component", fontsize=20, color=INK)
ax.set_ylabel("Amount ($K)", fontsize=20, color=INK)
ax.set_title("waterfall-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=16, rotation=15, ha="right", color=INK_SOFT)
ax.tick_params(axis="y", labelsize=16, colors=INK_SOFT)

# Grid
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK_SOFT)

# Spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Set y-axis to start from 0
ax.set_ylim(bottom=0)

# Add legend for color meanings
legend_elements = [
    Patch(facecolor=TOTAL_COLOR, edgecolor=INK_SOFT, label="Total", linewidth=1.5),
    Patch(facecolor=INCREASE_COLOR, edgecolor=INK_SOFT, label="Increase", linewidth=1.5),
    Patch(facecolor=DECREASE_COLOR, edgecolor=INK_SOFT, label="Decrease", linewidth=1.5),
]
leg = ax.legend(handles=legend_elements, fontsize=16, loc="upper right", framealpha=0.95)
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
