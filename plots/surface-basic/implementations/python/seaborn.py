""" anyplot.ai
surface-basic: Basic 3D Surface Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 85/100 | Created: 2026-05-05
"""

import os
import sys


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/../../../../.venv/lib/python3.13/site-packages")

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data
np.random.seed(42)
x = np.linspace(-5, 5, 40)
y = np.linspace(-5, 5, 40)
X, Y = np.meshgrid(x, y)
Z = np.sin(np.sqrt(X**2 + Y**2)) * np.exp(-0.1 * (X**2 + Y**2))

# Plot
fig = plt.figure(figsize=(16, 9), facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="3d")
ax.set_facecolor(PAGE_BG)

surf = ax.plot_surface(X, Y, Z, cmap="viridis", alpha=0.95, edgecolor="none")

# Style
ax.set_xlabel("X", fontsize=20, color=INK, labelpad=15)
ax.set_ylabel("Y", fontsize=20, color=INK, labelpad=15)
ax.set_zlabel("Z", fontsize=20, color=INK, labelpad=15)
ax.set_title("surface-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=20)

ax.tick_params(axis="both", labelsize=14, colors=INK_SOFT)
for spine in ax.spines.values():
    spine.set_edgecolor(INK_SOFT)
ax.grid(False)

# Colorbar
cbar = fig.colorbar(surf, ax=ax, pad=0.1, shrink=0.8)
cbar.set_label("Height", fontsize=16, color=INK, labelpad=10)
cbar.ax.tick_params(labelsize=14, colors=INK_SOFT)

ax.view_init(elev=25, azim=45)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
plt.close()
