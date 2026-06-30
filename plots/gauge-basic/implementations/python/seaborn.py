""" anyplot.ai
gauge-basic: Basic Gauge Chart
Library: seaborn 0.13.2 | Python 3.13.14
Quality: 87/100 | Updated: 2026-06-30
"""

import os
import sys


# matplotlib.py in this directory is a sibling implementation — remove own dir from sys.path
# so it does not shadow the installed matplotlib package
_own_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if not p or os.path.abspath(p) != _own_dir]

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.patches import Circle, Wedge


# Imprint palette chrome — theme-adaptive
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint semantic anchors for CPU health zones (low usage = good, high = danger)
ZONE_NORMAL = "#009E73"  # Imprint green — healthy CPU load
ZONE_MODERATE = "#DDCC77"  # Imprint amber — elevated load, caution
ZONE_HIGH = "#AE3030"  # Imprint red — high CPU, intervention needed

# Data — production server CPU utilization
value = 83
min_value = 0
max_value = 100
thresholds = [40, 80]  # 0–40: Normal, 40–80: Moderate, 80–100: High

# Gauge geometry (unit-square axis coordinates)
center = (0.5, 0.45)
radius = 0.38
width = 0.15
start_angle = 180
end_angle = 0
angle_range = start_angle - end_angle
value_range = max_value - min_value

zone_boundaries = [min_value] + thresholds + [max_value]
zone_names = ["Normal", "Moderate", "High"]
zone_colors = [ZONE_NORMAL, ZONE_MODERATE, ZONE_HIGH]

# Plot — seaborn theme with Imprint chrome
sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Arc zones — Wedge patches for each CPU health band
for i in range(len(zone_boundaries) - 1):
    z_start = start_angle - (zone_boundaries[i] - min_value) / value_range * angle_range
    z_end = start_angle - (zone_boundaries[i + 1] - min_value) / value_range * angle_range
    ax.add_patch(
        Wedge(
            center=center,
            r=radius + width / 2,
            theta1=z_end,
            theta2=z_start,
            width=width,
            facecolor=zone_colors[i],
            edgecolor="none",
            linewidth=0,
            zorder=2,
        )
    )

# Zone boundary dividers — thin radial cuts in INK_SOFT
for threshold in thresholds:
    angle = start_angle - (threshold - min_value) / value_range * angle_range
    rad = np.radians(angle)
    rs = (radius - width / 2, radius + width / 2)
    ax.plot(
        [center[0] + r * np.cos(rad) for r in rs],
        [center[1] + r * np.sin(rad) for r in rs],
        color=INK_SOFT,
        linewidth=2,
        zorder=3,
        solid_capstyle="butt",
    )

# Needle — points to current CPU utilization
needle_angle = start_angle - (value - min_value) / value_range * angle_range
needle_rad = np.radians(needle_angle)
needle_length = radius + width / 2 - 0.012
needle_tip_x = center[0] + needle_length * np.cos(needle_rad)
needle_tip_y = center[1] + needle_length * np.sin(needle_rad)
ax.plot([center[0], needle_tip_x], [center[1], needle_tip_y], color=INK, linewidth=3, zorder=12, solid_capstyle="round")

# Hub — page-bg ring + ink disc for crisp look in both themes
ax.add_patch(Circle(center, radius=0.045, facecolor=PAGE_BG, edgecolor="none", zorder=13))
ax.add_patch(Circle(center, radius=0.035, facecolor=INK, edgecolor="none", zorder=14))

# Value display — bold reading centered below gauge
ax.text(center[0], center[1] - 0.19, f"{value}%", ha="center", va="center", fontsize=32, fontweight="bold", color=INK)

# Context label
ax.text(center[0], center[1] - 0.29, "CPU Utilization", ha="center", va="center", fontsize=9, color=INK_MUTED)

# Min / max scale endpoints
for vlabel, x_off in [(min_value, -1), (max_value, 1)]:
    ax.text(
        center[0] + x_off * radius, center[1] - 0.055, f"{vlabel}", ha="center", va="top", fontsize=10, color=INK_SOFT
    )

# Zone labels on arc — white text with PAGE_BG stroke (theme-adaptive halo)
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
    txt = ax.text(lx, ly, label, ha="center", va="center", fontsize=11, color="white", fontweight="bold", zorder=5)
    txt.set_path_effects([pe.withStroke(linewidth=2, foreground=PAGE_BG)])

# Title
ax.set_title("gauge-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", pad=16, color=INK)

# Canvas — pure coordinate space, no axes chrome
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_aspect("equal")
ax.axis("off")

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
