""" anyplot.ai
polar-scatter: Polar Scatter Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-09
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD"]

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
        "grid.alpha": 0.10,
        "legend.facecolor": PAGE_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Data - Wind measurements with prevailing directions
np.random.seed(42)
n_points = 120

# Morning winds: predominantly from SW (around 225 degrees)
morning_angles = np.random.normal(225, 30, n_points // 2) % 360
morning_speeds = np.random.gamma(3, 3, n_points // 2) + 5

# Afternoon winds: predominantly from NE (around 45 degrees)
afternoon_angles = np.random.normal(45, 40, n_points // 2) % 360
afternoon_speeds = np.random.gamma(2.5, 4, n_points // 2) + 3

# Combine data
angles_deg = np.concatenate([morning_angles, afternoon_angles])
speeds = np.concatenate([morning_speeds, afternoon_speeds])
time_of_day = ["Morning"] * (n_points // 2) + ["Afternoon"] * (n_points // 2)

# Convert to radians for plotting
angles_rad = np.deg2rad(angles_deg)

# Create DataFrame for seaborn
df = pd.DataFrame({"angle_rad": angles_rad, "speed": speeds, "time_of_day": time_of_day})

# Create polar plot
fig = plt.figure(figsize=(16, 9), facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="polar")

# Create scatter with Okabe-Ito colors
sns.scatterplot(
    data=df,
    x="angle_rad",
    y="speed",
    hue="time_of_day",
    palette=IMPRINT,
    hue_order=["Morning", "Afternoon"],
    s=150,
    alpha=0.7,
    ax=ax,
    edgecolor=PAGE_BG,
    linewidth=0.5,
)

# Configure polar plot appearance
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)

# Set angular ticks with cardinal directions
ax.set_xticks(np.deg2rad([0, 45, 90, 135, 180, 225, 270, 315]))
ax.set_xticklabels(["N", "NE", "E", "SE", "S", "SW", "W", "NW"], fontsize=18, color=INK_SOFT)

# Configure radial axis
max_speed = max(speeds)
ax.set_ylim(0, max_speed * 1.1)
ax.tick_params(axis="y", labelsize=16, colors=INK_SOFT)

# Add radial label on the left side
ax.text(np.deg2rad(330), max_speed * 0.5, "Wind Speed (m/s)", fontsize=16, ha="center", va="center", color=INK)

# Style the grid
ax.grid(True, alpha=0.15, linewidth=0.8)

# Title
ax.set_title("polar-scatter · seaborn · anyplot.ai", fontsize=24, fontweight="medium", pad=20, color=INK)

# Legend
legend = ax.legend(
    title="Time of Day",
    title_fontsize=16,
    fontsize=16,
    loc="upper right",
    bbox_to_anchor=(1.1, 1.0),
    framealpha=0.9,
    facecolor=PAGE_BG,
    edgecolor=INK_SOFT,
)
if legend.get_title():
    legend.get_title().set_color(INK)
    for t in legend.texts:
        t.set_color(INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
