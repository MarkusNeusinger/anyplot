""" anyplot.ai
scatter-3d: 3D Scatter Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 93/100 | Created: 2026-05-08
"""

import os

import matplotlib.pyplot as plt
import numpy as np


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data
np.random.seed(42)
n_points = 150
cluster1_x = np.random.normal(-2, 0.8, n_points // 3)
cluster1_y = np.random.normal(2, 0.8, n_points // 3)
cluster1_z = np.random.normal(1, 0.8, n_points // 3)

cluster2_x = np.random.normal(1, 0.8, n_points // 3)
cluster2_y = np.random.normal(-1, 0.8, n_points // 3)
cluster2_z = np.random.normal(3, 0.8, n_points // 3)

cluster3_x = np.random.normal(2, 0.8, n_points - 2 * (n_points // 3))
cluster3_y = np.random.normal(1, 0.8, n_points - 2 * (n_points // 3))
cluster3_z = np.random.normal(-1, 0.8, n_points - 2 * (n_points // 3))

x = np.concatenate([cluster1_x, cluster2_x, cluster3_x])
y = np.concatenate([cluster1_y, cluster2_y, cluster3_y])
z = np.concatenate([cluster1_z, cluster2_z, cluster3_z])

# Plot
fig = plt.figure(figsize=(16, 9), facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="3d")
ax.set_facecolor(PAGE_BG)

ax.scatter(x, y, z, c=BRAND, s=200, alpha=0.7, edgecolors=PAGE_BG, linewidth=0.5)

# Style
ax.set_xlabel("Feature A", fontsize=20, color=INK, labelpad=10)
ax.set_ylabel("Feature B", fontsize=20, color=INK, labelpad=10)
ax.set_zlabel("Feature C", fontsize=20, color=INK, labelpad=10)
ax.set_title("scatter-3d · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=20)

ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.xaxis.pane.set_facecolor(PAGE_BG)
ax.yaxis.pane.set_facecolor(PAGE_BG)
ax.zaxis.pane.set_facecolor(PAGE_BG)
ax.xaxis.pane.set_edgecolor(INK_SOFT)
ax.yaxis.pane.set_edgecolor(INK_SOFT)
ax.zaxis.pane.set_edgecolor(INK_SOFT)

ax.view_init(elev=20, azim=45)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
plt.close()
