""" anyplot.ai
contour-basic: Basic Contour Plot
Library: matplotlib 3.11.0 | Python 3.13.14
Quality: 88/100 | Updated: 2026-06-25
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint sequential colormap for single-polarity elevation data
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

# Data — simulated topographic elevation of a 20 × 10 km mountain range
# Northeast summit ~1220 m; southwest summit ~820 m — visible height contrast
x = np.linspace(0, 20, 120)
y = np.linspace(0, 10, 60)
X, Y = np.meshgrid(x, y)

elevation = (
    900 * np.exp(-((X - 16) ** 2 + (Y - 7.5) ** 2) / 5.0)
    + 500 * np.exp(-((X - 5) ** 2 + (Y - 3) ** 2) / 4.0)
    - 100 * np.exp(-((X - 10) ** 2 + (Y - 5) ** 2) / 10.0)
    + 320
)

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

levels = np.arange(200, 1301, 50)
major_levels = np.arange(400, 1301, 200)

filled = ax.contourf(X, Y, elevation, levels=levels, cmap=imprint_seq)
ax.contour(X, Y, elevation, levels=levels, colors=INK, linewidths=0.4, alpha=0.30)
major = ax.contour(X, Y, elevation, levels=major_levels, colors=INK, linewidths=0.8, alpha=0.65)
ax.clabel(major, inline=True, fontsize=7, fmt="%d m", inline_spacing=5)

# Summit markers — peak triangles with labeled elevations for data storytelling
ax.plot(16, 7.5, "^", color=INK, markersize=4.5, markeredgecolor=PAGE_BG, markeredgewidth=0.5, zorder=5)
ax.annotate(
    "NE Summit\n~1,220 m",
    xy=(16, 7.5),
    xytext=(13.3, 5.2),
    fontsize=6.5,
    color=INK,
    ha="center",
    va="center",
    arrowprops={"arrowstyle": "->", "color": INK_SOFT, "lw": 0.6, "mutation_scale": 6, "shrinkA": 0, "shrinkB": 5},
    bbox={"facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.88, "boxstyle": "round,pad=0.3", "lw": 0.5},
    zorder=6,
)

ax.plot(5, 3, "^", color=INK, markersize=4.5, markeredgecolor=PAGE_BG, markeredgewidth=0.5, zorder=5)
ax.annotate(
    "SW Summit\n~815 m",
    xy=(5, 3),
    xytext=(7.8, 5.8),
    fontsize=6.5,
    color=INK,
    ha="center",
    va="center",
    arrowprops={"arrowstyle": "->", "color": INK_SOFT, "lw": 0.6, "mutation_scale": 6, "shrinkA": 0, "shrinkB": 5},
    bbox={"facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.88, "boxstyle": "round,pad=0.3", "lw": 0.5},
    zorder=6,
)

# Colorbar
cbar = fig.colorbar(filled, ax=ax, shrink=0.88, aspect=30, pad=0.025)
cbar.set_label("Elevation (m)", fontsize=10, color=INK)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)
cbar.outline.set_linewidth(0.5)

# Style
ax.set_xlabel("Distance East (km)", fontsize=10, color=INK)
ax.set_ylabel("Distance North (km)", fontsize=10, color=INK)
ax.set_title("contour-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=10)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.set_ylim(-0.3, 10.3)
for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

fig.subplots_adjust(left=0.07, right=0.84, top=0.93, bottom=0.11)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
