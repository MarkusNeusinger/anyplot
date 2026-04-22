""" pyplots.ai
polar-basic: Basic Polar Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Set seaborn style for consistent aesthetics
sns.set_theme(style="whitegrid")
sns.set_context("talk", font_scale=1.2)

# Data: Hourly website traffic pattern (24-hour cycle)
np.random.seed(42)
hours = np.arange(0, 24)
theta = hours * (2 * np.pi / 24)  # Convert hours to radians

# Realistic website traffic pattern: peaks in morning (9-11) and evening (19-21)
base_traffic = 100
morning_peak = 80 * np.exp(-0.5 * ((hours - 10) / 2) ** 2)
evening_peak = 100 * np.exp(-0.5 * ((hours - 20) / 2.5) ** 2)
noise = np.random.normal(0, 10, 24)
traffic = base_traffic + morning_peak + evening_peak + noise
traffic = np.clip(traffic, 20, None)  # Ensure positive values

# Create polar plot (square format for radial symmetry)
fig, ax = plt.subplots(figsize=(12, 12), subplot_kw={"projection": "polar"})

# Create color palette using seaborn
colors = sns.color_palette("viridis", n_colors=24)

# Use seaborn's scatterplot on polar axis
# Plot each point with color gradient based on traffic value
scatter = ax.scatter(
    theta, traffic, c=traffic, cmap="viridis", s=300, alpha=0.8, edgecolors="#306998", linewidths=2, zorder=5
)

# Connect points with a line for continuity
ax.plot(np.append(theta, theta[0]), np.append(traffic, traffic[0]), color="#306998", linewidth=2.5, alpha=0.7, zorder=4)

# Fill area under the curve with seaborn blue
ax.fill(np.append(theta, theta[0]), np.append(traffic, traffic[0]), color="#306998", alpha=0.15, zorder=3)

# Styling
ax.set_title("Website Traffic by Hour · polar-basic · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20)

# Set theta labels (hours of day)
ax.set_xticks(np.linspace(0, 2 * np.pi, 24, endpoint=False))
hour_labels = [f"{h:02d}:00" for h in range(24)]
ax.set_xticklabels(hour_labels, fontsize=14)

# Set radial ticks and label
ax.set_ylim(0, max(traffic) * 1.15)
ax.set_ylabel("Visitors", fontsize=18, labelpad=35)
ax.yaxis.set_label_position("right")
ax.tick_params(axis="y", labelsize=14)

# Configure grid with seaborn-appropriate styling
ax.grid(True, alpha=0.3, linestyle="--")

# Add colorbar for traffic intensity
cbar = plt.colorbar(scatter, ax=ax, pad=0.12, shrink=0.8)
cbar.set_label("Traffic Volume", fontsize=16)
cbar.ax.tick_params(labelsize=14)

# Start at top (12 o'clock position for time-based data)
ax.set_theta_offset(np.pi / 2)
ax.set_theta_direction(-1)  # Clockwise

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
