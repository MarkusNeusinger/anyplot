"""anyplot.ai
hexbin-basic: Basic Hexbin Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 88/100 | Created: 2026-05-29
"""

import os
import sys


# Remove the script's own directory from sys.path so it doesn't shadow the installed matplotlib package
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _script_dir]

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import LogFormatterSciNotation


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint sequential colormap — brand green → blue (single-polarity density)
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

# Data — simulated urban sensor readings with three density clusters
np.random.seed(42)
n_points = 10000

downtown_x = np.random.randn(n_points // 2) * 1.5 + 2
downtown_y = np.random.randn(n_points // 2) * 1.5 + 2
industrial_x = np.random.randn(n_points // 3) * 1.0 - 2
industrial_y = np.random.randn(n_points // 3) * 1.0 - 1
suburb_x = np.random.randn(n_points // 6) * 0.8 + 1
suburb_y = np.random.randn(n_points // 6) * 0.8 - 2

longitude = np.concatenate([downtown_x, industrial_x, suburb_x])
latitude = np.concatenate([downtown_y, industrial_y, suburb_y])

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

hb = ax.hexbin(
    longitude,
    latitude,
    gridsize=30,
    cmap=imprint_seq,
    mincnt=1,
    linewidths=0.2,
    edgecolors=PAGE_BG,
    norm=mcolors.LogNorm(),
)

# Colorbar with LogFormatterSciNotation for cleaner log-scale tick labels
cbar = fig.colorbar(hb, ax=ax, shrink=0.85, pad=0.02)
cbar.set_label("Sensor Reading Count", fontsize=10, color=INK)
cbar.ax.yaxis.set_major_formatter(LogFormatterSciNotation())
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
cbar.outline.set_linewidth(0.5)
cbar.outline.set_edgecolor(INK_SOFT)

# Style
ax.set_xlabel("Longitude (km)", fontsize=10, color=INK)
ax.set_ylabel("Latitude (km)", fontsize=10, color=INK)

title = "hexbin-basic · python · matplotlib · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK)

ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["left"].set_linewidth(0.5)
ax.spines["bottom"].set_color(INK_SOFT)
ax.spines["bottom"].set_linewidth(0.5)

# Cluster annotations — label the three density zones to aid data storytelling
_ann_style = {
    "fontsize": 7,
    "color": INK_SOFT,
    "ha": "center",
    "va": "center",
    "bbox": {
        "facecolor": ELEVATED_BG,
        "edgecolor": INK_SOFT,
        "alpha": 0.85,
        "boxstyle": "round,pad=0.3",
        "linewidth": 0.5,
    },
}
ax.text(2, 2, "Downtown", **_ann_style)
ax.text(-2, -1, "Industrial District", **_ann_style)
ax.text(1, -2, "Suburban Area", **_ann_style)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
