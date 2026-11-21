"""anyplot.ai
streamline-basic: Basic Streamline Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-14
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

# Imprint palette: position 1 is the brand green; the sequential map runs green to blue
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]])

# Columns: set these to your table's column names
X = "X Position (m)"  # role: x
Y = "Y Position (m)"  # role: y
U = "Horizontal velocity (m/s)"  # role: u
V = "Vertical velocity (m/s)"  # role: v

# Data: replace this block with your own table, for example df = pd.read_csv("field.csv")
# One row per grid point: a vortex with a weak source at the origin plus a secondary vortex at (1.5, 0)
axis = np.linspace(-3, 3, 40)
gx, gy = np.meshgrid(axis, axis)
u = -0.8 * gy + 0.3 * gx / (gx**2 + gy**2 + 0.1)
v = 0.8 * gx + 0.3 * gy / (gx**2 + gy**2 + 0.1)
dx, dy = gx - 1.5, gy
u += -0.4 * dy / ((dx**2 + dy**2 + 0.5) ** 0.5)
v += 0.4 * dx / ((dx**2 + dy**2 + 0.5) ** 0.5)
df = pd.DataFrame({X: gx.ravel(), Y: gy.ravel(), U: u.ravel(), V: v.ravel()})

# Plot: reads only df and the constants above
field = df.dropna(subset=[X, Y])  # a grid point without coordinates cannot be placed
grid_u = field.pivot(index=Y, columns=X, values=U)
grid_v = field.pivot(index=Y, columns=X, values=V)
xs, ys = grid_u.columns.to_numpy(), grid_u.index.to_numpy()
# Points with a missing velocity are masked, so streamlines stop there instead of crashing
mask = grid_u.isna().to_numpy() | grid_v.isna().to_numpy()
u_arr = np.ma.masked_array(grid_u.to_numpy(), mask=mask)
v_arr = np.ma.masked_array(grid_v.to_numpy(), mask=mask)
speed = np.ma.hypot(u_arr, v_arr)
speed_norm = (speed - speed.min()) / (speed.max() - speed.min() + 1e-6)

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Color and line width both encode speed
strm = ax.streamplot(
    xs,
    ys,
    u_arr,
    v_arr,
    color=speed,
    cmap=imprint_seq,
    linewidth=0.8 + 1.4 * speed_norm,
    density=1.5,
    arrowsize=1.2,
    arrowstyle="->",
)

cbar = fig.colorbar(strm.lines, ax=ax, shrink=0.8, pad=0.02)
cbar.set_label("Velocity magnitude (m/s)", fontsize=10, color=INK)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)
cbar.outline.set_linewidth(0.5)

# Style
ax.set_title("streamline-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(X, fontsize=10, color=INK)
ax.set_ylabel(Y, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.set_aspect("equal")
ax.grid(True, alpha=0.10, linestyle="-", linewidth=0.8, color=INK)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(INK_SOFT)
    ax.spines[side].set_linewidth(0.5)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
