""" anyplot.ai
line-cycle-seasonal: Cycle Plot (Seasonal Subseries)
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 87/100 | Created: 2026-06-15
"""

import os
import sys


# Remove this script's directory from sys.path so 'import seaborn' finds the installed
# library rather than this file (Python adds the script dir to sys.path[0] automatically)
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _script_dir]

import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens (Imprint palette — see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"  # Imprint palette position 1 — always first series

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

# Data: monthly average temperatures (°C) over 24 years for a mid-latitude city
# A warming trend of ~0.035 °C/year is embedded within each month's subseries
np.random.seed(42)
years = np.arange(2000, 2024)
n_years = len(years)

month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
base_temps = np.array([1.8, 3.2, 7.5, 12.1, 17.0, 21.3, 24.1, 23.6, 18.8, 13.0, 6.8, 2.9])

rows = []
for yi, year in enumerate(years):
    for mi, (base_temp, month_name) in enumerate(zip(base_temps, month_names, strict=False)):
        temp = base_temp + 0.035 * yi + np.random.normal(0, 0.7)
        rows.append({"year": year, "month_idx": mi, "month_name": month_name, "temp": temp})

df = pd.DataFrame(rows)

# Layout: 12 month groups along the shared x-axis; years spread within each group
group_width = 1.0
gap = 0.28
group_starts = np.arange(12) * (group_width + gap)
group_centers = group_starts + group_width / 2
year_offsets = np.linspace(0, group_width, n_years)

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for mi in range(12):
    month_data = df[df["month_idx"] == mi].sort_values("year")
    x_base = group_starts[mi]
    x_vals = x_base + year_offsets
    y_vals = month_data["temp"].values

    # Chronological subseries line (within-season trend)
    ax.plot(x_vals, y_vals, color=BRAND, linewidth=1.5, alpha=0.75, zorder=2)

    # Horizontal reference line at the group mean (key visual for seasonal comparison)
    mean_val = y_vals.mean()
    ax.hlines(mean_val, x_base, x_base + group_width, colors=INK, linewidth=2.0, alpha=0.85, zorder=3)

# Subtle vertical dividers between seasonal groups
for mi in range(1, 12):
    x_div = group_starts[mi] - gap / 2
    ax.axvline(x_div, color=INK_MUTED, linewidth=0.6, alpha=0.25, zorder=1)

# Style
ax.set_xticks(group_centers)
ax.set_xticklabels(month_names, fontsize=8, color=INK_SOFT)
ax.tick_params(axis="x", length=0)
ax.tick_params(axis="y", labelsize=8, colors=INK_SOFT)
ax.set_xlim(group_starts[0] - 0.18, group_starts[-1] + group_width + 0.18)

ax.set_xlabel("Month", fontsize=10, color=INK)
ax.set_ylabel("Avg Temperature (°C)", fontsize=10, color=INK)

title = "line-cycle-seasonal · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK, pad=10)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK, zorder=0)
ax.set_axisbelow(True)

# Legend for the two visual elements
trend_handle = mlines.Line2D([], [], color=BRAND, linewidth=1.5, label="Yearly values")
mean_handle = mlines.Line2D([], [], color=INK, linewidth=2.0, label="Monthly mean")
ax.legend(
    handles=[trend_handle, mean_handle],
    fontsize=8,
    loc="upper left",
    frameon=True,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
    labelcolor=INK_SOFT,
)

fig.subplots_adjust(left=0.08, right=0.97, top=0.92, bottom=0.12)

# Save — no bbox_inches='tight' (would trim canvas away from exact 3200×1800 target)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
