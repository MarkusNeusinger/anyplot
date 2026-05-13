"""anyplot.ai
heatmap-polar: Polar Heatmap for Cyclic Two-Dimensional Data
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-05-13
"""

import os
import sys


sys.path.pop(0)  # prevent shadowing the matplotlib library with this file

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Data — hourly website visits by day of week
np.random.seed(42)
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
n_days = 7
n_hours = 24
h = np.arange(n_hours, dtype=float)

# Weekday pattern: morning surge (9am) + evening surge (7pm) + late-night tail
wd_factors = [0.92, 0.98, 1.05, 1.02, 1.08]
traffic = np.zeros((n_days, n_hours))
for i in range(5):
    f = wd_factors[i]
    base = (
        700 * np.exp(-0.5 * ((h - 9) / 1.5) ** 2)
        + 800 * np.exp(-0.5 * ((h - 19) / 2.0) ** 2)
        + 90 * np.exp(-0.5 * ((h - 3) / 2.5) ** 2)
    )
    traffic[i] = np.maximum(50, base * f + np.random.normal(0, 25, n_hours))

# Weekend pattern: broad afternoon peak (2pm), quieter mornings
for i in range(5, 7):
    base = 850 * np.exp(-0.5 * ((h - 14) / 3.5) ** 2) + 70 * np.exp(-0.5 * ((h - 2) / 2.0) ** 2)
    traffic[i] = np.maximum(50, base + np.random.normal(0, 25, n_hours))

# Plot
fig = plt.figure(figsize=(12, 12), facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="polar")
ax.set_facecolor(PAGE_BG)

# Clock orientation: midnight at top, hours run clockwise
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)

r_inner, r_outer = 2.0, 9.0
theta_edges = np.linspace(0, 2 * np.pi, n_hours + 1)  # 25 edges for 24 hour cells
r_edges = np.linspace(r_inner, r_outer, n_days + 1)  # 8 edges for 7 day rings
r_centers = (r_edges[:-1] + r_edges[1:]) / 2

mesh = ax.pcolormesh(theta_edges, r_edges, traffic, cmap="viridis", shading="flat")

# Cell borders — background-colored lines separate angular and radial cells
circle_theta = np.linspace(0, 2 * np.pi, 300)
for r in r_edges:
    ax.plot(circle_theta, [r] * 300, color=PAGE_BG, linewidth=1.2, zorder=5)
for theta in theta_edges:
    ax.plot([theta, theta], [r_inner, r_outer], color=PAGE_BG, linewidth=0.7, zorder=5)

# Angular axis: label at clock quadrants only
ax.set_xticks([0, np.pi / 2, np.pi, 3 * np.pi / 2])
ax.set_xticklabels(["12am", "6am", "12pm", "6pm"], fontsize=18, color=INK_SOFT)
ax.tick_params(axis="x", pad=15, colors=INK_SOFT)

# Radial axis: day-of-week labels with background box for contrast against dark viridis cells
ax.set_yticks([])
ax.set_yticklabels([])
ax.set_ylim(0, r_outer + 0.3)
label_angle = 2 * np.pi * 1.5 / 24  # 1:30am clockwise from midnight
for r, day in zip(r_centers, days, strict=False):
    ax.text(
        label_angle,
        r,
        day,
        ha="center",
        va="center",
        fontsize=14,
        color=INK,
        fontweight="medium",
        zorder=10,
        bbox={
            "facecolor": ELEVATED_BG,
            "edgecolor": INK_SOFT,
            "alpha": 0.88,
            "boxstyle": "round,pad=0.25",
            "linewidth": 0.5,
        },
    )

ax.grid(False)
ax.spines["polar"].set_visible(False)

# Title
ax.set_title(
    "Website Traffic · heatmap-polar · matplotlib · anyplot.ai", fontsize=22, fontweight="medium", color=INK, pad=30
)

# Colorbar
cbar = fig.colorbar(mesh, ax=ax, fraction=0.04, pad=0.1, shrink=0.72, aspect=22)
cbar.set_label("Hourly Visits", fontsize=18, color=INK)
cbar.ax.tick_params(labelsize=14, labelcolor=INK_SOFT, color=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
