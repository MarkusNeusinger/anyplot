"""anyplot.ai
contour-filled: Filled Contour Plot
Library: matplotlib | Python 3.13
Quality: pending | Created: 2025-05-11
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - create a meshgrid with an interesting mathematical surface
np.random.seed(42)
x = np.linspace(-3, 3, 80)
y = np.linspace(-3, 3, 80)
X, Y = np.meshgrid(x, y)

# Create a surface with multiple Gaussian peaks and a saddle point
# This demonstrates various features: peaks, valleys, and gradients
Z = (
    1.5 * np.exp(-((X - 1) ** 2 + (Y - 1) ** 2))
    + 1.2 * np.exp(-((X + 1.5) ** 2 + (Y + 1) ** 2) / 1.5)
    - 0.8 * np.exp(-((X + 0.5) ** 2 + (Y - 1.5) ** 2) / 0.8)
    + 0.5 * np.exp(-((X - 1.5) ** 2 + (Y + 1.5) ** 2))
)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Create filled contour plot with sequential colormap
levels = 15
contourf = ax.contourf(X, Y, Z, levels=levels, cmap="viridis")

# Overlay contour lines for level identification
ax.contour(X, Y, Z, levels=levels, colors=INK_SOFT, linewidths=0.8, alpha=0.4)

# Add colorbar
cbar = plt.colorbar(contourf, ax=ax, shrink=0.9, pad=0.02)
cbar.set_label("Surface Value", fontsize=20, color=INK)
cbar.ax.tick_params(labelsize=16, colors=INK_SOFT)

# Style
ax.set_xlabel("X Coordinate", fontsize=20, color=INK)
ax.set_ylabel("Y Coordinate", fontsize=20, color=INK)
ax.set_title("contour-filled · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Set equal aspect ratio for proper visualization
ax.set_aspect("equal", adjustable="box")

# Style spines
for spine in ("top", "right", "left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)
    ax.spines[spine].set_linewidth(0.8)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
