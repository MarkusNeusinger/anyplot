""" pyplots.ai
range-interval: Range Interval Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import matplotlib.pyplot as plt
import numpy as np


# Data: Monthly temperature ranges (high/low) for a coastal city
np.random.seed(42)

months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Simulate realistic temperature ranges (Celsius) - warmer in summer
base_temps = np.array([5, 7, 11, 15, 19, 23, 26, 25, 21, 16, 10, 6])
variation = np.random.uniform(3, 7, size=12)

min_temps = base_temps - variation / 2 + np.random.uniform(-2, 2, size=12)
max_temps = base_temps + variation / 2 + np.random.uniform(2, 5, size=12)

# Ensure max > min
min_temps = np.round(min_temps, 1)
max_temps = np.round(max_temps, 1)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Create range bars using bar plot with bottom parameter
x_positions = np.arange(len(months))
range_heights = max_temps - min_temps

# Draw range bars
ax.bar(
    x_positions,
    range_heights,
    bottom=min_temps,
    width=0.6,
    color="#306998",
    alpha=0.7,
    edgecolor="#1f4d6b",
    linewidth=2,
)

# Add min/max markers for emphasis
ax.scatter(x_positions, min_temps, s=150, color="#1f4d6b", zorder=5, marker="_", linewidths=4, label="Min Temperature")
ax.scatter(x_positions, max_temps, s=150, color="#1f4d6b", zorder=5, marker="_", linewidths=4, label="Max Temperature")

# Add midpoint markers
midpoints = (min_temps + max_temps) / 2
ax.scatter(
    x_positions,
    midpoints,
    s=100,
    color="#FFD43B",
    zorder=6,
    marker="o",
    edgecolor="#1f4d6b",
    linewidth=1.5,
    label="Midpoint",
)

# Add value annotations at top and bottom of each bar
for i, (low, high) in enumerate(zip(min_temps, max_temps, strict=True)):
    ax.annotate(
        f"{low:.0f}°",
        (x_positions[i], low),
        textcoords="offset points",
        xytext=(0, -20),
        ha="center",
        fontsize=12,
        color="#333333",
    )
    ax.annotate(
        f"{high:.0f}°",
        (x_positions[i], high),
        textcoords="offset points",
        xytext=(0, 10),
        ha="center",
        fontsize=12,
        color="#333333",
    )

# Styling
ax.set_xlabel("Month", fontsize=20)
ax.set_ylabel("Temperature (°C)", fontsize=20)
ax.set_title("range-interval · matplotlib · pyplots.ai", fontsize=24)

ax.set_xticks(x_positions)
ax.set_xticklabels(months)
ax.tick_params(axis="both", labelsize=16)

# Add horizontal grid for easier reading
ax.grid(True, axis="y", alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

# Legend
ax.legend(fontsize=14, loc="upper right", framealpha=0.9)

# Set y-axis range with padding
y_min = min_temps.min() - 5
y_max = max_temps.max() + 5
ax.set_ylim(y_min, y_max)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
