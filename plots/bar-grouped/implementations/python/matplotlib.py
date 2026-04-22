""" pyplots.ai
bar-grouped: Grouped Bar Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 95/100 | Created: 2025-12-24
"""

import matplotlib.pyplot as plt
import numpy as np


# Data: Quarterly sales by product line (in thousands USD)
categories = ["Q1", "Q2", "Q3", "Q4"]
groups = ["Electronics", "Clothing", "Home & Garden"]

# Sales data showing varied patterns across quarters
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

# Colors: Python Blue, Python Yellow, and a complementary color
colors = ["#306998", "#FFD43B", "#4CAF50"]

# Create plot (4800x2700 px at 300 DPI = 16x9 inches)
fig, ax = plt.subplots(figsize=(16, 9))

# Plot bars for each group
bars = []
for i, (group, color) in enumerate(zip(groups, colors, strict=True)):
    bar = ax.bar(
        x + offsets[i], sales_data[group], bar_width, label=group, color=color, edgecolor="white", linewidth=1.5
    )
    bars.append(bar)

# Add value labels on top of bars
for bar_group in bars:
    for bar in bar_group:
        height = bar.get_height()
        ax.annotate(
            f"{height}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 5),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=14,
            fontweight="medium",
        )

# Styling
ax.set_xlabel("Quarter", fontsize=20)
ax.set_ylabel("Sales (Thousands USD)", fontsize=20)
ax.set_title("bar-grouped · matplotlib · pyplots.ai", fontsize=24)

ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=16)
ax.tick_params(axis="y", labelsize=16)

ax.legend(fontsize=16, loc="upper left", framealpha=0.9)
ax.grid(True, axis="y", alpha=0.3, linestyle="--")

# Set y-axis to start at 0 with some headroom for labels
ax.set_ylim(0, max(max(v) for v in sales_data.values()) * 1.15)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
