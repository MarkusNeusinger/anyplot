""" pyplots.ai
map-route-path: Route Path Map
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-19
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Simulate a hiking trail GPS track
np.random.seed(42)
n_points = 200

# Generate a winding path using cumulative random walks
# Start point: somewhere in Central Park, NYC area (approximate coordinates)
start_lat, start_lon = 40.785, -73.968

# Create path with varying step sizes to simulate realistic movement
lat_steps = np.random.normal(0.0003, 0.0002, n_points)
lon_steps = np.random.normal(0.0004, 0.0003, n_points)

# Add some directional bias to make a coherent route
lat_steps[:60] += 0.0002
lon_steps[:60] += 0.0003
lat_steps[60:120] -= 0.0001
lon_steps[60:120] += 0.0002
lat_steps[120:] -= 0.0002
lon_steps[120:] -= 0.0001

lats = start_lat + np.cumsum(lat_steps)
lons = start_lon + np.cumsum(lon_steps)

# Create timestamps for color encoding (morning hike)
base_time = pd.Timestamp("2024-06-15 08:00:00")
timestamps = pd.date_range(start=base_time, periods=n_points, freq="30s")

# Calculate elapsed minutes for color mapping
elapsed_minutes = np.arange(n_points) * 0.5

df = pd.DataFrame(
    {"lat": lats, "lon": lons, "sequence": np.arange(n_points), "timestamp": timestamps, "elapsed_min": elapsed_minutes}
)

# Plot
sns.set_context("talk", font_scale=1.2)
fig, ax = plt.subplots(figsize=(16, 9))

# Draw the connecting path using seaborn's lineplot
sns.lineplot(data=df, x="lon", y="lat", color="#306998", linewidth=2, alpha=0.5, ax=ax, sort=False, zorder=1)

# Draw waypoints colored by elapsed time using seaborn's scatterplot
sns.scatterplot(
    data=df, x="lon", y="lat", hue="elapsed_min", palette="viridis", s=80, alpha=0.7, ax=ax, legend=False, zorder=2
)

# Create a ScalarMappable for colorbar since scatterplot with hue doesn't provide one
norm = plt.Normalize(df["elapsed_min"].min(), df["elapsed_min"].max())
sm = plt.cm.ScalarMappable(cmap="viridis", norm=norm)

# Mark start point (green circle)
ax.scatter(
    df["lon"].iloc[0],
    df["lat"].iloc[0],
    c="#2ECC71",
    s=400,
    marker="o",
    edgecolors="white",
    linewidths=3,
    zorder=4,
    label="Start",
)

# Mark end point (red square)
ax.scatter(
    df["lon"].iloc[-1],
    df["lat"].iloc[-1],
    c="#E74C3C",
    s=400,
    marker="s",
    edgecolors="white",
    linewidths=3,
    zorder=4,
    label="End",
)

# Add direction arrows at intervals along the path
arrow_indices = [40, 80, 120, 160]
for i in arrow_indices:
    if i < len(df) - 1:
        ax.annotate(
            "",
            xy=(df["lon"].iloc[i + 1], df["lat"].iloc[i + 1]),
            xytext=(df["lon"].iloc[i], df["lat"].iloc[i]),
            arrowprops={"arrowstyle": "->", "color": "#306998", "lw": 2.5},
            zorder=3,
        )

# Colorbar for time progression
cbar = plt.colorbar(sm, ax=ax, pad=0.02)
cbar.set_label("Elapsed Time (minutes)", fontsize=18)
cbar.ax.tick_params(labelsize=14)

# Labels and styling
ax.set_xlabel("Longitude (°)", fontsize=20)
ax.set_ylabel("Latitude (°)", fontsize=20)
ax.set_title("map-route-path · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")
ax.legend(fontsize=16, loc="upper left")

# Set equal aspect ratio for geographic accuracy
ax.set_aspect("equal")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
