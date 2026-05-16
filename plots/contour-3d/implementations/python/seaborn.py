"""anyplot.ai
contour-3d: 3D Contour Plot
Library: seaborn | Python 3.13
Quality: pending | Created: 2025-05-16
"""

import os
import sys
from pathlib import Path

import numpy as np


# Avoid import collision with matplotlib.py in the same directory
_mpl_path = [p for p in sys.path if "implementations/python" in p]
for p in _mpl_path:
    sys.path.remove(p)

import matplotlib.pyplot as plt  # noqa: E402


sys.path.extend(_mpl_path)

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data
x = np.linspace(-5, 5, 40)
y = np.linspace(-5, 5, 40)
X, Y = np.meshgrid(x, y)
Z = np.exp(-(X**2 + Y**2) / 5) * np.cos(X) * np.sin(Y)

# Plot
fig = plt.figure(figsize=(16, 9), facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="3d")
ax.set_facecolor(PAGE_BG)

# 3D surface
surf = ax.plot_surface(
    X, Y, Z, cmap="viridis", alpha=0.8, edgecolor="none", linewidth=0, antialiased=True
)

# 3D contour lines on surface
ax.contour(X, Y, Z, levels=12, colors=INK_SOFT, alpha=0.4, linewidths=1.5)

# Project contours to base plane
z_min = Z.min() - 0.1
ax.contour(
    X, Y, Z, levels=12, zdir="z", offset=z_min, cmap="viridis", alpha=0.3, linewidths=1.2
)

# Colorbar
cbar = fig.colorbar(surf, ax=ax, pad=0.1, fraction=0.046, aspect=30)
cbar.set_label("Value", fontsize=16, color=INK, labelpad=15)
cbar.ax.tick_params(labelsize=14, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Styling
ax.set_xlabel("X", fontsize=20, color=INK, labelpad=10)
ax.set_ylabel("Y", fontsize=20, color=INK, labelpad=10)
ax.set_zlabel("Z", fontsize=20, color=INK, labelpad=10)
ax.set_title(
    "contour-3d · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=20
)

ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.xaxis.label.set_color(INK)
ax.yaxis.label.set_color(INK)
ax.zaxis.label.set_color(INK)
ax.grid(True, alpha=0.1, color=INK_SOFT, linewidth=0.8)

# Adjust viewing angle for clear visualization
ax.view_init(elev=25, azim=45)

# Panes
ax.xaxis.pane.fill = False
ax.yaxis.pane.fill = False
ax.zaxis.pane.fill = False
ax.xaxis.pane.set_edgecolor(INK_SOFT)
ax.yaxis.pane.set_edgecolor(INK_SOFT)
ax.zaxis.pane.set_edgecolor(INK_SOFT)
ax.xaxis.pane.set_alpha(0.1)
ax.yaxis.pane.set_alpha(0.1)
ax.zaxis.pane.set_alpha(0.1)

plt.tight_layout()

script_dir = Path(__file__).parent
plt.savefig(
    script_dir / f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG
)
