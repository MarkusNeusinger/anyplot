""" pyplots.ai
quiver-basic: Basic Quiver Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 99/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - create a circular rotation pattern (u = -y, v = x)
np.random.seed(42)
grid_size = 15
x = np.linspace(-3, 3, grid_size)
y = np.linspace(-3, 3, grid_size)
X, Y = np.meshgrid(x, y)

# Vector components: rotation field
U = -Y
V = X

# Calculate magnitude for color encoding
magnitude = np.sqrt(U**2 + V**2)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

quiver = ax.quiver(
    X, Y, U, V, magnitude, cmap="viridis", scale=25, width=0.008, headwidth=4, headlength=5, headaxislength=4.5
)

# Colorbar for magnitude
cbar = plt.colorbar(quiver, ax=ax, shrink=0.8, pad=0.02)
cbar.set_label("Vector Magnitude", fontsize=20)
cbar.ax.tick_params(labelsize=16)

# Styling
ax.set_xlabel("X Position", fontsize=20)
ax.set_ylabel("Y Position", fontsize=20)
ax.set_title("quiver-basic · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.set_aspect("equal")
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
