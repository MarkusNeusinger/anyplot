""" pyplots.ai
polar-scatter: Polar Scatter Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


# Data - Wind measurement data with prevailing directions
np.random.seed(42)

# Generate 120 wind observations with realistic prevailing wind patterns
n_points = 120

# Create clusters around prevailing wind directions (SW and NW winds common)
# Cluster 1: Southwest winds (around 225 degrees) - morning observations
morning_angles = np.random.normal(225, 30, 40)
morning_speeds = np.random.gamma(2, 3, 40)  # Wind speeds in m/s (typical 5-15 m/s)

# Cluster 2: Northwest winds (around 315 degrees) - afternoon observations
afternoon_angles = np.random.normal(315, 25, 40)
afternoon_speeds = np.random.gamma(2.5, 3, 40)

# Cluster 3: Variable winds - evening observations
evening_angles = np.random.uniform(0, 360, 40)
evening_speeds = np.random.gamma(1.5, 3, 40)

# Combine all observations
angles_deg = np.concatenate([morning_angles, afternoon_angles, evening_angles])
speeds = np.concatenate([morning_speeds, afternoon_speeds, evening_speeds])
categories = np.array(["Morning"] * 40 + ["Afternoon"] * 40 + ["Evening"] * 40)

# Normalize angles to 0-360 range
angles_deg = angles_deg % 360

# Convert to radians for polar plot
angles_rad = np.deg2rad(angles_deg)

# Create polar plot with square aspect ratio (better for polar)
fig, ax = plt.subplots(figsize=(12, 12), subplot_kw={"projection": "polar"})

# Color mapping for categories
colors = {"Morning": "#306998", "Afternoon": "#FFD43B", "Evening": "#8B4513"}
color_list = [colors[cat] for cat in categories]

# Plot scatter with size based on data density considerations (100-120 points)
# Use s=150 for visibility, alpha=0.7 for overlap handling
scatter = ax.scatter(angles_rad, speeds, c=color_list, s=150, alpha=0.7, edgecolors="white", linewidths=0.5)

# Configure angular axis (theta)
ax.set_theta_zero_location("N")  # 0 degrees at top (North)
ax.set_theta_direction(-1)  # Clockwise direction (compass-like)
ax.set_thetagrids(
    [0, 45, 90, 135, 180, 225, 270, 315], labels=["N", "NE", "E", "SE", "S", "SW", "W", "NW"], fontsize=18
)

# Configure radial axis - use 10 unit intervals to avoid crowded labels
max_speed = np.ceil(speeds.max() / 10) * 10  # Round up to nearest 10
ax.set_rlim(0, max_speed)
ax.set_rticks(np.arange(0, max_speed + 1, 10))
ax.tick_params(axis="y", labelsize=14)

# Add radial label
ax.set_ylabel("Wind Speed (m/s)", fontsize=18, labelpad=35)

# Title
ax.set_title("polar-scatter · matplotlib · pyplots.ai", fontsize=24, pad=20)

# Create custom legend
legend_elements = [
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#306998", markersize=14, label="Morning"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#FFD43B", markersize=14, label="Afternoon"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#8B4513", markersize=14, label="Evening"),
]
ax.legend(
    handles=legend_elements,
    loc="upper left",
    bbox_to_anchor=(1.05, 1.0),
    fontsize=16,
    title="Time of Day",
    title_fontsize=18,
)

# Grid styling
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
