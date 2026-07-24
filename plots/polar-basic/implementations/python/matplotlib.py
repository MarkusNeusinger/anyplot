""" anyplot.ai
polar-basic: Basic Polar Chart
Library: matplotlib 3.11.1 | Python 3.13.14
Quality: 77/100 | Updated: 2026-07-24
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter


# Theme tokens (Imprint palette)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data - hourly temperature pattern (24-hour diurnal cycle)
np.random.seed(42)
hours = np.arange(24)
theta = hours * (2 * np.pi / 24)

base_temp = 15 + 8 * np.sin(theta - np.pi / 2)  # smooth diurnal curve, trough near midnight
noise = np.random.randn(24) * 1.5
radius = base_temp + noise

theta_closed = np.append(theta, theta[0])
radius_closed = np.append(radius, radius[0])

peak_idx = int(np.argmax(radius))
peak_hour, peak_temp = hours[peak_idx], radius[peak_idx]
avg_temp = radius.mean()

# Plot - square canvas for a symmetric polar chart (6x6in @ 400dpi = 2400x2400 px)
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, subplot_kw={"projection": "polar"}, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Filled area from center to data for visual weight
ax.fill_between(theta_closed, 0, radius_closed, color=BRAND, alpha=0.18, zorder=1)

# Connecting line showing the cyclical pattern
ax.plot(theta_closed, radius_closed, color=BRAND, linewidth=2.5, alpha=0.9, zorder=2)

# Scatter points for individual hourly readings
ax.scatter(theta, radius, s=90, color=BRAND, alpha=0.95, zorder=3, edgecolors=PAGE_BG, linewidth=1.0)

# Dashed reference ring at the daily average - a second radial layer for context
ring_theta = np.linspace(0, 2 * np.pi, 200)
ax.plot(
    ring_theta, np.full_like(ring_theta, avg_temp), linestyle="--", linewidth=1.0, color=INK_SOFT, alpha=0.6, zorder=1.5
)
ax.text(np.deg2rad(315), avg_temp + 1.4, f"avg {avg_temp:.1f}°C", fontsize=7, color=INK_SOFT, ha="center")

# Callout for the daily peak
ax.annotate(
    f"Peak {peak_temp:.1f}°C",
    xy=(theta[peak_idx], peak_temp),
    xytext=(theta[peak_idx] + 0.4, peak_temp + 4.5),
    fontsize=8,
    color=INK,
    ha="center",
    arrowprops={"arrowstyle": "-", "color": INK_SOFT, "linewidth": 1.0},
    bbox={"boxstyle": "round,pad=0.35", "facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.95},
    zorder=4,
)

# Configure angular axis (hours of day, midnight at top, clockwise)
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)
hour_labels = ["12 AM", "3 AM", "6 AM", "9 AM", "12 PM", "3 PM", "6 PM", "9 PM"]
ax.set_xticks(np.linspace(0, 2 * np.pi, 8, endpoint=False))
ax.set_xticklabels(hour_labels, fontsize=9)

# Configure radial axis (temperature) with a formatter instead of a static label list
ax.set_ylim(0, 30)
ax.set_yticks([5, 10, 15, 20, 25])
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, pos: f"{v:.0f}°C"))
ax.tick_params(axis="y", labelsize=8)
ax.set_rlabel_position(247.5)
# Radial labels must draw above the filled data area: the y-Axis container's own
# zorder (2.5 by default) governs the whole tick group's draw order, not each
# Text's zorder, so it needs raising above the scatter (zorder=3) too.
ax.yaxis.set_zorder(6)
for label in ax.get_yticklabels():
    label.set_bbox({"facecolor": PAGE_BG, "edgecolor": "none", "alpha": 0.9, "pad": 2.5})

# Theme-adaptive styling
title = "Hourly Temperature Pattern · polar-basic · python · matplotlib · anyplot.ai"
ax.set_title(title, fontsize=12, pad=16, fontweight="medium", color=INK)
ax.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.spines["polar"].set_color(INK_SOFT)
ax.tick_params(colors=INK_SOFT, labelcolor=INK_SOFT)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
