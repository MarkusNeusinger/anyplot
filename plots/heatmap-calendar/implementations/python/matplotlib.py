""" anyplot.ai
heatmap-calendar: Basic Calendar Heatmap
Library: matplotlib 3.10.9 | Python 3.14.4
Quality: 86/100 | Updated: 2026-04-27
"""

import os

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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Theme-adaptive colormap: near-background for zero, green for high activity
if THEME == "light":
    _cal_colors = ["#E0EAE3", "#c6e48b", "#7bc96f", "#239a3b", "#196127"]
else:
    _cal_colors = ["#2A2A25", "#1a4731", "#2d7040", "#239a3b", "#52c760"]
cmap = LinearSegmentedColormap.from_list("calendar", _cal_colors, N=256)

# Data
np.random.seed(42)
dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
n_days = len(dates)
date_idx = pd.DatetimeIndex(dates)

# Vectorized activity generation with realistic developer patterns
base = np.random.poisson(3, n_days)
weekday_mask = np.asarray(date_idx.dayofweek < 5)
weekday_bonus = np.random.poisson(2, n_days) * weekday_mask
zero_mask = np.random.random(n_days) < 0.15
spike_mask = np.random.random(n_days) < 0.05

activity = (base + weekday_bonus).astype(float)
activity[zero_mask] = 0
activity += np.random.randint(0, 15, n_days) * spike_mask

# Vacation period: 2 weeks of no activity in August
vacation = np.asarray((date_idx.month == 8) & (date_idx.day >= 5) & (date_idx.day <= 19))
activity[vacation] = 0

# Project deadline spike: high activity in late March
deadline = np.asarray((date_idx.month == 3) & (date_idx.day >= 20))
activity[deadline] += np.random.randint(5, 12, int(deadline.sum()))

# Calendar layout — vectorized grid assignment
week_of_year = np.asarray((dates - dates[0]).days // 7)
dayofweek = np.asarray(date_idx.dayofweek)

n_weeks = week_of_year.max() + 1
heatmap_data = np.full((7, n_weeks), np.nan)
heatmap_data[dayofweek, week_of_year] = activity

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

x = np.arange(n_weeks + 1)
y = np.arange(8)
mesh = ax.pcolormesh(
    x,
    y,
    np.ma.masked_invalid(heatmap_data),
    cmap=cmap,
    vmin=0,
    vmax=np.nanmax(heatmap_data),
    edgecolors=PAGE_BG,
    linewidth=1.5,
)

# Style: weekday labels on y-axis
weekday_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
ax.set_yticks(np.arange(7) + 0.5)
ax.set_yticklabels(weekday_labels, fontsize=16, color=INK_SOFT)

# Month labels at top
month_positions = []
month_labels = []
for month in range(1, 13):
    mask = np.asarray(date_idx.month == month)
    if mask.any():
        month_positions.append(week_of_year[mask][0])
        month_labels.append(pd.Timestamp(2024, month, 1).strftime("%b"))

ax.set_xticks(month_positions)
ax.set_xticklabels(month_labels, fontsize=16, color=INK_SOFT)
ax.xaxis.tick_top()
ax.xaxis.set_label_position("top")

for spine in ax.spines.values():
    spine.set_visible(False)

ax.invert_yaxis()
ax.tick_params(colors=INK_SOFT, length=0)

# Colorbar
cbar = plt.colorbar(mesh, ax=ax, orientation="horizontal", pad=0.06, shrink=0.55, aspect=35)
cbar.ax.tick_params(labelsize=14, labelcolor=INK_SOFT, color=INK_SOFT)
cbar.set_label("Daily Commits", fontsize=16, color=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

ax.set_title("heatmap-calendar · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=20)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
