""" anyplot.ai
gauge-basic: Basic Gauge Chart
Library: matplotlib 3.11.0 | Python 3.13.14
Quality: 91/100 | Updated: 2026-06-30
"""

import os
import sys


# Script named matplotlib.py shadows the installed package when run from its own directory.
# Removing the first sys.path entry (the script's directory) before any matplotlib import
# restores the normal package lookup — the venv site-packages takes over.
sys.path.pop(0)

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint semantic anchors (red / amber / green traffic-light)
ZONE_BAD = "#AE3030"  # matte red — semantic bad
ZONE_WARN = "#DDCC77"  # amber — semantic warning
ZONE_GOOD = "#009E73"  # brand green — semantic good

# Data
value = 72
min_value = 0
max_value = 100
thresholds = [30, 70]

# Gauge geometry: 180° arc (left=0, right=100)
angle_range = 180
value_normalized = (value - min_value) / (max_value - min_value)
needle_angle = 180 - value_normalized * angle_range

# Plot — square canvas (2400×2400) for optimal gauge proportions
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Color zones with labels
zone_colors = [ZONE_BAD, ZONE_WARN, ZONE_GOOD]
zone_boundaries = [min_value] + thresholds + [max_value]
zone_labels = ["Poor", "Fair", "Good"]

for i in range(len(zone_colors)):
    start_norm = (zone_boundaries[i] - min_value) / (max_value - min_value)
    end_norm = (zone_boundaries[i + 1] - min_value) / (max_value - min_value)
    theta1 = 180 - end_norm * angle_range
    theta2 = 180 - start_norm * angle_range
    wedge = mpatches.Wedge(
        center=(0, 0),
        r=1.0,
        theta1=theta1,
        theta2=theta2,
        width=0.3,
        facecolor=zone_colors[i],
        edgecolor=PAGE_BG,
        linewidth=2,
    )
    ax.add_patch(wedge)

    # Zone label at arc midpoint (tangential orientation)
    mid_norm = (start_norm + end_norm) / 2
    mid_angle = 180 - mid_norm * angle_range
    mid_rad = np.radians(mid_angle)
    ax.text(
        0.85 * np.cos(mid_rad),
        0.85 * np.sin(mid_rad),
        zone_labels[i],
        ha="center",
        va="center",
        fontsize=8,
        fontweight="bold",
        color=PAGE_BG,
        rotation=mid_angle - 90,
    )

# Inner fill (matches page background, cleans dial center)
ax.add_patch(mpatches.Wedge(center=(0, 0), r=0.65, theta1=0, theta2=180, facecolor=PAGE_BG, edgecolor="none"))

# Tick marks: minor and major
major_ticks = [0, 25, 50, 75, 100]
minor_ticks = [t for t in range(0, 101, 5) if t not in major_ticks]

for tick in minor_ticks:
    tick_norm = (tick - min_value) / (max_value - min_value)
    tick_angle = 180 - tick_norm * angle_range
    tick_rad = np.radians(tick_angle)
    ax.plot(
        [1.02 * np.cos(tick_rad), 1.05 * np.cos(tick_rad)],
        [1.02 * np.sin(tick_rad), 1.05 * np.sin(tick_rad)],
        color=INK_SOFT,
        linewidth=1.5,
    )

for tick in major_ticks:
    tick_norm = (tick - min_value) / (max_value - min_value)
    tick_angle = 180 - tick_norm * angle_range
    tick_rad = np.radians(tick_angle)
    ax.plot(
        [1.02 * np.cos(tick_rad), 1.09 * np.cos(tick_rad)],
        [1.02 * np.sin(tick_rad), 1.09 * np.sin(tick_rad)],
        color=INK,
        linewidth=3,
    )
    ax.text(
        1.19 * np.cos(tick_rad),
        1.19 * np.sin(tick_rad),
        str(tick),
        ha="center",
        va="center",
        fontsize=16,
        fontweight="bold",
        color=INK_SOFT,
    )

# Needle
needle_rad = np.radians(needle_angle)
ax.plot(
    [0, 0.78 * np.cos(needle_rad)],
    [0, 0.78 * np.sin(needle_rad)],
    color=INK,
    linewidth=5,
    solid_capstyle="round",
    zorder=9,
)

# Center cap (two-tone for definition)
ax.add_patch(plt.Circle((0, 0), 0.09, facecolor=INK, edgecolor="none", zorder=10))
ax.add_patch(plt.Circle((0, 0), 0.035, facecolor=PAGE_BG, edgecolor="none", zorder=11))

# Value label and context
ax.text(0, -0.22, f"{value}", ha="center", va="center", fontsize=56, fontweight="bold", color=ZONE_GOOD)
ax.text(0, -0.46, "Current Sales", ha="center", va="center", fontsize=18, color=INK_MUTED)

# Title
title = "gauge-basic · python · matplotlib · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK, pad=20)

# Frame — square axes to match square canvas
ax.set_aspect("equal")
ax.set_xlim(-1.5, 1.5)
ax.set_ylim(-1.15, 1.85)
ax.axis("off")

fig.subplots_adjust(left=0.03, right=0.97, top=0.88, bottom=0.05)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
