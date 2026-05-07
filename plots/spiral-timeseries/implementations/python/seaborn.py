""" anyplot.ai
spiral-timeseries: Spiral Time Series Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 87/100 | Created: 2026-05-07
"""

import os
import sys


# Prevent this file from shadowing the installed seaborn package
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if not (p and os.path.abspath(p) == _this_dir)]

import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

sns.set_theme(style="white", rc={"figure.facecolor": PAGE_BG, "axes.facecolor": PAGE_BG, "text.color": INK})

# Data: 5 years of daily average temperatures (Northern Hemisphere city)
np.random.seed(42)
n_years = 5
days_per_year = 365
n = n_years * days_per_year

dates = pd.date_range("2020-01-01", periods=n, freq="D")
day_of_year_arr = np.array([d.timetuple().tm_yday for d in dates])
year_num_arr = np.array([d.year - 2020 for d in dates])

# Seasonal temperature: peak ~July, trough ~January, with warming trend + noise
temperature = (
    12.0 + 14.0 * np.sin(2 * np.pi * (day_of_year_arr - 80) / 365) + 0.4 * year_num_arr + np.random.normal(0, 2.5, n)
)

# Archimedean spiral: theta increases 2π per year, r grows with each revolution
theta = 2 * np.pi * np.arange(n) / days_per_year
r_min = 2.0
arm_spacing = 1.3
r = r_min + arm_spacing * (theta / (2 * np.pi))

# Build colored line segments for the spiral
points = np.column_stack([theta, r]).reshape(-1, 1, 2)
segments = np.concatenate([points[:-1], points[1:]], axis=1)

norm = Normalize(vmin=temperature.min(), vmax=temperature.max())
lc = LineCollection(segments, cmap="viridis", norm=norm, linewidth=5, alpha=0.92, zorder=3)
lc.set_array(temperature[:-1])

# Plot: square figure with polar axes
fig = plt.figure(figsize=(12, 12), facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="polar")
ax.set_facecolor(PAGE_BG)

# January at top, spiral growing clockwise
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)
ax.add_collection(lc)

# Radial limits
r_outer = r_min + arm_spacing * n_years + 0.8
ax.set_ylim(0, r_outer)

# Month angular ticks and labels around the outer ring
month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
month_start_days = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
month_angles_deg = [360.0 * (d - 1) / 365.0 for d in month_start_days]

ax.set_thetagrids(month_angles_deg, labels=month_names)
for label in ax.get_xticklabels():
    label.set_color(INK_SOFT)
    label.set_fontsize(18)
ax.tick_params(axis="x", pad=22, length=0)

# Remove radial tick marks and labels (they clutter the spiral)
ax.set_rticks([])
ax.set_yticklabels([])

# Year labels at the start of each spiral arm (just past Jan 1, clockwise)
year_label_angle = np.radians(10)
for yr in range(n_years):
    yr_r = r_min + arm_spacing * yr + 0.1
    ax.text(
        year_label_angle,
        yr_r,
        str(2020 + yr),
        ha="left",
        va="center",
        fontsize=15,
        color=INK,
        fontweight="bold",
        zorder=6,
    )

# Show only spoke grid lines (months), hide concentric r-circles
ax.yaxis.grid(False)
ax.xaxis.grid(True, alpha=0.10, color=INK, linewidth=0.8)
ax.spines["polar"].set_visible(False)

# Colorbar
sm = cm.ScalarMappable(cmap="viridis", norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, pad=0.08, shrink=0.65, aspect=22)
cbar.set_label("Daily Avg. Temp. (°C)", fontsize=18, color=INK, labelpad=12)
cbar.ax.tick_params(labelsize=15, colors=INK_SOFT)
for lbl in cbar.ax.yaxis.get_ticklabels():
    lbl.set_color(INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Title
fig.suptitle("spiral-timeseries · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK, y=0.98)

plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
