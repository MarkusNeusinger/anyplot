""" anyplot.ai
ternary-basic: Basic Ternary Plot
Library: matplotlib 3.11.1 | Python 3.13.14
Quality: 84/100 | Updated: 2026-08-04
"""

import os
import sys


if sys.path and (sys.path[0] == "" or sys.path[0].endswith("/python")):
    sys.path.pop(0)

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data - Soil composition samples (sand, silt, clay summing to 100%)
np.random.seed(42)
n_points = 60

# Generate compositions with better edge/corner coverage using Dirichlet
# Lower alpha values concentrate points at edges; higher values favor center
# Use alpha=1 for more uniform distribution across the simplex
raw = np.random.dirichlet([1, 1, 1], n_points) * 100
sand = raw[:, 0]
silt = raw[:, 1]
clay = raw[:, 2]

# Convert ternary coordinates to Cartesian (equilateral triangle)
# Triangle: Sand at top (0.5, sqrt(3)/2), Silt at bottom-left (0, 0), Clay at bottom-right (1, 0)
sqrt3_2 = np.sqrt(3) / 2
total = sand + silt + clay
x_points = 0.5 * (2 * clay + sand) / total
y_points = sqrt3_2 * sand / total


def to_xy(a_sand, b_silt, c_clay):
    t = a_sand + b_silt + c_clay
    return 0.5 * (2 * c_clay + a_sand) / t, sqrt3_2 * a_sand / t


# USDA-style "Loam" classification zone (sand 23-52%, silt 28-50%, clay 7-27%)
loam_vertices = [(23, 50, 27), (45, 28, 27), (52, 28, 20), (52, 41, 7), (43, 50, 7)]
loam_xy = [to_xy(*v) for v in loam_vertices]
loam_cx = sum(p[0] for p in loam_xy) / len(loam_xy)
loam_cy = sum(p[1] for p in loam_xy) / len(loam_xy)

# Create figure (square format for triangle) — 6x6in @ dpi=400 -> exactly 2400x2400px
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Draw triangle outline
triangle_x = [0.5, 0, 1, 0.5]
triangle_y = [sqrt3_2, 0, 0, sqrt3_2]
ax.plot(triangle_x, triangle_y, color=INK_SOFT, linewidth=1.5)

# Draw grid lines at 20% intervals
grid_levels = [0.2, 0.4, 0.6, 0.8]
for level in grid_levels:
    # Lines parallel to bottom edge (constant sand)
    a_val = level
    x1 = 0.5 * (2 * (1 - a_val) + a_val)
    y1 = sqrt3_2 * a_val
    x2 = 0.5 * (2 * 0 + a_val)
    y2 = sqrt3_2 * a_val
    ax.plot([x1, x2], [y1, y2], color=INK, alpha=0.15, linewidth=0.8, linestyle="--")

    # Lines parallel to right edge (constant silt)
    b_val = level
    x1 = 0.5 * (2 * (1 - b_val) + 0)
    y1 = sqrt3_2 * 0
    x2 = 0.5 * (2 * 0 + (1 - b_val))
    y2 = sqrt3_2 * (1 - b_val)
    ax.plot([x1, x2], [y1, y2], color=INK, alpha=0.15, linewidth=0.8, linestyle="--")

    # Lines parallel to left edge (constant clay)
    c_val = level
    x1 = 0.5 * (2 * c_val + 0)
    y1 = sqrt3_2 * 0
    x2 = 0.5 * (2 * c_val + (1 - c_val))
    y2 = sqrt3_2 * (1 - c_val)
    ax.plot([x1, x2], [y1, y2], color=INK, alpha=0.15, linewidth=0.8, linestyle="--")

# Add tick labels at 20% intervals along each edge
tick_fontsize = 10
for level in [0, 20, 40, 60, 80, 100]:
    frac = level / 100

    # Sand axis (A) - along left edge from bottom to top
    x_tick = 0.5 * (2 * 0 + frac)
    y_tick = sqrt3_2 * frac
    ax.text(x_tick - 0.06, y_tick, f"{level}", fontsize=tick_fontsize, ha="right", va="center", color=INK_SOFT)

    # Silt axis (B) - along bottom edge from right to left
    x_tick = 0.5 * (2 * (1 - frac) + 0)
    y_tick = 0
    ax.text(x_tick, y_tick - 0.05, f"{level}", fontsize=tick_fontsize, ha="center", va="top", color=INK_SOFT)

    # Clay axis (C) - along right edge from top to bottom
    x_tick = 0.5 * (2 * frac + (1 - frac))
    y_tick = sqrt3_2 * (1 - frac)
    ax.text(x_tick + 0.06, y_tick, f"{level}", fontsize=tick_fontsize, ha="left", va="center", color=INK_SOFT)

# Highlight the "Loam" soil-classification zone with a filled Polygon patch
loam_patch = Polygon(
    loam_xy, closed=True, facecolor="#BD8233", alpha=0.18, edgecolor="#BD8233", linewidth=1.0, linestyle=":", zorder=2
)
ax.add_patch(loam_patch)
ax.text(
    loam_cx,
    loam_cy,
    "Loam",
    fontsize=11,
    ha="center",
    va="center",
    fontstyle="italic",
    color=INK_SOFT,
    alpha=0.9,
    zorder=3,
)

# Plot data points
ax.scatter(x_points, y_points, s=130, color=BRAND, alpha=0.75, edgecolors=PAGE_BG, linewidth=0.8, zorder=5)

# Add vertex labels with component names
label_fontsize = 16
ax.text(
    0.5, sqrt3_2 + 0.12, "Sand (%)", fontsize=label_fontsize, ha="center", va="bottom", fontweight="bold", color=INK
)
ax.text(-0.1, -0.1, "Silt (%)", fontsize=label_fontsize, ha="right", va="top", fontweight="bold", color=INK)
ax.text(1.1, -0.1, "Clay (%)", fontsize=label_fontsize, ha="left", va="top", fontweight="bold", color=INK)

# Title
ax.set_title("ternary-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=14)

# Clean up axes
ax.set_aspect("equal")
ax.axis("off")

# Adjust limits to prevent clipping
ax.set_xlim(-0.28, 1.28)
ax.set_ylim(-0.22, 1.15)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
