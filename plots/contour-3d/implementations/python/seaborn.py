""" anyplot.ai
contour-3d: 3D Contour Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 86/100 | Created: 2026-05-16
"""

import os
import sys


# Remove script directory temporarily — local matplotlib.py would shadow the package
_here = sys.path.pop(0)

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


sys.path.insert(0, _here)

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

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
        "grid.color": INK,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Data — vibration displacement on a plate (physical science context)
x = np.linspace(-5, 5, 40)
y = np.linspace(-5, 5, 40)
X, Y = np.meshgrid(x, y)
Z_raw = np.exp(-(X**2 + Y**2) / 5) * np.cos(X) * np.sin(Y)
Z = Z_raw * 10  # scale to micrometers

# Seaborn's color palette API for the continuous colormap
cmap = sns.color_palette("viridis", as_cmap=True)

# Plot
fig = plt.figure(figsize=(16, 9), facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="3d")
ax.set_facecolor(PAGE_BG)

# 3D surface
surf = ax.plot_surface(X, Y, Z, cmap=cmap, alpha=0.85, edgecolor="none", linewidth=0, antialiased=True)

# On-surface contour lines
ax.contour(X, Y, Z, levels=12, colors=INK_SOFT, alpha=0.5, linewidths=1.5)

# Projected contours onto base plane — increased alpha and linewidth for visibility
z_min = Z.min() - 0.8
ax.contour(X, Y, Z, levels=12, zdir="z", offset=z_min, cmap=cmap, alpha=0.6, linewidths=2.0)

# Colorbar
cbar = fig.colorbar(surf, ax=ax, pad=0.1, fraction=0.046, aspect=30)
cbar.set_label("Displacement (μm)", fontsize=16, color=INK, labelpad=15)
cbar.ax.tick_params(labelsize=14, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Axis labels with physical units
ax.set_xlabel("x Position (cm)", fontsize=20, color=INK, labelpad=10)
ax.set_ylabel("y Position (cm)", fontsize=20, color=INK, labelpad=10)
ax.set_zlabel("Displacement (μm)", fontsize=20, color=INK, labelpad=10)
ax.set_title("contour-3d · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=20)

ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.xaxis.label.set_color(INK)
ax.yaxis.label.set_color(INK)
ax.zaxis.label.set_color(INK)
ax.grid(True, alpha=0.1, color=INK_SOFT, linewidth=0.8)

ax.view_init(elev=25, azim=45)

# Panes — edges only, no fill
ax.xaxis.pane.fill = False
ax.yaxis.pane.fill = False
ax.zaxis.pane.fill = False
ax.xaxis.pane.set_edgecolor(INK_SOFT)
ax.yaxis.pane.set_edgecolor(INK_SOFT)
ax.zaxis.pane.set_edgecolor(INK_SOFT)
ax.xaxis.pane.set_alpha(0.1)
ax.yaxis.pane.set_alpha(0.1)
ax.zaxis.pane.set_alpha(0.1)

# Peak annotation — identify and label the maximum displacement point
peak_idx = np.unravel_index(np.argmax(Z), Z.shape)
peak_x, peak_y, peak_z = X[peak_idx], Y[peak_idx], Z[peak_idx]
ax.text(
    peak_x,
    peak_y,
    peak_z + 0.6,
    f"Peak: {peak_z:.1f} μm",
    fontsize=14,
    color=INK,
    bbox={"facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.9, "boxstyle": "round,pad=0.3"},
    ha="center",
)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
