""" pyplots.ai
heatmap-geographic: Geographic Heatmap for Spatial Density
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-10
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data: Simulated event locations in a city region (San Francisco Bay Area coordinates)
np.random.seed(42)

# Create clustered geographic data with hotspots
# Downtown cluster (high density area)
downtown_lat = np.random.normal(37.79, 0.015, 300)
downtown_lon = np.random.normal(-122.41, 0.015, 300)

# Secondary cluster (financial district)
financial_lat = np.random.normal(37.795, 0.008, 200)
financial_lon = np.random.normal(-122.395, 0.008, 200)

# Scattered points (suburban areas)
scattered_lat = np.random.normal(37.78, 0.04, 200)
scattered_lon = np.random.normal(-122.42, 0.04, 200)

# Smaller cluster (marina area)
marina_lat = np.random.normal(37.805, 0.01, 100)
marina_lon = np.random.normal(-122.435, 0.01, 100)

# Combine all points
latitude = np.concatenate([downtown_lat, financial_lat, scattered_lat, marina_lat])
longitude = np.concatenate([downtown_lon, financial_lon, scattered_lon, marina_lon])

# Create plot with seaborn KDE
fig, ax = plt.subplots(figsize=(16, 9))

# Set style for better visualization
sns.set_style("whitegrid")

# Create 2D KDE plot with seaborn - geographic heatmap
kde = sns.kdeplot(
    x=longitude,
    y=latitude,
    ax=ax,
    fill=True,
    cmap="YlOrRd",
    levels=30,
    thresh=0.02,
    alpha=0.85,
    cbar=True,
    cbar_kws={"label": "Density", "shrink": 0.8},
)

# Overlay scatter points with low alpha to show data locations
ax.scatter(longitude, latitude, s=15, alpha=0.3, c="#306998", edgecolors="none", zorder=5)

# Add geographic context with gridlines
ax.set_axisbelow(True)
ax.grid(True, alpha=0.3, linestyle="--", color="gray")

# Labels with proper styling for large canvas
ax.set_xlabel("Longitude (°W)", fontsize=20)
ax.set_ylabel("Latitude (°N)", fontsize=20)
ax.set_title("heatmap-geographic · seaborn · pyplots.ai", fontsize=24, pad=15)
ax.tick_params(axis="both", labelsize=16)

# Format tick labels to show degree symbols
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{abs(x):.2f}°"))
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.2f}°"))

# Adjust colorbar text size
cbar = ax.collections[-1].colorbar
if cbar:
    cbar.ax.tick_params(labelsize=14)
    cbar.set_label("Event Density", fontsize=18)

# Set equal aspect ratio for geographic accuracy
ax.set_aspect("equal", adjustable="box")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
