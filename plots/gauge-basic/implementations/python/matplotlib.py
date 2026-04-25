""" anyplot.ai
gauge-basic: Basic Gauge Chart
Library: matplotlib 3.10.9 | Python 3.14.4
Quality: 91/100 | Updated: 2026-04-25
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito zone colors (colorblind-safe red/yellow/green)
ZONE_BAD = "#D55E00"  # vermillion
ZONE_WARN = "#E69F00"  # orange
ZONE_GOOD = "#009E73"  # bluish green (brand)

# Data
value = 72  # Current sales value
min_value = 0
max_value = 100
thresholds = [30, 70]  # Boundaries for bad/warn/good zones

# Geometry: gauge spans from 180° (left) to 0° (right)
angle_range = 180
value_normalized = (value - min_value) / (max_value - min_value)
needle_angle = 180 - value_normalized * angle_range

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Background zone wedges
zone_colors = [ZONE_BAD, ZONE_WARN, ZONE_GOOD]
zone_boundaries = [min_value] + thresholds + [max_value]

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

# Inner cutout to clean the dial center (matches page background)
inner_circle = mpatches.Wedge(center=(0, 0), r=0.65, theta1=0, theta2=180, facecolor=PAGE_BG, edgecolor="none")
ax.add_patch(inner_circle)

# Tick marks: major (with labels) and minor (between)
major_ticks = [0, 25, 50, 75, 100]
minor_ticks = [t for t in range(0, 101, 5) if t not in major_ticks]

for tick in minor_ticks:
    tick_norm = (tick - min_value) / (max_value - min_value)
    tick_angle = 180 - tick_norm * angle_range
    tick_rad = np.radians(tick_angle)
    inner_r, outer_r = 1.02, 1.05
    ax.plot(
        [inner_r * np.cos(tick_rad), outer_r * np.cos(tick_rad)],
        [inner_r * np.sin(tick_rad), outer_r * np.sin(tick_rad)],
        color=INK_SOFT,
        linewidth=1.5,
    )

for tick in major_ticks:
    tick_norm = (tick - min_value) / (max_value - min_value)
    tick_angle = 180 - tick_norm * angle_range
    tick_rad = np.radians(tick_angle)
    inner_r, outer_r = 1.02, 1.09
    ax.plot(
        [inner_r * np.cos(tick_rad), outer_r * np.cos(tick_rad)],
        [inner_r * np.sin(tick_rad), outer_r * np.sin(tick_rad)],
        color=INK,
        linewidth=3,
    )
    label_r = 1.19
    ax.text(
        label_r * np.cos(tick_rad),
        label_r * np.sin(tick_rad),
        str(tick),
        ha="center",
        va="center",
        fontsize=18,
        fontweight="bold",
        color=INK_SOFT,
    )

# Needle
needle_rad = np.radians(needle_angle)
needle_length = 0.78
needle_x = needle_length * np.cos(needle_rad)
needle_y = needle_length * np.sin(needle_rad)
ax.plot([0, needle_x], [0, needle_y], color=INK, linewidth=6, solid_capstyle="round", zorder=9)

# Center cap (two-tone for definition)
ax.add_patch(plt.Circle((0, 0), 0.09, facecolor=INK, edgecolor="none", zorder=10))
ax.add_patch(plt.Circle((0, 0), 0.035, facecolor=PAGE_BG, edgecolor="none", zorder=11))

# Value label and context
ax.text(0, -0.25, f"{value}", ha="center", va="center", fontsize=56, fontweight="bold", color=ZONE_GOOD)
ax.text(0, -0.47, "Current Sales", ha="center", va="center", fontsize=20, color=INK_MUTED)

# Title
ax.set_title("gauge-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=20)

# Frame
ax.set_aspect("equal")
ax.set_xlim(-1.5, 1.5)
ax.set_ylim(-0.7, 1.5)
ax.axis("off")

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
