"""anyplot.ai
contour-filled: Filled Contour Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
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

# Imprint diverging colormap: matte red <-> theme-adaptive midpoint <-> blue
MIDPOINT = "#FAF8F1" if THEME == "light" else "#1A1A17"
imprint_div = LinearSegmentedColormap.from_list("imprint_div", ["#AE3030", MIDPOINT, "#4467A3"])

# Constants
N_BANDS = 16  # even, so zero is a band boundary and the color midpoint sits on it

# Columns: set these to your table's column names
X_POS = "Distance east (cm)"  # role: x
Y_POS = "Distance north (cm)"  # role: y
HEIGHT = "Surface height (mm)"  # role: z

# Data: replace this block with your own table, for example df = pd.read_csv("surface.csv")
# A ripple on a water surface: a stone dropped at (-1, 0.5) sends out damped circular waves
gx, gy = np.meshgrid(np.linspace(-9, 9, 360), np.linspace(-5, 5, 200))
radius = np.hypot(gx + 1.0, gy - 0.5)
df = pd.DataFrame(
    {X_POS: gx.ravel(), Y_POS: gy.ravel(), HEIGHT: (4.0 * np.cos(2.2 * radius) * np.exp(-radius / 4.5)).ravel()}
)

# Plot: reads only df and the constants above
grid = df.pivot_table(index=Y_POS, columns=X_POS, values=HEIGHT)
x_vals = grid.columns.to_numpy()
y_vals = grid.index.to_numpy()
limit = np.nanmax(np.abs(grid.to_numpy()))
levels = np.linspace(-limit, limit, N_BANDS + 1)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

filled = ax.contourf(x_vals, y_vals, grid.to_numpy(), levels=levels, cmap=imprint_div)
ax.contour(x_vals, y_vals, grid.to_numpy(), levels=levels, colors=INK_SOFT, linewidths=0.35, alpha=0.55)

cbar = fig.colorbar(filled, ax=ax, pad=0.02, ticks=levels[::2])
cbar.set_label(HEIGHT, fontsize=10, color=INK)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.ax.yaxis.set_major_formatter("{x:.1f}")
cbar.outline.set_edgecolor(INK_SOFT)

# Style
ax.set_title("contour-filled · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(X_POS, fontsize=10, color=INK)
ax.set_ylabel(Y_POS, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
for spine in ax.spines.values():
    spine.set_color(INK_SOFT)
    spine.set_linewidth(0.8)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
