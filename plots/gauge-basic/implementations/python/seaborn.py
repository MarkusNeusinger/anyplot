"""anyplot.ai
gauge-basic: Basic Gauge Chart
Library: seaborn 0.13.2 | Python 3.14.4
Quality: 84/100 | Updated: 2026-04-25
"""

import os

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.patches import Circle, Wedge


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito zone palette (semantic gauge mapping: vermillion / orange / brand green)
ZONE_LOW, ZONE_MED, ZONE_HIGH = sns.color_palette(["#D55E00", "#E69F00", "#009E73"])

# Data — sales performance gauge
value = 72
min_value = 0
max_value = 100
thresholds = [30, 70]

# Gauge geometry
center = (0.5, 0.45)
radius = 0.40
width = 0.16
start_angle = 180
end_angle = 0
angle_range = start_angle - end_angle
value_range = max_value - min_value

zone_boundaries = [min_value] + thresholds + [max_value]
zone_names = ["Low", "Medium", "High"]
zone_colors = [ZONE_LOW, ZONE_MED, ZONE_HIGH]

# Plot
sns.set_theme(
    style="white",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "text.color": INK,
        "axes.labelcolor": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
    },
)
fig, ax = plt.subplots(figsize=(12, 12), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Arc — three coloured zones drawn as smooth Wedge patches
for i in range(len(zone_boundaries) - 1):
    z_start_angle = start_angle - (zone_boundaries[i] - min_value) / value_range * angle_range
    z_end_angle = start_angle - (zone_boundaries[i + 1] - min_value) / value_range * angle_range
    ax.add_patch(
        Wedge(
            center=center,
            r=radius + width / 2,
            theta1=z_end_angle,
            theta2=z_start_angle,
            width=width,
            facecolor=zone_colors[i],
            edgecolor="none",
            linewidth=0,
            zorder=2,
        )
    )

# Boundary cuts between zones — short radial line, theme-visible color
for threshold in thresholds:
    boundary_angle = start_angle - (threshold - min_value) / value_range * angle_range
    rad = np.radians(boundary_angle)
    rs = (radius - width / 2, radius + width / 2)
    ax.plot(
        [center[0] + r * np.cos(rad) for r in rs],
        [center[1] + r * np.sin(rad) for r in rs],
        color=INK_SOFT,
        linewidth=3,
        zorder=3,
        solid_capstyle="butt",
    )

# Needle
needle_angle = start_angle - (value - min_value) / value_range * angle_range
needle_rad = np.radians(needle_angle)
needle_length = radius + width / 2 - 0.015
needle_tip_x = center[0] + needle_length * np.cos(needle_rad)
needle_tip_y = center[1] + needle_length * np.sin(needle_rad)
ax.plot([center[0], needle_tip_x], [center[1], needle_tip_y], color=INK, linewidth=6, zorder=12, solid_capstyle="round")

# Hub — outer ring (page bg) + inner disc (ink) for clean contrast in both themes
ax.add_patch(Circle(center, radius=0.045, facecolor=PAGE_BG, edgecolor="none", zorder=13))
ax.add_patch(Circle(center, radius=0.035, facecolor=INK, edgecolor="none", zorder=14))

# Value display
ax.text(center[0], center[1] - 0.20, f"{value}%", ha="center", va="center", fontsize=56, fontweight="bold", color=INK)

# Min / max endpoint labels
for vlabel, x_off in [(min_value, -1), (max_value, 1)]:
    ax.text(
        center[0] + x_off * radius, center[1] - 0.06, f"{vlabel}", ha="center", va="top", fontsize=20, color=INK_SOFT
    )

# Zone labels on the arc — white text with dark stroke for legibility on every zone in both themes
zone_label_centers = [
    (thresholds[0] - min_value) / 2 + min_value,
    (thresholds[0] + thresholds[1]) / 2,
    (thresholds[1] + max_value) / 2,
]
for v_center, label in zip(zone_label_centers, zone_names, strict=True):
    angle = start_angle - (v_center - min_value) / value_range * angle_range
    rad = np.radians(angle)
    lx = center[0] + radius * np.cos(rad)
    ly = center[1] + radius * np.sin(rad)
    txt = ax.text(lx, ly, label, ha="center", va="center", fontsize=22, color="white", fontweight="bold", zorder=5)
    txt.set_path_effects([pe.withStroke(linewidth=3, foreground="#1A1A17")])

# Title
ax.set_title("gauge-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", pad=20, color=INK)

# Axis settings — purely a canvas
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_aspect("equal")
ax.axis("off")

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
