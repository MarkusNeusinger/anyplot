""" pyplots.ai
scatter-3d: 3D Scatter Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Simulate protein structure analysis with 3D atomic coordinates
# Representing different protein domains with distinct spatial clustering
np.random.seed(42)

# Domain 1: Alpha helix region (lower left)
n1 = 60
x1 = np.random.randn(n1) * 1.5 + 2
y1 = np.random.randn(n1) * 1.5 + 2
z1 = np.random.randn(n1) * 1.5 + 2

# Domain 2: Beta sheet region (upper right)
n2 = 50
x2 = np.random.randn(n2) * 1.2 + 7
y2 = np.random.randn(n2) * 1.2 + 7
z2 = np.random.randn(n2) * 1.2 + 7

# Domain 3: Loop region (middle-high)
n3 = 40
x3 = np.random.randn(n3) * 1.0 + 5
y3 = np.random.randn(n3) * 1.0 + 4
z3 = np.random.randn(n3) * 1.0 + 9

# Combine all domains
x = np.concatenate([x1, x2, x3])
y = np.concatenate([y1, y2, y3])
z = np.concatenate([z1, z2, z3])

# Color based on z-value (representing depth/elevation in Angstroms)
colors = z

# Create 3D plot
fig = plt.figure(figsize=(16, 9))
ax = fig.add_subplot(111, projection="3d")

# Scatter plot with color encoding
scatter = ax.scatter(x, y, z, c=colors, cmap="viridis", s=120, alpha=0.7, edgecolors="white", linewidth=0.5)

# Add colorbar with improved positioning (closer to plot, better proportions)
cbar = fig.colorbar(scatter, ax=ax, shrink=0.65, aspect=25, pad=0.02, location="left")
cbar.set_label("Elevation (Å)", fontsize=18)
cbar.ax.tick_params(labelsize=14)

# Labels with realistic scientific context (molecular coordinates in Angstroms)
ax.set_xlabel("X Coordinate (Å)", fontsize=18, labelpad=15)
ax.set_ylabel("Y Coordinate (Å)", fontsize=18, labelpad=15)
ax.set_zlabel("Z Coordinate (Å)", fontsize=18, labelpad=15)
ax.set_title("Protein Structure · scatter-3d · matplotlib · pyplots.ai", fontsize=24, pad=20)

# Tick parameters
ax.tick_params(axis="x", labelsize=14)
ax.tick_params(axis="y", labelsize=14)
ax.tick_params(axis="z", labelsize=14)

# Set viewing angle for better visualization
ax.view_init(elev=25, azim=45)

# Subtle pane styling
ax.xaxis.pane.fill = False
ax.yaxis.pane.fill = False
ax.zaxis.pane.fill = False
ax.xaxis.pane.set_edgecolor("gray")
ax.yaxis.pane.set_edgecolor("gray")
ax.zaxis.pane.set_edgecolor("gray")
ax.xaxis.pane.set_alpha(0.3)
ax.yaxis.pane.set_alpha(0.3)
ax.zaxis.pane.set_alpha(0.3)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
