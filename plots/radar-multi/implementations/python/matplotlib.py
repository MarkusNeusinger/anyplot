""" anyplot.ai
radar-multi: Multi-Series Radar Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-07
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

# Imprint palette (first three series, canonical order)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data: product comparison across key attributes — Product B is the overall leader
categories = ["Performance", "Battery Life", "Camera", "Display", "Build Quality", "Value"]
products = {
    "Product A": [85, 70, 90, 88, 75, 65],
    "Product B": [72, 95, 78, 82, 88, 80],
    "Product C": [90, 60, 85, 75, 70, 90],
}
leader_idx = 1  # Product B carries the highest average score — given visual emphasis

# Number of variables
n_categories = len(categories)

# Compute angle for each axis
angles = np.linspace(0, 2 * np.pi, n_categories, endpoint=False).tolist()
angles += angles[:1]  # Close the polygon

# Create figure (square format for radar)
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, subplot_kw={"polar": True}, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Per-series visual weight — the leader draws bolder and on top, guiding the eye
# to the strongest overall performer without adding any text annotation
markers = ["o", "s", "^"]
linewidths = [2.5, 2.5, 2.5]
markersizes = [8, 8, 8]
fill_alphas = [0.18, 0.18, 0.18]
zorders = [1, 1, 1]  # below the default radial-grid/tick-label zorder (~2.5)
linewidths[leader_idx] = 3.5
markersizes[leader_idx] = 12
fill_alphas[leader_idx] = 0.35
zorders[leader_idx] = 1.5

# Plot each product
for idx, (product, values) in enumerate(products.items()):
    values_closed = values + values[:1]  # Close the polygon
    ax.plot(
        angles,
        values_closed,
        marker=markers[idx],
        linestyle="-",
        linewidth=linewidths[idx],
        label=product,
        color=IMPRINT[idx],
        markersize=markersizes[idx],
        markeredgecolor=PAGE_BG,
        markeredgewidth=1,
        zorder=zorders[idx],
    )
    ax.fill(angles, values_closed, alpha=fill_alphas[idx], color=IMPRINT[idx], zorder=zorders[idx])

# Set category labels at each axis, nudged outward and aligned so labels at
# the horizontal axes (0 / pi radians) don't collide with the data markers
ax.set_xticks(angles[:-1])
tick_labels = ax.set_xticklabels(categories, fontsize=15, fontweight="bold", color=INK)
ax.tick_params(axis="x", pad=18)
for label, angle in zip(tick_labels, angles[:-1], strict=True):
    if np.isclose(angle, 0.0):
        label.set_horizontalalignment("left")
    elif np.isclose(angle, np.pi):
        label.set_horizontalalignment("right")

# Set radial grid — labels get an opaque halo so they stay legible where
# polygon fills cross the radial axis
ax.set_ylim(0, 100)
ax.set_yticks([20, 40, 60, 80, 100])
r_tick_labels = ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=13, color=INK_SOFT)
for label in r_tick_labels:
    label.set_bbox({"facecolor": PAGE_BG, "edgecolor": "none", "alpha": 0.9, "pad": 1.5})

# Grid styling
ax.yaxis.grid(True, linestyle="-", alpha=0.15, linewidth=0.8, color=INK_SOFT)
ax.xaxis.grid(True, linestyle="-", alpha=0.15, linewidth=0.8, color=INK_SOFT)

# Title — figure-level (not axes-level) so it stays centered on the full
# canvas regardless of how the legend reshapes the polar axes below
fig.suptitle("radar-multi · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, y=0.97)

# Legend outside the circular grid, vertically centered — leader label
# rendered bold to echo its bolder polygon
leg = ax.legend(loc="center left", bbox_to_anchor=(1.08, 0.5), fontsize=13, framealpha=1.0)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.8)
for idx, text in enumerate(leg.get_texts()):
    text.set_color(INK)
    if idx == leader_idx:
        text.set_fontweight("bold")

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
