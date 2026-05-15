""" anyplot.ai
bar-3d-categorical: 3D Bar Chart for Categorical Comparison
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 80/100 | Created: 2026-05-15
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Data: retail sales (thousands USD) by product category and region
products = ["Electronics", "Clothing", "Home & Garden", "Sports"]
regions = ["North", "South", "East", "West"]

sales = np.array([[142, 98, 115, 87], [76, 103, 91, 118], [55, 71, 63, 49], [88, 95, 72, 110]])

# Plot
fig = plt.figure(figsize=(16, 9), facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="3d", computed_zorder=False)
fig.subplots_adjust(left=0.0, right=0.85, bottom=0.05, top=0.92)

# Theme-adaptive pane styling
for pane in (ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane):
    pane.fill = False
    pane.set_edgecolor(INK_SOFT)
    pane.set_alpha(0.4)

ax.grid(True, alpha=0.10, linewidth=0.6, color=INK)

norm = plt.Normalize(vmin=sales.min(), vmax=sales.max())
cmap = plt.get_cmap("viridis")

bar_width = 0.55
bar_depth = 0.55
num_products = len(products)
num_regions = len(regions)

for i in range(num_products):
    for j in range(num_regions):
        value = sales[i, j]
        color = cmap(norm(value))
        ax.bar3d(
            i - bar_width / 2, j - bar_depth / 2, 0, bar_width, bar_depth, value, color=color, alpha=0.88, shade=True
        )
        ax.text(i, j, value + 5, f"{value}", ha="center", va="bottom", fontsize=10, color=INK, fontweight="semibold")

# View angle and z-axis headroom for value labels
ax.view_init(elev=28, azim=-48)
ax.set_zlim(0, 165)

# Axis ticks and labels
ax.set_xticks(range(num_products))
ax.set_xticklabels(products, fontsize=13, color=INK_SOFT)
ax.set_yticks(range(num_regions))
ax.set_yticklabels(regions, fontsize=13, color=INK_SOFT)
ax.tick_params(axis="z", labelsize=13, colors=INK_SOFT)

ax.set_xlabel("Product Category", fontsize=15, color=INK, labelpad=16)
ax.set_ylabel("Region", fontsize=15, color=INK, labelpad=16)
ax.set_zlabel("$ thousands", fontsize=14, color=INK_SOFT, labelpad=12)

ax.set_title(
    "Retail Sales by Product & Region  ·  bar-3d-categorical · matplotlib · anyplot.ai",
    fontsize=20,
    fontweight="medium",
    color=INK,
    pad=16,
)

# Colorbar — placed in its own axes to avoid tight_layout conflicts
cbar_ax = fig.add_axes([0.87, 0.15, 0.025, 0.65])
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, cax=cbar_ax)
cbar.set_label("Sales ($ thousands)", fontsize=14, color=INK)
cbar.ax.tick_params(labelsize=12, colors=INK_SOFT)
plt.setp(cbar.ax.yaxis.get_ticklabels(), color=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)
cbar_ax.set_facecolor(PAGE_BG)

plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
