""" anyplot.ai
quiver-basic: Basic Quiver Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 85/100 | Updated: 2026-04-29
"""

import os
import sys


# Prevent this file (matplotlib.py) from shadowing the real matplotlib package
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - circular rotation pattern (u = -y, v = x)
grid_size = 15
x = np.linspace(-3, 3, grid_size)
y = np.linspace(-3, 3, grid_size)
X, Y = np.meshgrid(x, y)

U = -Y
V = X
magnitude = np.sqrt(U**2 + V**2)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

quiver = ax.quiver(
    X, Y, U, V, magnitude, cmap="viridis", scale=25, width=0.008, headwidth=4, headlength=5, headaxislength=4.5
)

# Colorbar
cbar = plt.colorbar(quiver, ax=ax, shrink=0.8, pad=0.02)
cbar.set_label("Vector Magnitude", fontsize=20, color=INK)
cbar.ax.tick_params(labelsize=16, colors=INK_SOFT)
cbar.ax.set_facecolor(PAGE_BG)
cbar.outline.set_edgecolor(INK_SOFT)

# Style
ax.set_xlabel("X Position", fontsize=20, color=INK)
ax.set_ylabel("Y Position", fontsize=20, color=INK)
ax.set_title("quiver-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.set_aspect("equal")

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.grid(True, alpha=0.12, linewidth=0.8, color=INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
