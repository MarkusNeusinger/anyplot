""" anyplot.ai
windbarb-basic: Wind Barb Plot for Meteorological Data
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-19
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.patches import Circle


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

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
    },
)
sns.set_context("talk", font_scale=1.2)

# Data: Simulated surface wind observations from a grid of weather stations
np.random.seed(42)

# Create a grid of observation points (6x4 grid = 24 stations)
x_grid = np.linspace(2, 12, 6)
y_grid = np.linspace(2, 8, 4)
x, y = np.meshgrid(x_grid, y_grid)
x = x.flatten()
y = y.flatten()

n_points = len(x)

# Generate wind components with full range: calm, moderate, and strong (with pennants)
base_u = 20 * np.sin(x * 0.4) + 15
base_v = 15 * np.cos(y * 0.5) + 10
noise_u = np.random.randn(n_points) * 8
noise_v = np.random.randn(n_points) * 8

u = base_u + noise_u
v = base_v + noise_v

# Force calm winds (< 2.5 knots) shown as open circles
calm_indices = [0, 11, 23]
for idx in calm_indices:
    u[idx] = 0.5 * (np.random.rand() - 0.5)
    v[idx] = 0.5 * (np.random.rand() - 0.5)

# Force strong winds with pennants (50+ knots)
strong_indices = [5, 9, 18]
for idx in strong_indices:
    angle = np.random.rand() * 2 * np.pi
    speed_val = 55 + np.random.rand() * 15
    u[idx] = speed_val * np.cos(angle)
    v[idx] = speed_val * np.sin(angle)

speed = np.sqrt(u**2 + v**2)

calm_mask = speed < 2.5
barb_mask = ~calm_mask

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
fig.subplots_adjust(bottom=0.15)

if np.any(barb_mask):
    barbs = ax.barbs(
        x[barb_mask],
        y[barb_mask],
        u[barb_mask],
        v[barb_mask],
        speed[barb_mask],
        cmap="viridis",
        length=9,
        linewidth=2.5,
        barb_increments={"half": 5, "full": 10, "flag": 50},
        pivot="middle",
        clim=(0, 75),
    )

    cbar = plt.colorbar(barbs, ax=ax, pad=0.02)
    cbar.set_label("Wind Speed (knots)", fontsize=20, color=INK, rotation=270, labelpad=25)
    cbar.ax.tick_params(labelsize=16, colors=INK_SOFT)
    cbar.ax.yaxis.set_tick_params(color=INK_SOFT)
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color=INK_SOFT)
    cbar.outline.set_edgecolor(INK_SOFT)

# Calm winds as open circles (standard meteorological notation)
calm_circle_color = "#440154" if THEME == "light" else "#90d743"
for idx in np.where(calm_mask)[0]:
    circle = Circle((x[idx], y[idx]), radius=0.35, fill=False, edgecolor=calm_circle_color, linewidth=3)
    ax.add_patch(circle)

# Style
ax.set_xlabel("Longitude (°E)", fontsize=20, color=INK)
ax.set_ylabel("Latitude (°N)", fontsize=20, color=INK)
ax.set_title("windbarb-basic · python · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.grid(False)

for spine in ax.spines.values():
    spine.set_color(INK_SOFT)
    spine.set_linewidth(0.8)

legend_text = "Barb notation: ○ = calm (<2.5 kt) | half barb = 5 kt | full barb = 10 kt | pennant ▲ = 50 kt"
fig.text(0.5, 0.02, legend_text, fontsize=16, ha="center", va="bottom", color=INK_MUTED)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
