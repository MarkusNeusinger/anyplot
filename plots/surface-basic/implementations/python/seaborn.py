""" anyplot.ai
surface-basic: Basic 3D Surface Plot
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-11
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint sequential colormap (continuous height)
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
    },
)

# Constants
GRID_POINTS = 40  # grid size per axis (spec: 30x30 to 50x50)
DOMAIN = 5  # x and y range from -DOMAIN to DOMAIN
DECAY = 0.1  # Gaussian damping of the ripple

# Columns: set these to your table's column names
X_COORD = "X"  # role: x
Y_COORD = "Y"  # role: y
HEIGHT = "Height (Z)"  # role: z

# Data: replace this block with your own table, for example df = pd.read_csv("surface.csv")
# One row per grid point: z = sin(r) * exp(-DECAY * r^2)
grid_x, grid_y = np.meshgrid(np.linspace(-DOMAIN, DOMAIN, GRID_POINTS), np.linspace(-DOMAIN, DOMAIN, GRID_POINTS))
radius2 = grid_x**2 + grid_y**2
df = pd.DataFrame(
    {
        X_COORD: grid_x.ravel(),
        Y_COORD: grid_y.ravel(),
        HEIGHT: (np.sin(np.sqrt(radius2)) * np.exp(-DECAY * radius2)).ravel(),
    }
)

# Plot
surface = df.pivot_table(index=Y_COORD, columns=X_COORD, values=HEIGHT)
X, Y = np.meshgrid(surface.columns.to_numpy(), surface.index.to_numpy())
Z = surface.to_numpy()

fig = plt.figure(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="3d")
ax.set_facecolor(PAGE_BG)

surf = ax.plot_surface(X, Y, Z, cmap=imprint_seq, edgecolor="none", rstride=1, cstride=1)

# Style
ax.set_xlabel(X_COORD, fontsize=10, color=INK, labelpad=4)
ax.set_ylabel(Y_COORD, fontsize=10, color=INK, labelpad=4)
ax.set_zlabel("Z", fontsize=10, color=INK, labelpad=4)
ax.set_title("surface-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=4)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.tick_params(axis="z", labelsize=8, colors=INK_SOFT)
for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
    axis.set_pane_color(PAGE_BG)
    axis.pane.set_edgecolor(INK_SOFT)
ax.grid(False)
ax.view_init(elev=25, azim=45)

cbar = fig.colorbar(surf, ax=ax, pad=0.08, shrink=0.7)
cbar.set_label(HEIGHT, fontsize=10, color=INK, labelpad=6)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
