""" pyplots.ai
scatter-color-mapped: Color-Mapped Scatter Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data - simulate temperature readings across a geographic grid
np.random.seed(42)
n_points = 150

# Geographic coordinates (longitude, latitude-like)
x = np.random.uniform(-10, 10, n_points)
y = np.random.uniform(-8, 8, n_points)

# Temperature as color variable - warmer near center, cooler at edges
distance_from_center = np.sqrt(x**2 + y**2)
temperature = 35 - distance_from_center * 1.5 + np.random.normal(0, 3, n_points)

# Create figure (4800x2700 at dpi=300 -> figsize=(16, 9))
fig, ax = plt.subplots(figsize=(16, 9))

# Create scatter plot with color mapping using seaborn
sns.scatterplot(
    x=x, y=y, hue=temperature, palette="viridis", size=temperature, sizes=(80, 250), alpha=0.8, ax=ax, legend=False
)

# Add colorbar manually since we disabled legend
norm = plt.Normalize(temperature.min(), temperature.max())
sm = plt.cm.ScalarMappable(cmap="viridis", norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, shrink=0.8, aspect=30, pad=0.02)
cbar.set_label("Temperature (°C)", fontsize=20)
cbar.ax.tick_params(labelsize=16)

# Labels and styling
ax.set_xlabel("Longitude (°E)", fontsize=20)
ax.set_ylabel("Latitude (°N)", fontsize=20)
ax.set_title("scatter-color-mapped · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
