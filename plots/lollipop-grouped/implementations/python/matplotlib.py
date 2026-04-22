""" pyplots.ai
lollipop-grouped: Grouped Lollipop Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import matplotlib.pyplot as plt
import numpy as np


# Data: Quarterly revenue by product line across regions
np.random.seed(42)

categories = ["North", "South", "East", "West"]
series = ["Electronics", "Furniture", "Clothing"]
n_categories = len(categories)
n_series = len(series)

# Revenue data in millions
values = {"Electronics": [4.2, 3.1, 5.5, 2.8], "Furniture": [2.8, 3.5, 2.2, 4.1], "Clothing": [3.5, 2.9, 3.8, 3.2]}

# Colors: Python Blue, Python Yellow, plus one more
colors = ["#306998", "#FFD43B", "#4CAF50"]

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Positioning: group lollipops side by side
bar_width = 0.2
x = np.arange(n_categories)

for i, (series_name, color) in enumerate(zip(series, colors, strict=True)):
    # Offset position for each series within group
    x_pos = x + (i - (n_series - 1) / 2) * bar_width
    y_vals = values[series_name]

    # Draw stems (thin vertical lines from baseline to marker)
    for xp, yv in zip(x_pos, y_vals, strict=True):
        ax.plot([xp, xp], [0, yv], color=color, linewidth=2, zorder=1)

    # Draw markers (circular dots)
    ax.scatter(x_pos, y_vals, s=250, color=color, zorder=2, label=series_name, edgecolors="white", linewidths=1.5)

# Styling
ax.set_xlabel("Region", fontsize=20)
ax.set_ylabel("Revenue ($ millions)", fontsize=20)
ax.set_title("lollipop-grouped · matplotlib · pyplots.ai", fontsize=24)
ax.set_xticks(x)
ax.set_xticklabels(categories)
ax.tick_params(axis="both", labelsize=16)
ax.set_ylim(0, 6.5)
ax.legend(fontsize=16, loc="upper right")
ax.grid(True, alpha=0.3, linestyle="--", axis="y")

# Add baseline
ax.axhline(y=0, color="black", linewidth=0.8)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
