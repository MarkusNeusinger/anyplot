""" pyplots.ai
surface-basic: Basic 3D Surface Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - create a 40x40 grid for smooth visualization
x = np.linspace(-4, 4, 40)
y = np.linspace(-4, 4, 40)
X, Y = np.meshgrid(x, y)

# Gaussian-like surface with interesting features (radial ripple pattern)
Z = np.sin(np.sqrt(X**2 + Y**2)) * np.exp(-0.1 * (X**2 + Y**2))

# Create 3D plot (4800x2700 px)
fig = plt.figure(figsize=(16, 9))
ax = fig.add_subplot(111, projection="3d")

# Plot surface with colormap
surf = ax.plot_surface(X, Y, Z, cmap="viridis", edgecolor="none", alpha=0.9, antialiased=True)

# Add colorbar
cbar = fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10, pad=0.1)
cbar.set_label("Z Value", fontsize=16)
cbar.ax.tick_params(labelsize=12)

# Labels and styling (scaled font sizes for 4800x2700)
ax.set_xlabel("X Axis", fontsize=18, labelpad=12)
ax.set_ylabel("Y Axis", fontsize=18, labelpad=12)
ax.set_zlabel("Z Axis", fontsize=18, labelpad=12)
ax.set_title("surface-basic · matplotlib · pyplots.ai", fontsize=24, pad=20)

# Tick parameters
ax.tick_params(axis="both", labelsize=14)

# Set viewing angle for good perspective
ax.view_init(elev=30, azim=45)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
