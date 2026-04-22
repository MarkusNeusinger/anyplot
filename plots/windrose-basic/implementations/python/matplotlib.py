""" pyplots.ai
windrose-basic: Wind Rose Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-24
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Simulated annual wind measurements (8760 hourly readings)
np.random.seed(42)

n_observations = 8760  # One year of hourly data

# Generate realistic wind direction data with prevailing westerly winds
# Using mixture of normal distributions wrapped to [0, 360)
directions_main = np.random.normal(240, 30, int(n_observations * 0.5))  # SW prevailing
directions_secondary = np.random.normal(315, 25, int(n_observations * 0.3))  # NW secondary
directions_random = np.random.uniform(0, 360, int(n_observations * 0.2))  # Random

directions = np.concatenate([directions_main, directions_secondary, directions_random])
directions = directions % 360  # Wrap to [0, 360)

# Wind speeds using Weibull distribution (common for wind data)
speeds = np.random.weibull(2.2, len(directions)) * 6  # Scale for realistic m/s values
speeds = np.clip(speeds, 0, 25)

# Define bins - 16 direction sectors (22.5 degrees each)
n_dir_bins = 16
dir_bin_width = 360 / n_dir_bins
direction_centers = np.radians(np.arange(0, 360, dir_bin_width))

# Speed bins in m/s
speed_bins = [0, 3, 6, 9, 12, 15, 25]
speed_labels = ["0-3", "3-6", "6-9", "9-12", "12-15", "15+"]

# Calculate frequencies for each direction/speed combination
freq_matrix = np.zeros((n_dir_bins, len(speed_bins) - 1))

for i in range(n_dir_bins):
    # Calculate bin edges, centered on the direction
    bin_center = i * dir_bin_width
    bin_low = (bin_center - dir_bin_width / 2) % 360
    bin_high = (bin_center + dir_bin_width / 2) % 360

    # Handle wrap-around at 0/360 degrees
    if bin_low > bin_high:
        dir_mask = (directions >= bin_low) | (directions < bin_high)
    else:
        dir_mask = (directions >= bin_low) & (directions < bin_high)

    dir_speeds = speeds[dir_mask]

    for j in range(len(speed_bins) - 1):
        speed_mask = (dir_speeds >= speed_bins[j]) & (dir_speeds < speed_bins[j + 1])
        freq_matrix[i, j] = np.sum(speed_mask)

# Convert to percentage
freq_matrix = freq_matrix / len(directions) * 100

# Plot - square format for radial symmetry
fig, ax = plt.subplots(figsize=(12, 12), subplot_kw={"projection": "polar"})

# Colors from cool (calm) to warm (strong) - starts with Python Blue/Yellow
colors = ["#306998", "#4A90D9", "#7BC8F6", "#FFD43B", "#FF9F1C", "#E63946"]

# Bar width slightly less than bin width for visual clarity
bar_width = np.radians(20)

# Stack the bars for each speed category
bottoms = np.zeros(n_dir_bins)

for j in range(len(speed_bins) - 1):
    ax.bar(
        direction_centers,
        freq_matrix[:, j],
        width=bar_width,
        bottom=bottoms,
        color=colors[j],
        edgecolor="white",
        linewidth=0.5,
        label=f"{speed_labels[j]} m/s",
    )
    bottoms += freq_matrix[:, j]

# Configure polar plot - North at top, clockwise direction (meteorological convention)
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)

# Direction labels for 16 sectors
direction_labels = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
ax.set_xticks(np.radians(np.arange(0, 360, 22.5)))
ax.set_xticklabels(direction_labels, fontsize=16, fontweight="bold")

# Radial axis - frequency percentage
max_freq = np.ceil(bottoms.max() * 1.1)
ax.set_ylim(0, max_freq)
yticks = np.arange(0, max_freq + 1, 2)
ax.set_yticks(yticks)
ax.set_yticklabels([f"{int(y)}%" for y in yticks], fontsize=14)

# Grid styling - subtle
ax.grid(True, alpha=0.3, linestyle="--")

# Title
ax.set_title("windrose-basic · matplotlib · pyplots.ai", fontsize=24, fontweight="bold", pad=20)

# Legend - positioned outside the polar plot
ax.legend(
    title="Wind Speed",
    title_fontsize=16,
    fontsize=14,
    loc="lower left",
    bbox_to_anchor=(-0.15, -0.15),
    framealpha=0.95,
    edgecolor="gray",
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
