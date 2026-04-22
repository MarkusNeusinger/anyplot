""" pyplots.ai
gauge-basic: Basic Gauge Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 95/100 | Created: 2025-12-23
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


# Data
value = 72  # Current sales value
min_value = 0
max_value = 100
thresholds = [30, 70]  # Boundaries for red/yellow/green zones

# Calculate angles (gauge spans from 180° to 0°, i.e., left to right)
angle_range = 180  # Semi-circular gauge
value_normalized = (value - min_value) / (max_value - min_value)
needle_angle = 180 - value_normalized * angle_range  # Convert to degrees (180=left, 0=right)

# Create plot (4800x2700 px)
fig, ax = plt.subplots(figsize=(16, 9))

# Draw gauge background zones (wedges)
zone_colors = ["#E74C3C", "#F1C40F", "#2ECC71"]  # Red, Yellow, Green
zone_boundaries = [min_value] + thresholds + [max_value]

for i in range(len(zone_colors)):
    start_norm = (zone_boundaries[i] - min_value) / (max_value - min_value)
    end_norm = (zone_boundaries[i + 1] - min_value) / (max_value - min_value)
    # Convert to angles (180° to 0°)
    theta1 = 180 - end_norm * angle_range
    theta2 = 180 - start_norm * angle_range
    wedge = mpatches.Wedge(
        center=(0, 0),
        r=1.0,
        theta1=theta1,
        theta2=theta2,
        width=0.3,
        facecolor=zone_colors[i],
        edgecolor="white",
        linewidth=2,
    )
    ax.add_patch(wedge)

# Draw inner arc (white background for cleaner look)
inner_circle = mpatches.Wedge(center=(0, 0), r=0.65, theta1=0, theta2=180, facecolor="white", edgecolor="none")
ax.add_patch(inner_circle)

# Draw the needle
needle_rad = np.radians(needle_angle)
needle_length = 0.75
needle_x = needle_length * np.cos(needle_rad)
needle_y = needle_length * np.sin(needle_rad)

# Needle line
ax.plot([0, needle_x], [0, needle_y], color="#2C3E50", linewidth=6, solid_capstyle="round")

# Needle center cap
center_circle = plt.Circle((0, 0), 0.08, color="#2C3E50", zorder=10)
ax.add_patch(center_circle)

# Add tick marks and labels around the gauge
tick_values = [0, 25, 50, 75, 100]
for tick in tick_values:
    tick_norm = (tick - min_value) / (max_value - min_value)
    tick_angle = 180 - tick_norm * angle_range
    tick_rad = np.radians(tick_angle)

    # Tick mark
    inner_r = 1.02
    outer_r = 1.08
    ax.plot(
        [inner_r * np.cos(tick_rad), outer_r * np.cos(tick_rad)],
        [inner_r * np.sin(tick_rad), outer_r * np.sin(tick_rad)],
        color="#333333",
        linewidth=3,
    )

    # Tick label
    label_r = 1.18
    ax.text(
        label_r * np.cos(tick_rad),
        label_r * np.sin(tick_rad),
        str(tick),
        ha="center",
        va="center",
        fontsize=18,
        fontweight="bold",
        color="#333333",
    )

# Display the current value prominently below the gauge
ax.text(0, -0.25, f"{value}", ha="center", va="center", fontsize=48, fontweight="bold", color="#306998")

# Add "Current Sales" label below value
ax.text(0, -0.45, "Current Sales", ha="center", va="center", fontsize=20, color="#666666")

# Add title
ax.set_title("gauge-basic · matplotlib · pyplots.ai", fontsize=24, pad=20)

# Set equal aspect ratio and limits
ax.set_aspect("equal")
ax.set_xlim(-1.5, 1.5)
ax.set_ylim(-0.7, 1.5)
ax.axis("off")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
