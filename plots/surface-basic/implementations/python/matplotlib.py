""" anyplot.ai
surface-basic: Basic 3D Surface Plot
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-09
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, to_rgba


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: sequential colormap for height (brand green → blue)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]])

# 3D panes read their grid style from rcParams when the axes is created
plt.rcParams.update({"grid.color": to_rgba(INK, 0.15), "grid.linewidth": 0.6})

# Columns: set these to your table's column names
X = "X Axis"  # role: x
Y = "Y Axis"  # role: y
Z = "Amplitude"  # role: z

# Data: replace this block with your own table, for example df = pd.read_csv("grid.csv")
# Damped radial ripple on a 40 × 40 grid, one row per grid point
grid_x, grid_y = np.meshgrid(np.linspace(-4, 4, 40), np.linspace(-4, 4, 40))
radius_sq = grid_x**2 + grid_y**2
df = pd.DataFrame(
    {X: grid_x.ravel(), Y: grid_y.ravel(), Z: (np.sin(np.sqrt(radius_sq)) * np.exp(-0.1 * radius_sq)).ravel()}
)

# Plot: reads only df and the constants above
table = df.pivot_table(index=Y, columns=X, values=Z, sort=True)
XX, YY = np.meshgrid(table.columns.to_numpy(dtype=float), table.index.to_numpy(dtype=float))
ZZ = table.to_numpy(dtype=float)

fig = plt.figure(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="3d", facecolor=PAGE_BG)
fig.subplots_adjust(left=0.0, right=0.92, bottom=0.04, top=0.92)

surf = ax.plot_surface(XX, YY, ZZ, cmap=imprint_seq, linewidth=0, antialiased=False)
ax.view_init(elev=30, azim=45)

# Style
title = "surface-basic · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=4)
ax.set_xlabel(X, fontsize=10, color=INK, labelpad=6)
ax.set_ylabel(Y, fontsize=10, color=INK, labelpad=6)
ax.set_zlabel(Z, fontsize=10, color=INK, labelpad=6)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.tick_params(axis="z", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
    axis.set_pane_color((0, 0, 0, 0))
    axis.pane.set_edgecolor(INK_SOFT)
    axis.line.set_color(INK_SOFT)

cbar = fig.colorbar(surf, ax=ax, shrink=0.6, aspect=14, pad=0.06)
cbar.set_label(Z, fontsize=10, color=INK)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
