""" pyplots.ai
windrose-basic: Wind Rose Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Configure seaborn style
sns.set_style("whitegrid")
sns.set_context("talk", font_scale=1.2)

# Generate realistic wind data (1 year of hourly measurements)
np.random.seed(42)
n_obs = 8760  # hourly for one year

# Simulate prevailing winds from SW with secondary NE pattern
direction_weights = np.zeros(360)
# Primary: SW winds (200-240 degrees)
direction_weights[200:240] = 3.0
# Secondary: NE winds (30-60 degrees)
direction_weights[30:60] = 1.5
# Some westerly (260-290)
direction_weights[260:290] = 1.0
# Background noise
direction_weights += 0.2
direction_weights /= direction_weights.sum()

directions = np.random.choice(360, size=n_obs, p=direction_weights)
# Add some random jitter
directions = (directions + np.random.uniform(-10, 10, n_obs)) % 360

# Wind speeds: higher from prevailing directions
speeds = np.zeros(n_obs)
for i, d in enumerate(directions):
    if 200 <= d <= 240:  # SW - stronger
        speeds[i] = np.random.weibull(2.2) * 8 + 2
    elif 30 <= d <= 60:  # NE - moderate
        speeds[i] = np.random.weibull(2.0) * 6 + 1
    else:
        speeds[i] = np.random.weibull(1.8) * 4 + 0.5
speeds = np.clip(speeds, 0, 25)

# Define bins
n_dir_bins = 16
dir_bins = np.linspace(0, 360, n_dir_bins + 1)
dir_centers = (dir_bins[:-1] + dir_bins[1:]) / 2
dir_width = 2 * np.pi / n_dir_bins

# Speed bins with labels
speed_bins = [0, 3, 6, 10, 15, 25]
speed_labels = ["0-3 m/s", "3-6 m/s", "6-10 m/s", "10-15 m/s", "15+ m/s"]

# Get seaborn color palette (cool to warm progression)
colors = sns.color_palette("YlOrRd", n_colors=len(speed_labels))

# Calculate frequencies
frequencies = np.zeros((n_dir_bins, len(speed_labels)))
for i in range(n_dir_bins):
    dir_min, dir_max = dir_bins[i], dir_bins[i + 1]
    if i == 0:
        in_dir = (directions >= dir_min) & (directions < dir_max) | (directions >= 360 - dir_width / 2 * 180 / np.pi)
    else:
        in_dir = (directions >= dir_min) & (directions < dir_max)

    for j in range(len(speed_labels)):
        speed_min = speed_bins[j]
        speed_max = speed_bins[j + 1]
        in_speed = (speeds >= speed_min) & (speeds < speed_max)
        frequencies[i, j] = np.sum(in_dir & in_speed)

# Convert to percentage
frequencies = frequencies / n_obs * 100

# Create polar plot
fig = plt.figure(figsize=(12, 12))
ax = fig.add_subplot(111, projection="polar")

# Set North at top, clockwise direction
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)

# Convert direction centers to radians
theta = np.deg2rad(dir_centers)

# Plot stacked bars
bottoms = np.zeros(n_dir_bins)
bars_collection = []
for j, (label, color) in enumerate(zip(speed_labels, colors, strict=True)):
    bars = ax.bar(
        theta,
        frequencies[:, j],
        width=dir_width * 0.9,
        bottom=bottoms,
        color=color,
        edgecolor="white",
        linewidth=0.5,
        label=label,
        alpha=0.9,
    )
    bars_collection.append(bars)
    bottoms += frequencies[:, j]

# Customize appearance
ax.set_title("windrose-basic · seaborn · pyplots.ai", fontsize=24, pad=20, fontweight="bold")

# Set radial labels (frequency %)
max_freq = np.ceil(bottoms.max() / 5) * 5
ax.set_ylim(0, max_freq)
ax.set_yticks(np.arange(0, max_freq + 1, 5))
ax.set_yticklabels([f"{int(y)}%" for y in np.arange(0, max_freq + 1, 5)], fontsize=14)

# Set direction labels
direction_labels = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
ax.set_xticks(np.deg2rad(np.arange(0, 360, 45)))
ax.set_xticklabels(direction_labels, fontsize=18, fontweight="bold")

# Style the grid
ax.grid(True, alpha=0.3, linestyle="-", linewidth=0.5)
ax.spines["polar"].set_visible(True)
ax.spines["polar"].set_linewidth(1.5)

# Add legend with seaborn styling
legend = ax.legend(
    title="Wind Speed",
    loc="lower right",
    bbox_to_anchor=(1.15, 0),
    fontsize=14,
    title_fontsize=16,
    framealpha=0.95,
    edgecolor="gray",
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
