""" anyplot.ai
wireframe-3d-basic: Basic 3D Wireframe Plot
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-22
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: position 1 is the single-series color
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
X = "Distance from center (X)"  # role: x
Y = "Distance from center (Y)"  # role: y
Z = "Amplitude (Z)"  # role: z

# Data: replace this block with your own table, for example df = pd.read_csv("surface.csv")
# Ripple function z = sin(sqrt(x^2 + y^2)) on a 40 x 40 grid, one row per grid point
grid_x, grid_y = np.meshgrid(np.linspace(-6, 6, 40), np.linspace(-6, 6, 40))
df = pd.DataFrame({X: grid_x.ravel(), Y: grid_y.ravel(), Z: np.sin(np.sqrt(grid_x**2 + grid_y**2)).ravel()})

# Plot: reads only df and the constants above
surface = df.pivot_table(index=Y, columns=X, values=Z, sort=True, dropna=False)
mesh_x, mesh_y = np.meshgrid(surface.columns.to_numpy(), surface.index.to_numpy())

fig = plt.figure(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="3d", facecolor=PAGE_BG)

ax.plot_wireframe(mesh_x, mesh_y, surface.to_numpy(), color=IMPRINT_PALETTE[0], linewidth=0.9, alpha=0.9)
ax.view_init(elev=30, azim=45)
ax.set_box_aspect((1, 1, 0.7), zoom=0.95)

# Style
title = "wireframe-3d-basic · python · matplotlib · anyplot.ai"
fig.suptitle(title, fontsize=12, color=INK, y=0.97)
ax.set_xlabel(X, fontsize=10, labelpad=6, color=INK)
ax.set_ylabel(Y, fontsize=10, labelpad=6, color=INK)
ax.set_zlabel(Z, fontsize=10, labelpad=4, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.tick_params(axis="z", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)

for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
    axis.pane.set_facecolor(PAGE_BG)
    axis.pane.set_edgecolor(INK_SOFT)
    axis._axinfo["grid"].update(color=INK_SOFT, linewidth=0.5, linestyle="-")
    axis.line.set_color(INK_SOFT)
ax.grid(True, alpha=0.2)

fig.subplots_adjust(left=0.0, right=1.0, bottom=0.06, top=0.93)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
