""" anyplot.ai
contour-3d: 3D Contour Plot
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-22
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint continuous colormap (sequential, single polarity)
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

# Constants
N_LEVELS = 12  # regular contour intervals

# Columns: set these to your table's column names
EAST = "Distance East (km)"  # role: x
NORTH = "Distance North (km)"  # role: y
ELEVATION = "Elevation (m)"  # role: z

# Data: replace this block with your own table, for example df = pd.read_csv("terrain.csv")
gx, gy = np.meshgrid(np.linspace(0, 10, 40), np.linspace(0, 10, 40))
df = pd.DataFrame(
    {
        EAST: gx.ravel(),
        NORTH: gy.ravel(),
        ELEVATION: (
            100 + 30 * np.sin(gx / 2) * np.cos(gy / 2) + 20 * np.exp(-((gx - 5) ** 2 + (gy - 5) ** 2) / 8)
        ).ravel(),
    }
)

# Plot
grid = df.pivot_table(index=NORTH, columns=EAST, values=ELEVATION)
X, Y = np.meshgrid(grid.columns.to_numpy(), grid.index.to_numpy())
Z = grid.to_numpy()
z_min, z_max = np.nanmin(Z), np.nanmax(Z)
levels = np.linspace(z_min, z_max, N_LEVELS + 2)[1:-1]
z_floor = z_min - 0.12 * (z_max - z_min)

fig = plt.figure(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="3d", facecolor=PAGE_BG)
for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
    axis.pane.set_facecolor(PAGE_BG)
    axis.pane.set_edgecolor(INK_SOFT)
    axis.pane.set_alpha(0.1)

# Terrain surface, colored by elevation
surf = ax.plot_surface(X, Y, Z, cmap=imprint_seq, alpha=0.85, edgecolor="none", antialiased=True)

# Level curves lifted to their elevation, drawn in ink so they stand apart from the surface
ax.contour(X, Y, Z, levels=levels, colors=INK, linewidths=0.6, alpha=0.8)

# The same levels projected onto the base plane
ax.contour(X, Y, Z, levels=levels, zdir="z", offset=z_floor, cmap=imprint_seq, linewidths=0.8)
ax.set_zlim(z_floor, z_max)

# Chrome
ax.set_xlabel(EAST, fontsize=9, color=INK, labelpad=6)
ax.set_ylabel(NORTH, fontsize=9, color=INK, labelpad=6)
ax.set_zlabel(ELEVATION, fontsize=9, color=INK, labelpad=4)
ax.set_title("contour-3d · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=2)
ax.tick_params(axis="both", labelsize=7, colors=INK_SOFT)
ax.tick_params(axis="z", labelsize=7, colors=INK_SOFT)
ax.view_init(elev=30, azim=45)

cbar = fig.colorbar(surf, ax=ax, shrink=0.6, aspect=15, pad=0.08)
cbar.set_label(ELEVATION, fontsize=9, color=INK)
cbar.ax.tick_params(labelsize=7, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

fig.subplots_adjust(left=0.02, right=0.95, top=0.95, bottom=0.03)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
