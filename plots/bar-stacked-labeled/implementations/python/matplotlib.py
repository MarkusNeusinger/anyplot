""" pyplots.ai
bar-stacked-labeled: Stacked Bar Chart with Total Labels
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 95/100 | Created: 2026-01-09
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Quarterly revenue by product category (in millions $)
np.random.seed(42)
categories = ["Q1", "Q2", "Q3", "Q4"]
components = ["Software", "Hardware", "Services", "Support"]
colors = ["#306998", "#FFD43B", "#4ECDC4", "#FF6B6B"]

# Revenue data (realistic quarterly figures in millions)
data = {
    "Software": [45, 52, 58, 62],
    "Hardware": [30, 28, 35, 42],
    "Services": [25, 32, 38, 45],
    "Support": [15, 18, 22, 28],
}

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Create stacked bars
x = np.arange(len(categories))
width = 0.6
bottom = np.zeros(len(categories))

bars_list = []
for i, (component, values) in enumerate(data.items()):
    bars = ax.bar(x, values, width, bottom=bottom, label=component, color=colors[i], edgecolor="white", linewidth=1.5)
    bars_list.append(bars)
    bottom += values

# Calculate totals for labels
totals = np.sum([data[comp] for comp in components], axis=0)

# Add total labels above each bar stack
for i, total in enumerate(totals):
    ax.text(x[i], total + 3, f"${total}M", ha="center", va="bottom", fontsize=20, fontweight="bold", color="#333333")

# Add segment labels inside bars for larger segments
for i, (_component, values) in enumerate(data.items()):
    cumulative = np.zeros(len(categories))
    for j in range(i):
        cumulative += list(data.values())[j]
    for j, val in enumerate(values):
        if val >= 20:  # Only label segments >= 20
            y_pos = cumulative[j] + val / 2
            ax.text(x[j], y_pos, f"{val}", ha="center", va="center", fontsize=14, color="white", fontweight="bold")

# Styling
ax.set_xlabel("Quarter", fontsize=20)
ax.set_ylabel("Revenue ($ Millions)", fontsize=20)
ax.set_title("bar-stacked-labeled · matplotlib · pyplots.ai", fontsize=24)
ax.set_xticks(x)
ax.set_xticklabels(categories)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper left", framealpha=0.9)
ax.set_ylim(0, max(totals) * 1.15)  # Space for labels
ax.grid(True, alpha=0.3, linestyle="--", axis="y")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
