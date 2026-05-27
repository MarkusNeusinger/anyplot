""" anyplot.ai
frequency-polygon-basic: Frequency Polygon for Distribution Comparison
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-17
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

# Okabe-Ito palette (positions 1-3)
COLORS = ["#009E73", "#C475FD", "#4467A3"]

# Data - Heights by age group
np.random.seed(42)
n_per_group = 200

# Generate three distinct distributions representing height measurements (cm)
young_adults = np.random.normal(loc=172, scale=8, size=n_per_group)
middle_aged = np.random.normal(loc=170, scale=9, size=n_per_group)
seniors = np.random.normal(loc=166, scale=10, size=n_per_group)

groups = [young_adults, middle_aged, seniors]
group_names = ["Young Adults (18-25)", "Middle-Aged (40-50)", "Seniors (65+)"]

# Create common bin edges for all groups
all_data = np.concatenate(groups)
bin_edges = np.linspace(all_data.min() - 5, all_data.max() + 5, 20)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for data, name, color in zip(groups, group_names, COLORS, strict=True):
    # Calculate histogram frequencies
    counts, _ = np.histogram(data, bins=bin_edges)

    # Extend to zero at both ends to close the polygon
    x_extended = np.concatenate([[bin_edges[0]], bin_centers, [bin_edges[-1]]])
    y_extended = np.concatenate([[0], counts, [0]])

    # Plot frequency polygon line
    ax.plot(
        x_extended,
        y_extended,
        linewidth=3,
        color=color,
        label=name,
        marker="o",
        markersize=6,
        markerfacecolor=color,
        markeredgecolor=PAGE_BG,
        markeredgewidth=1,
    )

    # Add semi-transparent fill
    ax.fill(x_extended, y_extended, color=color, alpha=0.15)

# Labels and styling
ax.set_xlabel("Height (cm)", fontsize=20, color=INK)
ax.set_ylabel("Frequency", fontsize=20, color=INK)
ax.set_title("frequency-polygon-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Spine styling
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Grid styling
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Legend with theme-adaptive background
leg = ax.legend(fontsize=16, loc="upper left", framealpha=0.95)
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    leg.get_frame().set_linewidth(0.8)
    for text in leg.get_texts():
        text.set_color(INK_SOFT)

# Ensure y-axis starts at 0
ax.set_ylim(bottom=0)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
