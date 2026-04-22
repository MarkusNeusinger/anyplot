""" pyplots.ai
lollipop-grouped: Grouped Lollipop Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Data - Quarterly revenue by product line across regions
np.random.seed(42)
categories = ["North", "South", "East", "West"]
series = ["Electronics", "Clothing", "Food"]
n_categories = len(categories)
n_series = len(series)

# Generate realistic revenue data (in millions)
data = []
base_values = {"Electronics": 45, "Clothing": 32, "Food": 28}
for cat in categories:
    for s in series:
        value = base_values[s] + np.random.uniform(-10, 15)
        data.append({"Region": cat, "Product Line": s, "Revenue (M$)": value})

df = pd.DataFrame(data)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Colors for each series (Python Blue first, then accessible colors)
colors = ["#306998", "#FFD43B", "#E24A33"]

# Calculate positions for grouped lollipops
x = np.arange(n_categories)
width = 0.25  # Width between lollipops in same group
offsets = np.linspace(-width * (n_series - 1) / 2, width * (n_series - 1) / 2, n_series)

# Plot lollipops for each series
for i, (s, color) in enumerate(zip(series, colors, strict=True)):
    series_data = df[df["Product Line"] == s]
    positions = x + offsets[i]
    values = series_data["Revenue (M$)"].values

    # Draw stems (vertical lines from 0 to value)
    for pos, val in zip(positions, values, strict=True):
        ax.plot([pos, pos], [0, val], color=color, linewidth=2.5, zorder=1)

    # Draw markers at the top
    ax.scatter(positions, values, s=250, color=color, zorder=2, label=s, edgecolors="white", linewidths=1.5)

# Customize axes
ax.set_xticks(x)
ax.set_xticklabels(categories)
ax.set_xlabel("Region", fontsize=20)
ax.set_ylabel("Revenue (M$)", fontsize=20)
ax.set_title("lollipop-grouped · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Set y-axis to start from 0
ax.set_ylim(0, df["Revenue (M$)"].max() * 1.15)

# Add subtle grid
ax.grid(True, axis="y", alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

# Add legend
ax.legend(title="Product Line", fontsize=14, title_fontsize=16, loc="upper right")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
