""" pyplots.ai
contour-map-geographic: Contour Lines on Geographic Map
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-17
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Simplified world coastline polygons (major continents outline)
WORLD_COASTLINES = [
    # North America
    [
        (-168, 66),
        (-141, 70),
        (-130, 70),
        (-120, 60),
        (-125, 50),
        (-125, 40),
        (-117, 33),
        (-105, 25),
        (-97, 26),
        (-82, 25),
        (-81, 30),
        (-75, 35),
        (-70, 42),
        (-67, 45),
        (-60, 47),
        (-55, 52),
        (-60, 60),
        (-65, 68),
        (-80, 70),
        (-100, 73),
        (-120, 75),
        (-145, 72),
        (-168, 66),
    ],
    # South America
    [
        (-82, 10),
        (-77, 0),
        (-80, -5),
        (-70, -15),
        (-60, -5),
        (-50, 0),
        (-35, -5),
        (-40, -23),
        (-55, -35),
        (-68, -55),
        (-75, -50),
        (-75, -40),
        (-70, -20),
        (-80, -5),
        (-82, 10),
    ],
    # Europe
    [
        (-10, 36),
        (-10, 45),
        (-5, 48),
        (0, 52),
        (5, 55),
        (10, 58),
        (20, 60),
        (28, 70),
        (35, 70),
        (30, 60),
        (25, 55),
        (20, 50),
        (15, 45),
        (20, 40),
        (25, 35),
        (35, 35),
        (28, 42),
        (20, 38),
        (10, 38),
        (-10, 36),
    ],
    # Africa
    [
        (-17, 15),
        (-17, 28),
        (-5, 36),
        (10, 38),
        (20, 33),
        (35, 30),
        (45, 12),
        (52, 12),
        (45, 0),
        (42, -10),
        (35, -25),
        (25, -34),
        (18, -35),
        (12, -20),
        (15, -5),
        (5, 5),
        (-10, 5),
        (-17, 15),
    ],
    # Asia
    [
        (35, 30),
        (45, 42),
        (52, 45),
        (70, 42),
        (80, 30),
        (75, 15),
        (90, 22),
        (100, 15),
        (105, 22),
        (110, 5),
        (120, 25),
        (130, 35),
        (140, 45),
        (145, 55),
        (135, 70),
        (100, 78),
        (70, 75),
        (50, 70),
        (30, 70),
        (35, 50),
        (45, 45),
        (35, 30),
    ],
    # Australia
    [
        (113, -22),
        (120, -18),
        (135, -12),
        (145, -15),
        (152, -25),
        (150, -38),
        (140, -38),
        (130, -33),
        (115, -35),
        (113, -22),
    ],
]

# Data: Global temperature anomaly grid (simulated climate data)
np.random.seed(42)

# Create regular lat/lon grid covering the world
lon = np.linspace(-180, 180, 72)  # 5-degree resolution
lat = np.linspace(-70, 85, 32)  # 5-degree resolution
LON, LAT = np.meshgrid(lon, lat)

# Create realistic temperature anomaly pattern
# - Higher anomalies near poles (Arctic amplification)
# - Land-sea patterns
# - Some regional variation

# Base pattern: higher anomalies at high latitudes
anomaly_base = 0.5 + 1.5 * (np.abs(LAT) / 90) ** 1.5

# Add regional variations with smooth gradients
anomaly_regional = 0.8 * np.sin(np.radians(LON * 2)) * np.cos(np.radians(LAT * 1.5)) + 0.6 * np.cos(
    np.radians(LON + 60)
) * np.sin(np.radians(LAT * 2))

# Add some spatial noise (smoothed)
noise = np.random.randn(32, 72) * 0.3

# Combine components: temperature anomaly in degrees Celsius
Z = anomaly_base + anomaly_regional + noise
Z = np.clip(Z, -2.0, 4.5)  # Realistic anomaly range

# Apply seaborn styling
sns.set_theme(style="whitegrid", context="talk", font_scale=1.1)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Set map extent and ocean background
ax.set_xlim(-180, 180)
ax.set_ylim(-70, 85)
ax.set_facecolor("#d4e8f7")  # Light ocean blue

# Draw filled contours for temperature anomalies
levels = np.linspace(-2, 4.5, 14)
contourf = ax.contourf(
    LON,
    LAT,
    Z,
    levels=levels,
    cmap="RdYlBu_r",  # Red (warm) to blue (cool) reversed
    alpha=0.85,
    extend="both",
    zorder=1,
)

# Overlay contour lines with labels
contour = ax.contour(
    LON,
    LAT,
    Z,
    levels=levels[::2],  # Label every other level
    colors="black",
    linewidths=1.2,
    alpha=0.7,
    zorder=2,
)

# Label contour lines with temperature values
ax.clabel(contour, inline=True, fontsize=12, fmt="%.1f°C", colors="black")

# Draw simplified coastlines on top with fill for land masses
for coastline in WORLD_COASTLINES:
    if len(coastline) > 2:
        lons = [p[0] for p in coastline]
        lats = [p[1] for p in coastline]
        # Fill land masses with subtle gray
        ax.fill(lons, lats, color="none", edgecolor="#2d2d2d", linewidth=2.0, zorder=3)

# Add colorbar with proper sizing
cbar = fig.colorbar(contourf, ax=ax, shrink=0.75, pad=0.02, aspect=30)
cbar.set_label("Temperature Anomaly (°C)", fontsize=18)
cbar.ax.tick_params(labelsize=14)

# Labels and styling
ax.set_xlabel("Longitude (°)", fontsize=20)
ax.set_ylabel("Latitude (°)", fontsize=20)
ax.set_title(
    "Global Temperature Anomaly · contour-map-geographic · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=15
)
ax.tick_params(axis="both", labelsize=16)

# Add gridlines
ax.grid(True, alpha=0.3, linestyle="--", color="#888888", zorder=0)
ax.set_axisbelow(True)

# Set aspect ratio for geographic accuracy
ax.set_aspect("equal", adjustable="box")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
