"""anyplot.ai
contour-3d: 3D Contour Plot
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-05-16
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Terrain elevation data with realistic features
np.random.seed(42)
x = np.linspace(0, 10, 40)
y = np.linspace(0, 10, 40)
X, Y = np.meshgrid(x, y)

# Create realistic terrain with peaks and valleys (elevation in meters)
Z = 100 + 30 * np.sin(X / 2) * np.cos(Y / 2) + 20 * np.exp(-((X - 5) ** 2 + (Y - 5) ** 2) / 8)

# Create figure with 3D axes
fig = plt.figure(figsize=(16, 9), facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="3d", facecolor=PAGE_BG)
ax.xaxis.pane.set_facecolor(PAGE_BG)
ax.yaxis.pane.set_facecolor(PAGE_BG)
ax.zaxis.pane.set_facecolor(PAGE_BG)

# Plot surface with semi-transparency
surf = ax.plot_surface(X, Y, Z, cmap="viridis", alpha=0.6, edgecolor="none", antialiased=True)

# Add 3D contour lines on the surface
contours = ax.contour(X, Y, Z, levels=12, cmap="viridis", linewidths=2)

# Project contours onto the base plane (z = min)
z_offset = Z.min() - 5
ax.contour(X, Y, Z, levels=12, zdir="z", offset=z_offset, cmap="viridis", linewidths=1.5)

# Styling - theme-adaptive chrome
ax.set_xlabel("Distance East (km)", fontsize=20, color=INK, labelpad=15)
ax.set_ylabel("Distance North (km)", fontsize=20, color=INK, labelpad=15)
ax.set_zlabel("Elevation (m)", fontsize=20, color=INK, labelpad=15)
ax.set_title("contour-3d · matplotlib · anyplot.ai", fontsize=24, color=INK, pad=20)

# Tick params with theme-adaptive colors
ax.tick_params(axis="x", labelsize=16, colors=INK_SOFT)
ax.tick_params(axis="y", labelsize=16, colors=INK_SOFT)
ax.tick_params(axis="z", labelsize=16, colors=INK_SOFT)

# Set pane edge colors
ax.xaxis.pane.set_edgecolor(INK_SOFT)
ax.yaxis.pane.set_edgecolor(INK_SOFT)
ax.zaxis.pane.set_edgecolor(INK_SOFT)
ax.xaxis.pane.set_alpha(0.1)
ax.yaxis.pane.set_alpha(0.1)
ax.zaxis.pane.set_alpha(0.1)

# Set view angle
ax.view_init(elev=30, azim=45)

# Add colorbar with theme-adaptive colors
cbar = fig.colorbar(surf, ax=ax, shrink=0.6, aspect=15, pad=0.1)
cbar.set_label("Elevation (m)", fontsize=16, color=INK)
cbar.ax.tick_params(labelsize=14, colors=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
