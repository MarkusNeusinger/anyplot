""" anyplot.ai
wireframe-3d-basic: Basic 3D Wireframe Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-06
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - ripple function z = sin(sqrt(x^2 + y^2))
np.random.seed(42)
x = np.linspace(-6, 6, 40)
y = np.linspace(-6, 6, 40)
X, Y = np.meshgrid(x, y)
R = np.sqrt(X**2 + Y**2)
Z = np.sin(R)

# Create 3D plot
fig = plt.figure(figsize=(16, 9), facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="3d")

# Plot wireframe
ax.plot_wireframe(X, Y, Z, color=BRAND, linewidth=2.5, alpha=0.85)

# Set viewing angle (elevation 30, azimuth 45 as per spec)
ax.view_init(elev=30, azim=45)

# Labels and styling
ax.set_xlabel("Distance from Center (X)", fontsize=20, labelpad=15, color=INK)
ax.set_ylabel("Distance from Center (Y)", fontsize=20, labelpad=15, color=INK)
ax.set_zlabel("Amplitude (Z)", fontsize=20, labelpad=15, color=INK)
ax.set_title("wireframe-3d-basic · matplotlib · anyplot.ai", fontsize=24, pad=20, color=INK)

# Tick parameters
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.tick_params(axis="z", labelsize=16, colors=INK_SOFT)

# Theme-adaptive panes and grid
ax.xaxis.pane.set_facecolor(PAGE_BG)
ax.yaxis.pane.set_facecolor(PAGE_BG)
ax.zaxis.pane.set_facecolor(PAGE_BG)
ax.xaxis.pane.set_edgecolor(INK_SOFT)
ax.yaxis.pane.set_edgecolor(INK_SOFT)
ax.zaxis.pane.set_edgecolor(INK_SOFT)
ax.grid(True, alpha=0.15, linestyle="-", color=INK_SOFT, linewidth=0.8)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
