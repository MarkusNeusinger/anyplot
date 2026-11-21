"""anyplot.ai
heatmap-polar: Polar Heatmap for Cyclic Two-Dimensional Data
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 90/100 | Created: 2026-05-13
"""

import os
import sys


sys.path.pop(0)  # prevent shadowing the matplotlib library with this file

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — sequential colormap for single-sign data
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

# Columns
DAY = "Day"  # role: radial
HOUR = "Hour of day"  # role: angular
VISITS = "Hourly Visits"  # role: value

# Data — hourly website visits by day of week
np.random.seed(42)
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
hours = np.arange(24)
h = hours.astype(float)
wd_factors = [0.92, 0.98, 1.05, 1.02, 1.08]
rows = []
for i, day in enumerate(days):
    if i < 5:  # weekday: morning surge (9am) + evening surge (7pm) + late-night tail
        base = (
            700 * np.exp(-0.5 * ((h - 9) / 1.5) ** 2)
            + 800 * np.exp(-0.5 * ((h - 19) / 2.0) ** 2)
            + 90 * np.exp(-0.5 * ((h - 3) / 2.5) ** 2)
        ) * wd_factors[i]
    else:  # weekend: broad afternoon peak (2pm), quieter mornings
        base = 850 * np.exp(-0.5 * ((h - 14) / 3.5) ** 2) + 70 * np.exp(-0.5 * ((h - 2) / 2.0) ** 2)
    visits = np.maximum(50, base + np.random.normal(0, 25, len(hours)))
    rows.append(pd.DataFrame({DAY: day, HOUR: hours, VISITS: visits}))
df = pd.concat(rows, ignore_index=True)

# Plot
table = df.pivot_table(index=DAY, columns=HOUR, values=VISITS, sort=False)
n_days, n_hours = table.shape

fig = plt.figure(figsize=(8, 8), dpi=300, facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="polar")
ax.set_facecolor(PAGE_BG)

# Clock orientation: midnight at top, hours run clockwise
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)

r_inner, r_outer = 2.0, 9.0
theta_edges = np.linspace(0, 2 * np.pi, n_hours + 1)
r_edges = np.linspace(r_inner, r_outer, n_days + 1)
r_centers = (r_edges[:-1] + r_edges[1:]) / 2

mesh = ax.pcolormesh(
    theta_edges, r_edges, table.to_numpy(), cmap=imprint_seq, shading="flat", edgecolors=PAGE_BG, linewidth=0.8
)

# Angular axis: label at clock quadrants only
quarter_idx = [round(n_hours * k / 4) for k in range(4)]
ax.set_xticks(theta_edges[quarter_idx])
quarter_labels = [f"{(int(table.columns[i]) % 12) or 12}{'am' if table.columns[i] < 12 else 'pm'}" for i in quarter_idx]
ax.set_xticklabels(quarter_labels, fontsize=15, color=INK_SOFT)
ax.tick_params(axis="x", pad=12, colors=INK_SOFT)

# Radial axis: day labels in boxes for contrast against the cells
ax.set_yticks([])
ax.set_ylim(0, r_outer + 0.3)
label_angle = theta_edges[1] * 1.5
for r, day in zip(r_centers, table.index, strict=True):
    ax.text(
        label_angle,
        r,
        day,
        ha="center",
        va="center",
        fontsize=12,
        color=INK,
        fontweight="medium",
        zorder=10,
        bbox={
            "facecolor": ELEVATED_BG,
            "edgecolor": INK_SOFT,
            "alpha": 0.9,
            "boxstyle": "round,pad=0.2",
            "linewidth": 0.5,
        },
    )

ax.grid(False)
ax.spines["polar"].set_visible(False)

# Title
ax.set_title(
    "Website Traffic · heatmap-polar · python · matplotlib · anyplot.ai",
    fontsize=14,
    fontweight="medium",
    color=INK,
    pad=24,
)

# Colorbar
cbar = fig.colorbar(mesh, ax=ax, fraction=0.04, pad=0.1, shrink=0.72, aspect=22)
cbar.set_label(VISITS, fontsize=14, color=INK)
cbar.ax.tick_params(labelsize=12, labelcolor=INK_SOFT, color=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=300, facecolor=PAGE_BG)
