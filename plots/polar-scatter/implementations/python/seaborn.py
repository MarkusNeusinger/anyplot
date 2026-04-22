""" pyplots.ai
polar-scatter: Polar Scatter Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Wind measurements with prevailing directions
np.random.seed(42)
n_points = 120

# Create realistic wind data with prevailing directions (SW and NE)
# Morning winds: predominantly from SW (around 225 degrees)
morning_angles = np.random.normal(225, 30, n_points // 2) % 360
morning_speeds = np.random.gamma(3, 3, n_points // 2) + 5

# Afternoon winds: predominantly from NE (around 45 degrees)
afternoon_angles = np.random.normal(45, 40, n_points // 2) % 360
afternoon_speeds = np.random.gamma(2.5, 4, n_points // 2) + 3

# Combine data
angles_deg = np.concatenate([morning_angles, afternoon_angles])
speeds = np.concatenate([morning_speeds, afternoon_speeds])
time_of_day = ["Morning"] * (n_points // 2) + ["Afternoon"] * (n_points // 2)

# Convert to radians for plotting
angles_rad = np.deg2rad(angles_deg)

# Create DataFrame for seaborn
df = pd.DataFrame({"angle_rad": angles_rad, "speed": speeds, "time_of_day": time_of_day})

# Create polar plot
fig = plt.figure(figsize=(12, 12))
ax = fig.add_subplot(111, projection="polar")

# Use seaborn's scatterplot on the polar axes
sns.scatterplot(
    data=df,
    x="angle_rad",
    y="speed",
    hue="time_of_day",
    palette=["#306998", "#FFD43B"],
    s=150,
    alpha=0.7,
    ax=ax,
    edgecolor="white",
    linewidth=0.5,
)

# Configure polar plot appearance
ax.set_theta_zero_location("N")  # 0 degrees at top (North)
ax.set_theta_direction(-1)  # Clockwise

# Set angular ticks with cardinal directions
ax.set_xticks(np.deg2rad([0, 45, 90, 135, 180, 225, 270, 315]))
ax.set_xticklabels(["N", "NE", "E", "SE", "S", "SW", "W", "NW"], fontsize=18)

# Configure radial axis
ax.set_ylim(0, max(speeds) * 1.1)
ax.set_xlabel("")  # Remove angle_rad label
ax.set_ylabel("")
ax.tick_params(axis="y", labelsize=14)

# Add radial label
ax.text(np.deg2rad(60), max(speeds) * 0.55, "Wind Speed (m/s)", fontsize=16, ha="center", va="center", rotation=-30)

# Style the grid
ax.grid(True, alpha=0.3, linestyle="--")
ax.set_facecolor("#f8f9fa")

# Title
ax.set_title("polar-scatter · seaborn · pyplots.ai", fontsize=24, pad=20, fontweight="bold")

# Legend
legend = ax.legend(
    title="Time of Day", title_fontsize=16, fontsize=14, loc="upper right", bbox_to_anchor=(1.15, 1.0), framealpha=0.9
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
