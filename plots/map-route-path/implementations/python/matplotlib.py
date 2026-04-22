""" pyplots.ai
map-route-path: Route Path Map
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-19
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection


# Data: Simulated hiking trail GPS track (coastal path with curves)
np.random.seed(42)
n_points = 150

# Create a realistic hiking trail path with curves and turns
t = np.linspace(0, 4 * np.pi, n_points)

# Base path with sinusoidal variation to simulate a winding trail
lon = -122.4 + 0.03 * t / (4 * np.pi) + 0.008 * np.sin(2 * t) + np.cumsum(np.random.randn(n_points) * 0.0003)
lat = 37.75 + 0.025 * np.sin(t) + 0.015 * np.cos(1.5 * t) + np.cumsum(np.random.randn(n_points) * 0.0003)

# Sequence for color encoding (progression along path)
sequence = np.arange(n_points)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Create line segments for color gradient along path
points = np.array([lon, lat]).T.reshape(-1, 1, 2)
segments = np.concatenate([points[:-1], points[1:]], axis=1)

# Color by sequence (progression along trail)
norm = plt.Normalize(sequence.min(), sequence.max())
lc = LineCollection(segments, cmap="viridis", norm=norm, linewidth=4, alpha=0.9)
lc.set_array(sequence[:-1])
line = ax.add_collection(lc)

# Add colorbar to show progression
cbar = fig.colorbar(line, ax=ax, label="Trail Progress", shrink=0.8, pad=0.02)
cbar.ax.tick_params(labelsize=14)
cbar.set_label("Trail Progress", fontsize=18)

# Mark start point (green circle)
ax.scatter(lon[0], lat[0], s=400, c="#2ECC71", marker="o", edgecolors="white", linewidths=3, zorder=5, label="Start")

# Mark end point (red square)
ax.scatter(lon[-1], lat[-1], s=400, c="#E74C3C", marker="s", edgecolors="white", linewidths=3, zorder=5, label="End")

# Add direction arrows at intervals along the path
arrow_indices = np.linspace(20, n_points - 20, 5, dtype=int)
for i in arrow_indices:
    dx = lon[i + 1] - lon[i - 1]
    dy = lat[i + 1] - lat[i - 1]
    ax.annotate(
        "",
        xy=(lon[i] + dx * 0.3, lat[i] + dy * 0.3),
        xytext=(lon[i], lat[i]),
        arrowprops={"arrowstyle": "->", "color": "#333333", "lw": 2.5},
    )

# Labels and styling
ax.set_xlabel("Longitude", fontsize=20)
ax.set_ylabel("Latitude", fontsize=20)
ax.set_title("map-route-path · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper left", framealpha=0.9)
ax.grid(True, alpha=0.3, linestyle="--")

# Set aspect ratio to approximate geographic projection
ax.set_aspect("equal")

# Adjust axis limits with padding
x_margin = (lon.max() - lon.min()) * 0.1
y_margin = (lat.max() - lat.min()) * 0.1
ax.set_xlim(lon.min() - x_margin, lon.max() + x_margin)
ax.set_ylim(lat.min() - y_margin, lat.max() + y_margin)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
