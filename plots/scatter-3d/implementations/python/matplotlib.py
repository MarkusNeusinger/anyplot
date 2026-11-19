"""anyplot.ai
scatter-3d: 3D Scatter Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-08
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

# Imprint palette: continuous colormap built from its first and third positions
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]])

# Columns: set these to your table's column names
X = "X Coordinate (Å)"  # role: x
Y = "Y Coordinate (Å)"  # role: y
Z = "Z Coordinate (Å)"  # role: z
ELEVATION = "Elevation (Å)"  # role: color

# Data: replace this block with your own table, for example df = pd.read_csv("atoms.csv")
# Protein structure analysis: atomic coordinates of three domains (helix, sheet, loop)
rng = np.random.default_rng(42)
domains = [(60, 1.5, (2, 2, 2)), (50, 1.2, (7, 7, 7)), (40, 1.0, (5, 4, 9))]
coords = np.vstack([rng.normal(center, spread, size=(n, 3)) for n, spread, center in domains])
df = pd.DataFrame({X: coords[:, 0], Y: coords[:, 1], Z: coords[:, 2]})
df[ELEVATION] = df[Z]

# Plot: reads only df and the constants above
fig = plt.figure(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="3d")
ax.set_facecolor(PAGE_BG)

scatter = ax.scatter(
    df[X], df[Y], df[Z], c=df[ELEVATION], cmap=imprint_seq, s=45, alpha=0.75, edgecolors=PAGE_BG, linewidth=0.4
)

cbar = fig.colorbar(scatter, ax=ax, shrink=0.65, aspect=25, pad=0.08)
cbar.set_label(ELEVATION, fontsize=10, color=INK)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

ax.set_xlabel(X, fontsize=10, labelpad=8, color=INK)
ax.set_ylabel(Y, fontsize=10, labelpad=8, color=INK)
ax.set_zlabel(Z, fontsize=10, labelpad=6, color=INK)
ax.set_title("scatter-3d · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", pad=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.tick_params(axis="z", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)

# Oblique view so all three axes have visible extent
ax.view_init(elev=25, azim=45)

# Depth cues: faint panes with visible edges and grid lines
for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
    axis.pane.set_facecolor(INK_SOFT)
    axis.pane.set_alpha(0.06)
    axis.pane.set_edgecolor(INK_SOFT)
    axis._axinfo["grid"].update(color=INK_SOFT, linewidth=0.6, alpha=0.35)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
