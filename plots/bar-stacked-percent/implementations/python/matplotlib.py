""" pyplots.ai
bar-stacked-percent: 100% Stacked Bar Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import matplotlib.pyplot as plt
import numpy as np


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

# Colors: colorblind-safe palette starting with Python Blue
colors = ["#306998", "#FFD43B", "#50C878", "#DC143C", "#9370DB"]

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Calculate cumulative percentages for stacking
x = np.arange(len(categories))
bar_width = 0.6
bottom = np.zeros(len(categories))

# Create stacked bars
for i, (component, color) in enumerate(zip(components, colors, strict=True)):
    bars = ax.bar(
        x, percentages[:, i], bar_width, bottom=bottom, label=component, color=color, edgecolor="white", linewidth=1.5
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
                color="white" if color in ["#306998", "#DC143C"] else "black",
            )

    bottom += percentages[:, i]

# Labels and styling
ax.set_xlabel("Country", fontsize=20)
ax.set_ylabel("Percentage (%)", fontsize=20)
ax.set_title("European Energy Mix · bar-stacked-percent · matplotlib · pyplots.ai", fontsize=24)

ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=16)
ax.tick_params(axis="y", labelsize=16)

ax.set_ylim(0, 100)
ax.set_yticks([0, 25, 50, 75, 100])

# Legend outside the plot to avoid covering data
ax.legend(fontsize=16, loc="upper left", bbox_to_anchor=(1.02, 1), frameon=True, edgecolor="gray")

ax.grid(True, axis="y", alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
