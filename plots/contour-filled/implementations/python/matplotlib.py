""" pyplots.ai
contour-filled: Filled Contour Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - create a meshgrid with an interesting mathematical surface
np.random.seed(42)
x = np.linspace(-3, 3, 80)
y = np.linspace(-3, 3, 80)
X, Y = np.meshgrid(x, y)

# Create a surface with multiple Gaussian peaks and a saddle point
# This demonstrates various features: peaks, valleys, and gradients
Z = (
    1.5 * np.exp(-((X - 1) ** 2 + (Y - 1) ** 2))  # Peak at (1, 1)
    + 1.2 * np.exp(-((X + 1.5) ** 2 + (Y + 1) ** 2) / 1.5)  # Peak at (-1.5, -1)
    - 0.8 * np.exp(-((X + 0.5) ** 2 + (Y - 1.5) ** 2) / 0.8)  # Valley at (-0.5, 1.5)
    + 0.5 * np.exp(-((X - 1.5) ** 2 + (Y + 1.5) ** 2))  # Small peak at (1.5, -1.5)
)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Define number of contour levels for smooth transitions
levels = 15

# Create filled contour plot with a sequential colormap
contourf = ax.contourf(X, Y, Z, levels=levels, cmap="viridis")

# Overlay contour lines for precise level identification
ax.contour(X, Y, Z, levels=levels, colors="white", linewidths=0.8, alpha=0.5)

# Add colorbar to indicate value mapping
cbar = plt.colorbar(contourf, ax=ax, shrink=0.9, pad=0.02)
cbar.set_label("Surface Height (z)", fontsize=20)
cbar.ax.tick_params(labelsize=16)

# Styling
ax.set_xlabel("X Position", fontsize=20)
ax.set_ylabel("Y Position", fontsize=20)
ax.set_title("contour-filled · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Make the plot aspect ratio equal for proper visualization
ax.set_aspect("equal", adjustable="box")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
