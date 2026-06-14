"""anyplot.ai
gauge-activity-rings: Activity Rings Progress Chart
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-06-14
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens (Imprint palette + chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Daily fitness goal data — Move / Exercise / Stand
metrics = [
    {"name": "Move", "value": 420, "goal": 600, "unit": "kcal"},
    {"name": "Exercise", "value": 28, "goal": 30, "unit": "min"},
    {"name": "Stand", "value": 9, "goal": 12, "unit": "hr"},
]
ring_colors = IMPRINT_PALETTE[:3]  # green → lavender → blue
radii = [0.78, 0.53, 0.28]  # outer → inner
ring_lw = 20  # linewidth in screen points

fractions = [min(m["value"] / m["goal"], 1.0) for m in metrics]
avg_pct = sum(fractions) / len(fractions)

# Plot — square canvas for circular rings
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
ax.set_aspect("equal")
ax.set_xlim(-1.1, 1.1)
ax.set_ylim(-1.1, 1.1)
ax.axis("off")

theta_full = np.linspace(0, 2 * np.pi, 600)

for _metric, color, r, frac in zip(metrics, ring_colors, radii, fractions, strict=False):
    # Faint background track — full circle at low opacity
    ax.plot(
        r * np.cos(theta_full),
        r * np.sin(theta_full),
        linewidth=ring_lw,
        color=color,
        alpha=0.15,
        solid_capstyle="round",
        zorder=2,
    )
    # Progress arc — clockwise from 12 o'clock (π/2 in standard math angles)
    t0 = np.pi / 2
    t1 = t0 - frac * 2 * np.pi
    n_pts = max(int(abs(frac) * 500) + 2, 4)
    theta_arc = np.linspace(t0, t1, n_pts)
    ax.plot(
        r * np.cos(theta_arc), r * np.sin(theta_arc), linewidth=ring_lw, color=color, solid_capstyle="round", zorder=3
    )

# Center summary — overall average progress
ax.text(0, 0.06, f"{avg_pct:.0%}", ha="center", va="center", fontsize=22, fontweight="bold", color=INK, zorder=5)
ax.text(0, -0.10, "Daily Goals", ha="center", va="center", fontsize=9, color=INK_MUTED, zorder=5)

# Title
title = "gauge-activity-rings · python · matplotlib · anyplot.ai"
n = len(title)
title_fs = max(8, round(12 * 67 / n)) if n > 67 else 12
ax.set_title(title, fontsize=title_fs, fontweight="medium", color=INK, pad=14)

# Per-ring metric labels below the chart (figure coordinates)
fig.subplots_adjust(left=0.05, right=0.95, top=0.93, bottom=0.16)
label_ys = [0.140, 0.107, 0.074]

for i, (metric, color, frac) in enumerate(zip(metrics, ring_colors, fractions, strict=False)):
    pct = f"{frac:.0%}"
    label = f"●  {metric['name']}     {metric['value']} / {metric['goal']} {metric['unit']}     ({pct})"
    fig.text(0.50, label_ys[i], label, ha="center", va="top", fontsize=9, color=color)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
