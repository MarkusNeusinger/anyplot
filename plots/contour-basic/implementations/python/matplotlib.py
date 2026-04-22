""" pyplots.ai
contour-basic: Basic Contour Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Simulated topographic elevation map of a mountain region
np.random.seed(42)

# Create a 50x50 grid representing a 10km x 10km area
x = np.linspace(0, 10, 50)  # Distance East (km)
y = np.linspace(0, 10, 50)  # Distance North (km)
X, Y = np.meshgrid(x, y)

# Elevation model with multiple terrain features:
# - Main peak in the northeast
# - Secondary ridge in the southwest
# - Valley running through the center
elevation = (
    # Main peak centered at (7, 7) km
    800 * np.exp(-((X - 7) ** 2 + (Y - 7) ** 2) / 4)
    # Secondary ridge in southwest
    + 500 * np.exp(-((X - 2) ** 2 + (Y - 3) ** 2) / 3)
    # Gentle slope from east
    + 100 * X / 10
    # Valley depression
    - 200 * np.exp(-((X - 5) ** 2 + (Y - 5) ** 2) / 8)
    # Base elevation
    + 200
)

# Create plot (4800x2700 px)
fig, ax = plt.subplots(figsize=(16, 9))

# Custom contour levels every 100m for clear reading
levels = np.arange(200, 1100, 50)

# Filled contours with terrain-appropriate colormap
contourf = ax.contourf(X, Y, elevation, levels=levels, cmap="viridis", alpha=0.9)

# Contour lines with varied styles for key elevations
contour = ax.contour(X, Y, elevation, levels=levels, colors="white", linewidths=0.8, alpha=0.5)

# Highlight major elevation lines (every 200m) with thicker lines
major_levels = np.arange(200, 1100, 200)
contour_major = ax.contour(X, Y, elevation, levels=major_levels, colors="white", linewidths=2.0, alpha=0.8)

# Label major contour levels
ax.clabel(contour_major, inline=True, fontsize=14, fmt="%d m")

# Colorbar to show elevation scale
cbar = fig.colorbar(contourf, ax=ax, shrink=0.9, aspect=20)
cbar.set_label("Elevation (m)", fontsize=20)
cbar.ax.tick_params(labelsize=16)

# Labels and styling
ax.set_xlabel("Distance East (km)", fontsize=20)
ax.set_ylabel("Distance North (km)", fontsize=20)
ax.set_title("Mountain Terrain · contour-basic · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Set equal aspect ratio for geographic data
ax.set_aspect("equal")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
