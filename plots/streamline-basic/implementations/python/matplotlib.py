""" pyplots.ai
streamline-basic: Basic Streamline Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-31
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Create a vortex flow field
np.random.seed(42)

# Grid setup (40x40 for smooth streamlines)
x = np.linspace(-3, 3, 40)
y = np.linspace(-3, 3, 40)
X, Y = np.meshgrid(x, y)

# Vortex flow field: u = -y, v = x (creates circular streamlines)
# Add a second vortex offset to show more interesting flow patterns
U = -Y + 0.5 * np.exp(-((X - 1.5) ** 2 + Y**2))
V = X + 0.5 * np.exp(-((X + 1.5) ** 2 + Y**2))

# Calculate velocity magnitude for color mapping
speed = np.sqrt(U**2 + V**2)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Create streamlines with color based on velocity magnitude
strm = ax.streamplot(X, Y, U, V, color=speed, cmap="viridis", linewidth=2.5, density=1.5, arrowsize=2, arrowstyle="->")

# Colorbar for velocity magnitude
cbar = fig.colorbar(strm.lines, ax=ax, shrink=0.8, pad=0.02)
cbar.set_label("Velocity Magnitude", fontsize=20)
cbar.ax.tick_params(labelsize=16)

# Styling
ax.set_xlabel("X Position", fontsize=20)
ax.set_ylabel("Y Position", fontsize=20)
ax.set_title("streamline-basic · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.set_aspect("equal")
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
