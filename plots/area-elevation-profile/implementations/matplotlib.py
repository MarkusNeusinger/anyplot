""" pyplots.ai
area-elevation-profile: Terrain Elevation Profile Along Transect
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-15
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap


# Data - Alpine hiking trail profile (120 km)
np.random.seed(42)
num_points = 480
distance = np.linspace(0, 120, num_points)

# Build realistic terrain with multiple peaks and valleys
base = 1200
elevation = base + np.zeros(num_points)
# Broad mountain features
elevation += 600 * np.exp(-((distance - 25) ** 2) / 80)
elevation += 900 * np.exp(-((distance - 55) ** 2) / 120)
elevation += 450 * np.exp(-((distance - 85) ** 2) / 60)
elevation += 700 * np.exp(-((distance - 105) ** 2) / 90)
# Smaller ridges and dips
elevation += 200 * np.sin(distance * 0.15) * np.exp(-((distance - 40) ** 2) / 300)
elevation += 150 * np.cos(distance * 0.25)
# Micro-terrain noise
elevation += np.cumsum(np.random.normal(0, 1.5, num_points))
elevation = np.maximum(elevation, 800)

# Landmarks
landmark_labels = ["Bergdorf", "Sonnalm", "Hoher Kamm", "Talbach", "Gipfelkreuz", "Seefeld Hut", "Felsgrat", "Alpstadt"]
landmark_distances = [0, 18, 28, 42, 55, 72, 88, 120]
landmark_elevations = [
    elevation[0],
    elevation[np.argmin(np.abs(distance - 18))],
    elevation[np.argmin(np.abs(distance - 28))],
    elevation[np.argmin(np.abs(distance - 42))],
    elevation[np.argmin(np.abs(distance - 55))],
    elevation[np.argmin(np.abs(distance - 72))],
    elevation[np.argmin(np.abs(distance - 88))],
    elevation[-1],
]
# Build display names with actual elevations from the terrain data
landmark_names = [
    f"{name}\n{int(round(elev))} m" for name, elev in zip(landmark_labels, landmark_elevations, strict=True)
]

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Gradient fill under the profile
gradient_resolution = 200
y_min = 600
y_max = elevation.max()
y_levels = np.linspace(y_min, y_max, gradient_resolution)

cmap = LinearSegmentedColormap.from_list(
    "terrain_fill", ["#2d6a4f", "#40916c", "#74c69d", "#b7e4c7", "#d4a373", "#a0522d", "#6b3a2a"]
)

for i in range(len(y_levels) - 1):
    y_lo = y_levels[i]
    y_hi = y_levels[i + 1]
    clipped = np.clip(elevation, y_lo, y_hi)
    color = cmap(i / (len(y_levels) - 1))
    ax.fill_between(distance, y_lo, clipped, color=color, alpha=0.9, linewidth=0)

# Profile line
ax.plot(distance, elevation, color="#1b4332", linewidth=2.5, zorder=3)

# Landmark annotations
for name, d, e in zip(landmark_names, landmark_distances, landmark_elevations, strict=True):
    ax.plot([d, d], [y_min, e], color="#555555", linewidth=1, linestyle="--", alpha=0.5, zorder=2)
    ax.plot(d, e, "o", color="#1b4332", markersize=7, zorder=4, markeredgecolor="white", markeredgewidth=1)
    # Align edge labels inward to avoid clipping
    if d <= 5:
        ha = "left"
    elif d >= 115:
        ha = "right"
    else:
        ha = "center"
    ax.annotate(
        name,
        xy=(d, e),
        xytext=(0, 18),
        textcoords="offset points",
        fontsize=11,
        fontweight="bold",
        ha=ha,
        va="bottom",
        color="#1b4332",
    )

# Style
ax.set_xlabel("Distance (km)", fontsize=20)
ax.set_ylabel("Elevation (m)", fontsize=20)
ax.set_title(
    "Alpine Trail Profile \u00b7 area-elevation-profile \u00b7 matplotlib \u00b7 pyplots.ai",
    fontsize=24,
    fontweight="medium",
)
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.set_xlim(0, 120)
ax.set_ylim(y_min, y_max + 200)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)

# Vertical exaggeration note
ax.text(
    0.99,
    0.02,
    "Vertical exaggeration \u2248 10\u00d7",
    transform=ax.transAxes,
    fontsize=12,
    ha="right",
    va="bottom",
    color="#444444",
    fontstyle="italic",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "none", "alpha": 0.75},
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
