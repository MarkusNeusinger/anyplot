""" anyplot.ai
bar-grouped: Grouped Bar Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-06
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette (position 1 is always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data: Quarterly sales by product line (in thousands USD)
categories = ["Q1", "Q2", "Q3", "Q4"]
groups = ["Electronics", "Clothing", "Home & Garden"]

sales_data = {
    "Electronics": [245, 312, 287, 425],
    "Clothing": [178, 195, 285, 310],
    "Home & Garden": [125, 210, 195, 165],
}

# Setup for grouped bars
x = np.arange(len(categories))
n_groups = len(groups)
bar_width = 0.25
offsets = np.linspace(-(n_groups - 1) / 2, (n_groups - 1) / 2, n_groups) * bar_width

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Track max value per category for emphasis
max_values_per_category = {cat: max(sales_data[group][i] for group in groups) for i, cat in enumerate(categories)}

bars = []
for i, (group, color) in enumerate(zip(groups, IMPRINT, strict=True)):
    bar = ax.bar(
        x + offsets[i], sales_data[group], bar_width, label=group, color=color, edgecolor=INK_SOFT, linewidth=1.5
    )
    bars.append(bar)

    # Add subtle drop shadows for depth
    for rect in bar:
        # Shadow patch (offset below and slightly to the right)
        shadow = plt.Rectangle(
            (rect.get_x() + 0.003, rect.get_y() - 0.02),
            rect.get_width(),
            rect.get_height(),
            facecolor=INK_MUTED,
            alpha=0.08,
            zorder=0,
        )
        ax.add_patch(shadow)

# Add value labels and markers on top of bars
for bar_group in bars:
    for j, bar in enumerate(bar_group):
        height = bar.get_height()
        is_max = height == max_values_per_category[categories[j]]

        # Marker dot at bar top
        marker_size = 120 if is_max else 80
        marker_alpha = 1.0 if is_max else 0.6
        ax.scatter(
            bar.get_x() + bar.get_width() / 2,
            height,
            s=marker_size,
            color=bar.get_facecolor(),
            edgecolors=INK_SOFT,
            linewidth=1.2 if is_max else 0.8,
            alpha=marker_alpha,
            zorder=3,
        )

        # Value label
        ax.annotate(
            f"{int(height)}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=14,
            color=INK,
            fontweight="bold" if is_max else "normal",
            zorder=4,
        )

# Style
ax.set_xlabel("Quarter", fontsize=20, color=INK)
ax.set_ylabel("Sales (Thousands USD)", fontsize=20, color=INK)
ax.set_title("bar-grouped · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)

ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=16, color=INK_SOFT)
ax.tick_params(axis="y", labelsize=16, colors=INK_SOFT)

# Legend with theme-adaptive styling
leg = ax.legend(fontsize=16, loc="upper right", framealpha=0.95)
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    leg.get_frame().set_linewidth(1.0)
    plt.setp(leg.get_texts(), color=INK_SOFT)

# Grid
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

# Y-axis limits
ax.set_ylim(0, max(max(v) for v in sales_data.values()) * 1.15)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
