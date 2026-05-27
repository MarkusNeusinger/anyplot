"""anyplot.ai
map-animated-temporal: Animated Map over Time
Library: matplotlib | Python 3.13
Quality: pending | Updated: 2026-05-27
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.cm import ScalarMappable
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import Polygon


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OCEAN_BG = "#C8DDF0" if THEME == "light" else "#1E3A4A"
LAND_COLOR = "#E8E4D8" if THEME == "light" else "#2E2E28"

# anyplot diverging cmap: blue (cold anomaly) → neutral → red (warm anomaly)
midpoint = "#FAF8F1" if THEME == "light" else "#1A1A17"
imprint_div = LinearSegmentedColormap.from_list("imprint_div", ["#4467A3", midpoint, "#AE3030"])

# Data: European weather station temperature anomalies over 12 months
np.random.seed(42)

station_coords = [
    (48.86, 2.35),
    (51.51, -0.13),
    (52.52, 13.40),
    (41.90, 12.50),
    (40.42, -3.70),
    (59.33, 18.07),
    (60.17, 24.94),
    (55.68, 12.57),
    (52.37, 4.90),
    (50.85, 4.35),
    (48.21, 16.37),
    (47.50, 19.04),
    (50.08, 14.44),
    (52.23, 21.01),
    (38.72, -9.14),
    (45.46, 9.19),
    (43.30, 5.37),
    (53.55, 9.99),
    (48.14, 11.58),
    (45.44, 12.32),
    (41.39, 2.17),
    (37.98, 23.73),
    (44.43, 26.10),
    (42.70, 23.32),
    (46.95, 7.45),
]

n_months = 12
months = pd.date_range("2025-01-01", periods=n_months, freq="ME")
month_names = [m.strftime("%b %Y") for m in months]

lats = np.array([s[0] for s in station_coords])
lons = np.array([s[1] for s in station_coords])
n_stations = len(station_coords)

# Warming pattern: base anomaly grows over time, spreading north from southern stations
anomalies = np.zeros((n_months, n_stations))
for t in range(n_months):
    base = 0.5 + t * 0.15
    lat_effect = (50 - lats) * 0.03
    lag = np.maximum(0, (t - (lats - 35) / 5)) * 0.1
    anomalies[t] = base + lat_effect + lag + np.random.normal(0, 0.3, n_stations)

# Simplified Europe coastline as (lon, lat) polygon vertices
europe_coastline = [
    [(-10, 36), (-6, 37), (-2, 36), (3, 43), (0, 44), (-2, 43), (-8, 44), (-9, 42), (-10, 36)],
    [(-6, 50), (-5, 54), (-4, 58), (-8, 58), (-6, 55), (-6, 50)],
    [
        (-5, 43),
        (0, 43),
        (3, 43),
        (6, 44),
        (8, 44),
        (12, 46),
        (14, 45),
        (14, 41),
        (16, 40),
        (20, 40),
        (24, 37),
        (26, 38),
        (28, 41),
        (30, 42),
        (32, 42),
        (28, 56),
        (24, 55),
        (22, 56),
        (19, 55),
        (14, 54),
        (12, 56),
        (10, 56),
        (10, 54),
        (5, 54),
        (3, 51),
        (4, 51),
        (5, 49),
        (8, 48),
        (10, 47),
        (12, 44),
        (10, 47),
        (8, 48),
        (5, 49),
        (4, 51),
        (3, 51),
        (2, 50),
        (-2, 50),
        (-5, 48),
        (-5, 43),
    ],
    [
        (5, 58),
        (10, 62),
        (12, 65),
        (20, 70),
        (28, 70),
        (30, 60),
        (24, 55),
        (22, 56),
        (19, 55),
        (14, 54),
        (12, 56),
        (10, 56),
        (5, 58),
    ],
    [(8, 44), (12, 46), (14, 45), (16, 38), (15, 37), (12, 38), (10, 42), (8, 44)],
    [(20, 40), (24, 37), (26, 38), (28, 41), (24, 40), (20, 40)],
]

vmin, vmax = -1.0, 3.5
# Key snapshots: every other month — Jan, Mar, May, Jul, Sep, Nov
snapshot_indices = [0, 2, 4, 6, 8, 10]

# Plot: 2×3 small-multiples grid of key monthly snapshots
title = "map-animated-temporal · python · matplotlib · anyplot.ai"
fig, axes = plt.subplots(2, 3, figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
fig.suptitle(title, fontsize=11, fontweight="medium", color=INK, y=0.995)

for ax, month_idx in zip(axes.flat, snapshot_indices, strict=False):
    ax.set_facecolor(OCEAN_BG)

    for coastline in europe_coastline:
        poly = Polygon(coastline, facecolor=LAND_COLOR, edgecolor=INK_SOFT, linewidth=0.3, zorder=1)
        ax.add_patch(poly)

    # Graticule lines — more visible than minimal dotted hairlines
    for lat in range(35, 75, 10):
        ax.axhline(y=lat, color=INK_SOFT, linewidth=0.5, linestyle=":", alpha=0.55, zorder=0)
    for lon in range(-10, 35, 10):
        ax.axvline(x=lon, color=INK_SOFT, linewidth=0.5, linestyle=":", alpha=0.55, zorder=0)

    ax.set_xlim(-15, 35)
    ax.set_ylim(33, 72)

    current = anomalies[month_idx]
    sizes = 60 + np.abs(current) * 50

    ax.scatter(
        lons,
        lats,
        c=current,
        s=sizes,
        cmap=imprint_div,
        vmin=vmin,
        vmax=vmax,
        alpha=0.9,
        edgecolors=INK,
        linewidths=0.6,
        zorder=5,
    )

    ax.text(
        0.04,
        0.96,
        month_names[month_idx],
        transform=ax.transAxes,
        fontsize=7,
        fontweight="bold",
        ha="left",
        va="top",
        color=INK,
        bbox={"facecolor": ELEVATED_BG, "edgecolor": "none", "alpha": 0.85, "pad": 1.5},
    )

    ax.tick_params(axis="both", labelsize=5, colors=INK_SOFT)
    for spine in ax.spines.values():
        spine.set_color(INK_SOFT)
        spine.set_linewidth(0.4)

# Axis labels on left column and bottom row only
for row in range(2):
    axes[row, 0].set_ylabel("Latitude (°)", fontsize=5.5, color=INK)
for col in range(3):
    axes[1, col].set_xlabel("Longitude (°)", fontsize=5.5, color=INK)

# Layout and shared colorbar
fig.subplots_adjust(left=0.07, right=0.87, top=0.94, bottom=0.07, hspace=0.18, wspace=0.14)
cbar_ax = fig.add_axes([0.895, 0.12, 0.016, 0.76])
sm = ScalarMappable(cmap=imprint_div, norm=Normalize(vmin=vmin, vmax=vmax))
sm.set_array([])
cbar = fig.colorbar(sm, cax=cbar_ax)
cbar.set_label("Temp. Anomaly (°C)", fontsize=7, color=INK)
cbar.ax.tick_params(labelsize=6, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
