""" anyplot.ai
spiral-timeseries: Spiral Time Series Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 90/100 | Created: 2026-05-07
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Data: Daily average temperatures over 5 years (Berlin-like climate)
np.random.seed(42)
n_years = 5
start_year = 2019
days_per_year = 365
total_days = n_years * days_per_year

day_idx = np.arange(total_days)
day_of_year = day_idx % days_per_year

seasonal = -11.0 * np.cos(2 * np.pi * day_of_year / days_per_year)
warming_trend = 0.6 * day_idx / total_days
noise = np.random.normal(0, 3.5, total_days)
temperatures = 10.0 + seasonal + warming_trend + noise

# Archimedean spiral: r = r0 + spacing * (cumulative_angle / 2π)
r0 = 1.2
rev_spacing = 1.4
total_angle = day_idx * (2 * np.pi / days_per_year)
r = r0 + rev_spacing * total_angle / (2 * np.pi)

# Clockwise rotation, January starts at 12 o'clock
theta = -total_angle + np.pi / 2
x = r * np.cos(theta)
y = r * np.sin(theta)

r_max = r0 + rev_spacing * n_years

# Plot
fig, ax = plt.subplots(figsize=(12, 12), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
ax.set_aspect("equal")

# Spiral colored by temperature (cividis: cold=dark, warm=bright)
points = np.column_stack([x, y]).reshape(-1, 1, 2)
segments = np.concatenate([points[:-1], points[1:]], axis=1)
t_min, t_max = temperatures.min(), temperatures.max()
norm = plt.Normalize(t_min, t_max)
lc = LineCollection(segments, cmap="cividis", norm=norm, linewidth=2.8, alpha=0.95)
lc.set_array(temperatures[:-1])
ax.add_collection(lc)

# Month radial grid lines and outer labels
month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
for m in range(12):
    m_angle = -2 * np.pi * m / 12 + np.pi / 2
    ax.plot([0, r_max * np.cos(m_angle)], [0, r_max * np.sin(m_angle)], color=INK_SOFT, alpha=0.22, linewidth=0.8)
    label_r = r_max + 0.62
    cos_a, sin_a = np.cos(m_angle), np.sin(m_angle)
    ha = "left" if cos_a > 0.1 else ("right" if cos_a < -0.1 else "center")
    va = "bottom" if sin_a > 0.1 else ("top" if sin_a < -0.1 else "center")
    ax.text(label_r * cos_a, label_r * sin_a, month_names[m], ha=ha, va=va, fontsize=15, color=INK_SOFT)

# Concentric year-boundary rings and year labels
for yi in range(n_years + 1):
    ring_r = r0 + rev_spacing * yi
    ring_theta = np.linspace(0, 2 * np.pi, 500)
    ax.plot(
        ring_r * np.cos(ring_theta),
        ring_r * np.sin(ring_theta),
        color=INK_SOFT,
        alpha=0.22,
        linewidth=0.8,
        linestyle="--",
    )
    if yi < n_years:
        # Place year label just left of 12 o'clock where this revolution starts
        ax.text(
            -0.18,
            ring_r + 0.06,
            str(start_year + yi),
            ha="right",
            va="bottom",
            fontsize=14,
            fontweight="bold",
            color=INK,
        )

# Colorbar
sm = plt.cm.ScalarMappable(cmap="cividis", norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, fraction=0.030, pad=0.04, aspect=25)
cbar.set_label("Daily Temperature (°C)", fontsize=18, color=INK)
cbar.ax.tick_params(labelsize=14, colors=INK_SOFT, labelcolor=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)
plt.setp(cbar.ax.yaxis.get_ticklabels(), color=INK_SOFT)

# Axis bounds, title, and cleanup
margin = r_max + 1.5
ax.set_xlim(-margin, margin)
ax.set_ylim(-margin, margin)
ax.axis("off")

ax.set_title(
    "Seasonal Temperature Cycles  ·  spiral-timeseries  ·  matplotlib  ·  anyplot.ai",
    fontsize=20,
    fontweight="medium",
    color=INK,
    pad=16,
)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
