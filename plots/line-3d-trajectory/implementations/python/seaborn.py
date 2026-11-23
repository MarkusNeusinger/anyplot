"""anyplot.ai
line-3d-trajectory: 3D Line Plot for Trajectory Visualization
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-11-23
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.cm import ScalarMappable
from matplotlib.colors import LinearSegmentedColormap, Normalize
from mpl_toolkits.mplot3d.art3d import Line3DCollection


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "#DAD8D0" if THEME == "light" else "#3A3A35"

# Imprint palette: canonical order, first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential ramp (single polarity) for the progression along the path
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
        "grid.color": GRID,
        "grid.linewidth": 0.6,
    },
)

# Columns: set these to your table's column names
X_POS = "X (convection rate)"  # role: x
Y_POS = "Y (temperature difference)"  # role: y
Z_POS = "Z (vertical temperature deviation)"  # role: z
TIME = "Time step"  # role: color

# Data: replace this block with your own table, for example df = pd.read_csv("trajectory.csv")
# Lorenz attractor integrated with explicit Euler steps
dt = 0.01
num_steps = 2000
sigma, rho, beta = 10, 28, 8 / 3
path = np.zeros((num_steps, 3))
path[0] = (1, 1, 1)
for i in range(num_steps - 1):
    px, py, pz = path[i]
    path[i + 1] = path[i] + dt * np.array([sigma * (py - px), px * (rho - pz) - py, px * py - beta * pz])
df = pd.DataFrame({X_POS: path[:, 0], Y_POS: path[:, 1], Z_POS: path[:, 2], TIME: np.arange(num_steps)})

# Plot: reads only df and the constants above
points = df[[X_POS, Y_POS, Z_POS]].to_numpy()
segments = np.stack([points[:-1], points[1:]], axis=1)
norm = Normalize(vmin=df[TIME].min(), vmax=df[TIME].max())

fig = plt.figure(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax = fig.add_axes([0.07, 0.0, 0.8, 0.93], projection="3d")
ax.set_facecolor(PAGE_BG)

# One continuous line, colored by sequence position; slight transparency keeps strands traceable
if len(segments) > 0:
    line = Line3DCollection(segments, cmap=imprint_seq, norm=norm, linewidth=1.1, alpha=0.9)
    line.set_array(df[TIME].to_numpy()[:-1])
    ax.add_collection3d(line)

# Mark the start and end of the path
ax.scatter(*points[0], s=40, color=INK, edgecolor=PAGE_BG, linewidth=0.8, depthshade=False, zorder=10)
ax.scatter(*points[-1], s=40, color=IMPRINT_PALETTE[4], edgecolor=PAGE_BG, linewidth=0.8, depthshade=False, zorder=10)

for setter, col in ((ax.set_xlim, X_POS), (ax.set_ylim, Y_POS), (ax.set_zlim, Z_POS)):
    setter(df[col].min(), df[col].max())
ax.set_box_aspect(None, zoom=0.95)
ax.view_init(elev=22, azim=-58)

# Style
ax.set_xlabel(X_POS, fontsize=8, labelpad=4)
ax.set_ylabel(Y_POS, fontsize=8, labelpad=4)
ax.set_zlabel(Z_POS, fontsize=8, labelpad=2)
ax.set_title("line-3d-trajectory · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=7)
ax.tick_params(axis="z", labelsize=7)
for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
    axis.pane.set_facecolor(PAGE_BG)
    axis.pane.set_edgecolor(INK_SOFT)
    axis.pane.set_alpha(0.0)
ax.grid(True)

cbar = fig.colorbar(ScalarMappable(norm=norm, cmap=imprint_seq), cax=fig.add_axes([0.86, 0.28, 0.014, 0.44]))
cbar.set_label(TIME, fontsize=8, color=INK)
cbar.ax.tick_params(labelsize=7, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
