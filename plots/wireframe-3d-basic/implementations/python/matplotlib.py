""" pyplots.ai
wireframe-3d-basic: Basic 3D Wireframe Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - create ripple function z = sin(sqrt(x^2 + y^2))
np.random.seed(42)
x = np.linspace(-6, 6, 40)
y = np.linspace(-6, 6, 40)
X, Y = np.meshgrid(x, y)
R = np.sqrt(X**2 + Y**2)
Z = np.sin(R)

# Create 3D plot
fig = plt.figure(figsize=(16, 9))
ax = fig.add_subplot(111, projection="3d")

# Plot wireframe with Python Blue color
ax.plot_wireframe(X, Y, Z, color="#306998", linewidth=1.5, alpha=0.8)

# Set viewing angle (elevation 30, azimuth 45 as per spec)
ax.view_init(elev=30, azim=45)

# Labels and styling
ax.set_xlabel("X", fontsize=20, labelpad=15)
ax.set_ylabel("Y", fontsize=20, labelpad=15)
ax.set_zlabel("Z", fontsize=20, labelpad=15)
ax.set_title("wireframe-3d-basic · matplotlib · pyplots.ai", fontsize=24, pad=20)

# Tick parameters
ax.tick_params(axis="both", labelsize=14)
ax.tick_params(axis="z", labelsize=14)

# Subtle grid panes
ax.xaxis.pane.fill = False
ax.yaxis.pane.fill = False
ax.zaxis.pane.fill = False
ax.xaxis.pane.set_edgecolor("gray")
ax.yaxis.pane.set_edgecolor("gray")
ax.zaxis.pane.set_edgecolor("gray")
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
