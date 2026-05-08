"""anyplot.ai
histogram-2d: 2D Histogram Heatmap
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-05-08
"""

import os

import matplotlib.pyplot as plt
import numpy as np


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - bivariate normal with positive correlation
np.random.seed(42)
n_points = 5000
mean = [0, 0]
cov = [[1, 0.7], [0.7, 1]]
data = np.random.multivariate_normal(mean, cov, n_points)
x = data[:, 0]
y = data[:, 1]

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

h = ax.hist2d(x, y, bins=40, cmap="viridis", cmin=1)

# Colorbar
cbar = fig.colorbar(h[3], ax=ax, pad=0.02)
cbar.set_label("Frequency", fontsize=20, color=INK)
cbar.ax.tick_params(axis="y", labelsize=16, colors=INK_SOFT)

# Labels and styling
ax.set_xlabel("Feature X", fontsize=20, color=INK)
ax.set_ylabel("Feature Y", fontsize=20, color=INK)
ax.set_title("histogram-2d · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
