""" anyplot.ai
ternary-density: Ternary Density Plot
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-22
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Polygon
from scipy.stats import gaussian_kde


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: density runs along the single-polarity Imprint ramp (green to blue)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]])

# Constants
SQ3H = np.sqrt(3) / 2  # height of the unit equilateral triangle
GRID_LEVELS = [0.2, 0.4, 0.6, 0.8]  # ternary grid lines at 20/40/60/80 %

# Columns: set these to your table's column names
SAND = "Sand (%)"  # role: component_a
SILT = "Silt (%)"  # role: component_b
CLAY = "Clay (%)"  # role: component_c

# Data: replace this block with your own table, for example df = pd.read_csv("sediment.csv")
# Sediment composition (sand/silt/clay) with three cluster types, each row sums to 100
rng = np.random.default_rng(42)

n1 = 300
sand1 = rng.beta(5, 2, n1) * 60 + 35
silt1 = rng.beta(2, 3, n1) * (100 - sand1) * 0.6
clay1 = 100 - sand1 - silt1

n2 = 250
silt2 = rng.beta(5, 2, n2) * 50 + 40
sand2 = rng.beta(2, 4, n2) * (100 - silt2) * 0.5
clay2 = 100 - sand2 - silt2

n3 = 250
clay3 = rng.beta(4, 2, n3) * 45 + 40
sand3 = rng.beta(2, 5, n3) * (100 - clay3) * 0.4
silt3 = 100 - sand3 - clay3

df = pd.DataFrame(
    {
        SAND: np.clip(np.concatenate([sand1, sand2, sand3]), 0, 100),
        SILT: np.clip(np.concatenate([silt1, silt2, silt3]), 0, 100),
        CLAY: np.clip(np.concatenate([clay1, clay2, clay3]), 0, 100),
    }
)

# Plot: reads only df and the constants above
sand_name, silt_name, clay_name = (c.split(" (")[0] for c in (SAND, SILT, CLAY))
shares = df[[SAND, SILT, CLAY]].dropna().to_numpy()
shares = shares / shares.sum(axis=1, keepdims=True)

# Ternary → Cartesian: Sand vertex (0,0), Silt vertex (1,0), Clay vertex (0.5, SQ3H)
x_data = shares[:, 1] + 0.5 * shares[:, 2]
y_data = SQ3H * shares[:, 2]

# KDE on a grid, masked to the triangle
grid_res = 300
Xi, Yi = np.meshgrid(np.linspace(0, 1, grid_res), np.linspace(0, SQ3H, grid_res))
Ci = Yi / SQ3H
Bi = Xi - 0.5 * Ci
Ai = 1 - Bi - Ci
inside = (Ai >= 0) & (Bi >= 0) & (Ci >= 0)

kde = gaussian_kde(np.vstack([x_data, y_data]), bw_method="silverman")
Z = kde(np.vstack([Xi.ravel(), Yi.ravel()])).reshape(Xi.shape)
Z = np.where(inside, Z, np.nan)

fig = plt.figure(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax = fig.add_axes([0.0, 0.0, 0.84, 0.92])
ax.set_facecolor(PAGE_BG)

# Density surface and contour lines
density_plot = ax.contourf(Xi, Yi, Z, levels=24, cmap=imprint_seq, zorder=2)
ax.contour(Xi, Yi, Z, levels=6, colors="white", linewidths=0.9, alpha=0.7, zorder=3)

# Triangle boundary
ax.add_patch(Polygon([[0, 0], [1, 0], [0.5, SQ3H]], fill=False, edgecolor=INK_SOFT, linewidth=1.5, zorder=10))

# Grid lines — three families, drawn over the density with transparency so they stay visible
grid_style = {"color": INK_SOFT, "linewidth": 0.6, "alpha": 0.5, "linestyle": "--", "zorder": 4}
for lv in GRID_LEVELS:
    ax.plot([0.5 * lv, 1 - 0.5 * lv], [SQ3H * lv, SQ3H * lv], **grid_style)  # constant Clay
    ax.plot([lv, 0.5 + 0.5 * lv], [0, SQ3H * (1 - lv)], **grid_style)  # constant Silt
    ax.plot([0.5 * (1 - lv), 1 - lv], [SQ3H * (1 - lv), 0], **grid_style)  # constant Sand

# Colorbar, centered vertically on the triangle
cax = fig.add_axes([0.86, 0.22, 0.025, 0.5])
cbar = fig.colorbar(density_plot, cax=cax)
cbar.set_label("Density", fontsize=10, color=INK)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Vertex labels
ax.text(0, -0.06, sand_name, fontsize=12, ha="center", va="top", fontweight="bold", color=INK)
ax.text(1, -0.06, silt_name, fontsize=12, ha="center", va="top", fontweight="bold", color=INK)
ax.text(0.5, SQ3H + 0.04, clay_name, fontsize=12, ha="center", va="bottom", fontweight="bold", color=INK)

# Edge tick labels — each edge shows a different component's scale
for lv in GRID_LEVELS:
    pct = f"{round(lv * 100)}"
    ax.text(1 - lv, -0.025, pct, fontsize=8, ha="center", va="top", color=INK_MUTED)  # Sand, bottom edge
    ax.text(0.5 * lv - 0.03, SQ3H * lv, pct, fontsize=8, ha="right", va="center", color=INK_MUTED)  # Clay, left edge
    ax.text(0.5 + 0.5 * lv + 0.03, SQ3H * (1 - lv), pct, fontsize=8, ha="left", va="center", color=INK_MUTED)  # Silt

# Axis labels outside each edge
ax.text(0.5, -0.12, SAND, fontsize=10, ha="center", va="top", color=INK_SOFT, style="italic")
ax.text(0.15, SQ3H * 0.55, CLAY, fontsize=10, ha="center", va="center", color=INK_SOFT, style="italic", rotation=60)
ax.text(0.85, SQ3H * 0.55, SILT, fontsize=10, ha="center", va="center", color=INK_SOFT, style="italic", rotation=-60)

# Title
title = "Sediment Composition · ternary-density · python · matplotlib · anyplot.ai"
fig.text(0.5, 0.955, title, fontsize=max(8, round(11 * 67 / len(title))), ha="center", va="center", color=INK)

ax.set_xlim(-0.14, 1.14)
ax.set_ylim(-0.2, SQ3H + 0.08)
ax.set_aspect("equal")
ax.axis("off")

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
