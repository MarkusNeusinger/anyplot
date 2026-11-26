"""anyplot.ai
hexbin-map-geographic: Hexagonal Binning Map
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-26
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Polygon
from matplotlib.path import Path


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Continuous colormap — imprint_seq, fields stops (colored cells fill the map)
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.368, "#009E73"), (0.582, "#4467A3"), (1.0, "#002850")]
    if THEME == "light"
    else [(0.0, "#00573D"), (0.467, "#009E73"), (1.0, "#CDD9FF")]
)
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", SEQ_FIELDS)

# Base map surface colors
WATER_BG = "#C8DFF0" if THEME == "light" else "#1C2D3A"
LAND_BG = "#E8E5DB" if THEME == "light" else "#282820"

# Constants
GRIDSIZE = 35  # hexagons across the map's width: detail vs. aggregation
# Map window (lon_min, lon_max, lat_min, lat_max) and simplified land outlines (lon, lat)
EXTENT = (-74.05, -73.70, 40.58, 40.90)
LAND = [
    # New Jersey, west of the Hudson
    [
        (-74.06, 40.57),
        (-74.04, 40.645),
        (-74.02, 40.70),
        (-74.025, 40.72),
        (-74.015, 40.745),
        (-74.0, 40.77),
        (-73.985, 40.80),
        (-73.96, 40.85),
        (-73.945, 40.89),
        (-73.94, 40.91),
        (-74.06, 40.91),
    ],
    # Manhattan
    [
        (-74.017, 40.703),
        (-74.012, 40.725),
        (-74.003, 40.745),
        (-73.997, 40.765),
        (-73.985, 40.79),
        (-73.972, 40.815),
        (-73.95, 40.845),
        (-73.93, 40.87),
        (-73.922, 40.87),
        (-73.928, 40.85),
        (-73.94, 40.825),
        (-73.955, 40.80),
        (-73.965, 40.785),
        (-73.972, 40.765),
        (-73.975, 40.745),
        (-73.972, 40.728),
        (-73.977, 40.712),
        (-73.997, 40.708),
    ],
    # The Bronx and the mainland to the north
    [
        (-73.93, 40.80),
        (-73.91, 40.80),
        (-73.795, 40.82),
        (-73.78, 40.9),
        (-73.93, 40.9),
        (-73.925, 40.87),
        (-73.935, 40.835),
    ],
    # Brooklyn and Queens on western Long Island
    [
        (-74.04, 40.645),
        (-74.015, 40.66),
        (-74.0, 40.69),
        (-73.99, 40.70),
        (-73.97, 40.705),
        (-73.955, 40.725),
        (-73.945, 40.74),
        (-73.925, 40.76),
        (-73.905, 40.785),
        (-73.88, 40.79),
        (-73.85, 40.795),
        (-73.79, 40.81),
        (-73.70, 40.80),
        (-73.70, 40.58),
        (-74.0, 40.58),
        (-74.04, 40.61),
    ],
]
LAND_PATHS = [Path(outline) for outline in LAND]
LANDMARKS = [("Manhattan", -73.985, 40.758), ("Brooklyn", -73.960, 40.680), ("Queens", -73.850, 40.730)]

# Columns: set these to your table's column names
LON = "Longitude"  # role: lon
LAT = "Latitude"  # role: lat
FARE = "Trip fare ($)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("trips.csv")
# NYC taxi pickup locations (5,000 simulated trips) with the fare of each trip
np.random.seed(42)
n_points = 5000

# Pickups start on land: draw extra candidates per cluster and keep the first n that fall inside a land outline
clusters = [  # (center lon, center lat, spread lon, spread lat, trips)
    (-73.985, 40.758, 0.015, 0.030, 2500),
    (-73.960, 40.680, 0.030, 0.040, 1500),
    (-73.850, 40.730, 0.040, 0.030, 1000),
]
lons, lats = [], []
for lon_c, lat_c, lon_sd, lat_sd, n_trips in clusters:
    cand = np.column_stack([np.random.normal(lon_c, lon_sd, n_trips * 4), np.random.normal(lat_c, lat_sd, n_trips * 4)])
    on_land = np.any([path.contains_points(cand) for path in LAND_PATHS], axis=0)
    lons.append(cand[on_land][:n_trips, 0])
    lats.append(cand[on_land][:n_trips, 1])

df = pd.DataFrame({LON: np.concatenate(lons), LAT: np.concatenate(lats), FARE: np.random.exponential(15, n_points) + 5})

# Plot — landscape 3200 × 1800 px
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

# Base map: water background + simplified land outlines
ax.set_facecolor(WATER_BG)
for outline in LAND:
    ax.add_patch(Polygon(outline, closed=True, facecolor=LAND_BG, edgecolor=INK_MUTED, linewidth=0.6, zorder=0))

# Hexbin: mean trip fare aggregated per hex cell
hb = ax.hexbin(
    df[LON],
    df[LAT],
    C=df[FARE],
    gridsize=GRIDSIZE,
    extent=EXTENT,
    reduce_C_function=np.mean,
    cmap=imprint_seq,
    alpha=0.65,
    edgecolors=INK_MUTED,
    linewidths=0.3,
    mincnt=1,
    zorder=2,
)

# Colorbar
cbar = fig.colorbar(hb, ax=ax, shrink=0.90, pad=0.02, aspect=28, fraction=0.030)
cbar.set_label(f"Mean {FARE}", fontsize=10, color=INK, labelpad=8)
cbar.ax.tick_params(labelsize=9, colors=INK_SOFT, labelcolor=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Axis limits and coordinate formatters
ax.set_xlim(EXTENT[0], EXTENT[1])
ax.set_ylim(EXTENT[2], EXTENT[3])
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{abs(x):.2f}°W"))
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, p: f"{y:.2f}°N"))

# Style
ax.set_xlabel(LON, fontsize=10, color=INK)
ax.set_ylabel(LAT, fontsize=10, color=INK)

title = "hexbin-map-geographic · python · matplotlib · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK, pad=10)

ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.grid(True, alpha=0.12, linestyle="--", color=INK, zorder=1, linewidth=0.5)
for spine in ax.spines.values():
    spine.set_color(INK_SOFT)
    spine.set_linewidth(0.5)

# Borough annotations, offset in points from each borough's center
for name, x, y in LANDMARKS:
    ax.annotate(
        name,
        xy=(x, y),
        xytext=(25, 19),
        textcoords="offset points",
        fontsize=8,
        fontweight="bold",
        color=INK,
        ha="left",
        bbox={
            "boxstyle": "round,pad=0.2",
            "facecolor": ELEVATED_BG,
            "alpha": 0.6,
            "edgecolor": INK_SOFT,
            "linewidth": 0.5,
        },
        zorder=5,
    )

# Layout — subplots_adjust controls padding; no bbox_inches='tight' in savefig
fig.subplots_adjust(left=0.10, right=0.92, top=0.92, bottom=0.12)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
