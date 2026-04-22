""" pyplots.ai
scatter-color-mapped: Color-Mapped Scatter Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np


# Data: Simulating geographic temperature measurements
np.random.seed(42)
n_points = 150

# Coordinates (longitude, latitude style)
x = np.random.uniform(-10, 10, n_points)
y = np.random.uniform(-5, 5, n_points)

# Temperature values (influenced by position - warmer toward top-right)
temperature = 15 + 0.8 * x + 1.2 * y + np.random.randn(n_points) * 3

# Create plot (4800x2700 px at 300 dpi = 16x9 inches)
fig, ax = plt.subplots(figsize=(16, 9))

# Scatter plot with colormap
scatter = ax.scatter(x, y, c=temperature, cmap="viridis", s=150, alpha=0.8, edgecolors="white", linewidths=0.5)

# Colorbar with label
cbar = plt.colorbar(scatter, ax=ax, pad=0.02)
cbar.set_label("Temperature (°C)", fontsize=20)
cbar.ax.tick_params(labelsize=16)

# Labels and styling
ax.set_xlabel("Longitude (°)", fontsize=20)
ax.set_ylabel("Latitude (°)", fontsize=20)
ax.set_title("scatter-color-mapped · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
