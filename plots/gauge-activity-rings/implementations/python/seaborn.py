""" anyplot.ai
gauge-activity-rings: Activity Rings Progress Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 85/100 | Created: 2026-06-14
"""

import os
import sys
from pathlib import Path


# Remove current directory from sys.path to avoid self-import (file is named seaborn.py)
_orig_path = sys.path.copy()
sys.path = [p for p in sys.path if p not in ("", ".", str(Path(__file__).parent))]

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import seaborn as sns  # noqa: E402


sys.path = _orig_path

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — positions 1–3 for the three rings
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Daily fitness summary: Move, Exercise, Stand
metrics = ["Move", "Exercise", "Stand"]
values = [420, 25, 9]
goals = [600, 30, 12]
units = ["kcal", "min", "hr"]
ring_colors = IMPRINT_PALETTE[:3]

# Geometry: outer ring → inner ring
ring_radii = [0.80, 0.56, 0.32]
LW = 26  # ring stroke width in points (rounded caps)
TRACK_ALPHA = 0.14

# Full theme-adaptive rc — follows seaborn.md template exactly
sns.set_theme(
    style="white",
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
sns.set_palette(ring_colors)

# Fractions and arc end-point positions for seaborn progress-tip markers
fractions = [min(v / g, 1.0) for v, g in zip(values, goals, strict=False)]
end_angles = [np.pi / 2 - f * 2 * np.pi for f in fractions]
end_xs = [r * np.cos(a) for r, a in zip(ring_radii, end_angles, strict=False)]
end_ys = [r * np.sin(a) for r, a in zip(ring_radii, end_angles, strict=False)]

# Square canvas — 2400×2400 px (symmetric plot)
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
ax.set_aspect("equal")
ax.set_xlim(-1.5, 1.7)  # wider right margin for value labels
ax.set_ylim(-1.1, 1.2)  # reduced lower whitespace, better composition
ax.axis("off")

# Draw rings outer → inner
for _metric, value, goal, _unit, color, radius in zip(
    metrics, values, goals, units, ring_colors, ring_radii, strict=False
):
    fraction = min(value / goal, 1.0)

    # Background track: full faint circle
    theta_bg = np.linspace(np.pi / 2, np.pi / 2 - 2 * np.pi, 500)
    ax.plot(
        radius * np.cos(theta_bg),
        radius * np.sin(theta_bg),
        color=color,
        alpha=TRACK_ALPHA,
        linewidth=LW,
        solid_capstyle="round",
    )

    # Progress arc: clockwise from 12 o'clock
    if fraction > 0:
        sweep = fraction * 2 * np.pi
        n_pts = max(3, int(sweep * 300))
        theta_arc = np.linspace(np.pi / 2, np.pi / 2 - sweep, n_pts)
        ax.plot(
            radius * np.cos(theta_arc), radius * np.sin(theta_arc), color=color, linewidth=LW, solid_capstyle="round"
        )

# Seaborn: progress-tip indicators at the end of each arc — idiomatic hue+palette usage
marker_s = int(np.pi * (LW / 2) ** 2)  # circle area matching arc linewidth
sns.scatterplot(
    x=end_xs,
    y=end_ys,
    hue=metrics,
    palette=dict(zip(metrics, ring_colors, strict=False)),
    s=marker_s,
    edgecolor=PAGE_BG,
    linewidths=2.0,
    ax=ax,
    legend=False,
    zorder=11,
)
sns.despine(ax=ax, left=True, bottom=True, top=True, right=True)

# Center label: primary metric completion
pct_move = int(values[0] / goals[0] * 100)
ax.text(0, 0.06, f"{pct_move}%", ha="center", va="center", fontsize=22, fontweight="bold", color=INK, zorder=10)
ax.text(0, -0.1, "Move", ha="center", va="center", fontsize=11, color=INK_SOFT, zorder=10)

# Per-ring labels to the right, stacked at ring heights
x_lbl = 1.02
for metric, value, goal, unit, color, radius in zip(
    metrics, values, goals, units, ring_colors, ring_radii, strict=False
):
    pct = int(value / goal * 100)
    ax.text(x_lbl, radius + 0.05, metric, ha="left", va="center", fontsize=9, fontweight="bold", color=color)
    ax.text(
        x_lbl, radius - 0.07, f"{value} / {goal} {unit}  ({pct}%)", ha="left", va="center", fontsize=9, color=INK_MUTED
    )

# Title — 51 chars, under 67-char baseline → fontsize stays at 12
title = "gauge-activity-rings · python · seaborn · anyplot.ai"
n = len(title)
ratio = 67 / n if n > 67 else 1.0
title_fs = max(8, round(12 * ratio))
ax.set_title(title, fontsize=title_fs, fontweight="medium", color=INK, pad=14)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
