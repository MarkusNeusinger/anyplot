""" pyplots.ai
contour-3d: 3D Contour Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-07
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Create a surface with interesting features for visualization
np.random.seed(42)
x = np.linspace(-3, 3, 40)
y = np.linspace(-3, 3, 40)
X, Y = np.meshgrid(x, y)

# Create a surface combining peaks and valleys (simulates terrain or potential field)
Z = (1 - X / 2 + X**5 + Y**3) * np.exp(-(X**2) - Y**2) * 3

# Create figure with 3D axes
fig = plt.figure(figsize=(16, 9))
ax = fig.add_subplot(111, projection="3d")

# Plot surface with semi-transparency
surf = ax.plot_surface(X, Y, Z, cmap="viridis", alpha=0.6, edgecolor="none", antialiased=True)

# Add 3D contour lines on the surface
contours = ax.contour(X, Y, Z, levels=12, cmap="viridis", linewidths=2)

# Project contours onto the base plane (z = min)
z_offset = Z.min() - 0.3
ax.contour(X, Y, Z, levels=12, zdir="z", offset=z_offset, cmap="viridis", linewidths=1.5)

# Styling
ax.set_xlabel("X Position", fontsize=18, labelpad=15)
ax.set_ylabel("Y Position", fontsize=18, labelpad=15)
ax.set_zlabel("Amplitude", fontsize=18, labelpad=15)
ax.set_title("contour-3d \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24, pad=20)

# Tick params
ax.tick_params(axis="both", labelsize=14)

# Set view angle
ax.view_init(elev=30, azim=45)

# Add colorbar
cbar = fig.colorbar(surf, ax=ax, shrink=0.6, aspect=15, pad=0.1)
cbar.set_label("Amplitude", fontsize=16)
cbar.ax.tick_params(labelsize=14)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
