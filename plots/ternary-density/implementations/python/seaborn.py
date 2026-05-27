""" anyplot.ai
ternary-density: Ternary Density Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-19
"""

import os

import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.colors import Normalize
from matplotlib.patches import Polygon


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
ACCENT = "#4467A3"  # Okabe-Ito blue — structural elements

sns.set_theme(style="ticks", rc={"figure.facecolor": PAGE_BG, "axes.facecolor": PAGE_BG, "text.color": INK})

# Data - Soil composition samples (sand/silt/clay percentages)
np.random.seed(42)

# Cluster 1: Sandy soils (high sand content)
n1 = 200
sand1 = np.random.beta(5, 2, n1) * 70 + 25
silt1 = np.random.beta(2, 3, n1) * (100 - sand1) * 0.6
clay1 = 100 - sand1 - silt1

# Cluster 2: Silty soils (high silt content)
n2 = 150
silt2 = np.random.beta(5, 2, n2) * 60 + 30
sand2 = np.random.beta(2, 3, n2) * (100 - silt2) * 0.5
clay2 = 100 - sand2 - silt2

# Cluster 3: Clay-rich soils
n3 = 150
clay3 = np.random.beta(4, 2, n3) * 50 + 30
sand3 = np.random.beta(2, 3, n3) * (100 - clay3) * 0.4
silt3 = 100 - clay3 - sand3

sand = np.concatenate([sand1, sand2, sand3])
silt = np.concatenate([silt1, silt2, silt3])
clay = np.concatenate([clay1, clay2, clay3])

# Transform ternary to Cartesian: Sand → bottom-left, Silt → bottom-right, Clay → top
total = sand + silt + clay
sand_norm = sand / total
silt_norm = silt / total
clay_norm = clay / total
x = 0.5 * (2 * silt_norm + clay_norm)
y = (np.sqrt(3) / 2) * clay_norm

sqrt3_2 = np.sqrt(3) / 2
vertices = np.array([[0, 0], [1, 0], [0.5, sqrt3_2]])

# Plot
fig, ax = plt.subplots(figsize=(12, 12), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

triangle_clip = Polygon(vertices, transform=ax.transData)

# Grid lines at 10% intervals (all three ternary families)
for i in range(1, 10):
    frac = i / 10
    gkw = {"color": INK_SOFT, "alpha": 0.20, "linewidth": 0.8, "zorder": 1}
    # Constant clay (horizontal, parallel to base)
    ax.plot([0.5 * frac, 1 - 0.5 * frac], [sqrt3_2 * frac, sqrt3_2 * frac], **gkw)
    # Constant silt (parallel to Sand-Clay left edge, slope +√3)
    ax.plot([frac, 0.5 * (1 + frac)], [0, sqrt3_2 * (1 - frac)], **gkw)
    # Constant sand (parallel to Silt-Clay right edge, slope -√3)
    ax.plot([1 - frac, 0.5 * (1 - frac)], [0, sqrt3_2 * (1 - frac)], **gkw)

# KDE density fill
sns.kdeplot(x=x, y=y, fill=True, cmap="viridis", levels=20, alpha=0.85, ax=ax, thresh=0.02, zorder=5)

for collection in ax.collections:
    collection.set_clip_path(triangle_clip)

# KDE contour lines — thicker for visibility at full resolution
sns.kdeplot(x=x, y=y, levels=10, color=ACCENT, linewidths=3.0, ax=ax, zorder=6)

for collection in ax.collections:
    collection.set_clip_path(triangle_clip)

# Triangle boundary
ax.add_patch(Polygon(vertices, fill=False, edgecolor=ACCENT, linewidth=4, zorder=15))

# Colorbar showing relative density scale
sm = cm.ScalarMappable(cmap="viridis", norm=Normalize(vmin=0, vmax=1))
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, fraction=0.025, pad=0.04, aspect=20, shrink=0.55)
cbar.set_label("Relative Density", fontsize=18, labelpad=12)
cbar.ax.yaxis.label.set_color(INK)
cbar.set_ticks([0, 0.5, 1.0])
cbar.ax.set_yticklabels(["Low", "Medium", "High"])
for lbl in cbar.ax.get_yticklabels():
    lbl.set_color(INK_SOFT)
    lbl.set_fontsize(16)
cbar.ax.tick_params(colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Vertex labels (component names + unit)
ax.text(0, -0.08, "Sand (%)", ha="center", va="top", fontsize=22, fontweight="bold", color=INK)
ax.text(1, -0.08, "Silt (%)", ha="center", va="top", fontsize=22, fontweight="bold", color=INK)
ax.text(0.5, sqrt3_2 + 0.08, "Clay (%)", ha="center", va="bottom", fontsize=22, fontweight="bold", color=INK)

# Percentage tick labels along each edge
for i in [2, 4, 6, 8]:
    frac = i / 10
    ax.text(frac, -0.04, f"{int(frac * 100)}", ha="center", va="top", fontsize=16, color=INK_SOFT)
    ax.text(
        0.5 * frac - 0.04, sqrt3_2 * frac, f"{int(frac * 100)}", ha="right", va="center", fontsize=16, color=INK_SOFT
    )
    ax.text(
        1 - 0.5 * frac + 0.04, sqrt3_2 * frac, f"{int(frac * 100)}", ha="left", va="center", fontsize=16, color=INK_SOFT
    )

# Cluster annotations — label each density peak for data storytelling
ann_kw = {
    "fontsize": 15,
    "fontweight": "bold",
    "color": INK,
    "bbox": {"boxstyle": "round,pad=0.3", "facecolor": PAGE_BG, "edgecolor": INK_SOFT, "alpha": 0.75},
}
ax.text(0.13, 0.04, "Sandy\nsoils", ha="center", va="center", **ann_kw)
ax.text(0.80, 0.11, "Silty\nsoils", ha="center", va="center", **ann_kw)
ax.text(0.53, 0.50, "Clay-rich\nsoils", ha="center", va="center", **ann_kw)

# Style
ax.set_title(
    "Soil Composition · ternary-density · python · seaborn · anyplot.ai",
    fontsize=24,
    fontweight="medium",
    color=INK,
    pad=25,
)
ax.set_xlim(-0.15, 1.15)
ax.set_ylim(-0.15, 1.05)
ax.set_aspect("equal")
ax.axis("off")

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
