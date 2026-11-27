""" anyplot.ai
hexbin-map-geographic: Hexagonal Binning Map
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-27
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap


# Theme tokens
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
        "grid.color": INK,
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# imprint_seq: Imprint sequential ramp (fields stops) for colored cells
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.369, "#009E73"), (0.803, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#404C02"), (0.487, "#009E73"), (1.0, "#CDD9FF")]
)
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", SEQ_FIELDS)

# Constants
# Pacific coastline (south to north) and the sound, island and border lines of the base map
coast = np.array(
    [
        (-124.4, 43.0),
        (-124.1, 44.6),
        (-123.95, 46.0),
        (-124.05, 46.7),
        (-124.15, 46.95),
        (-124.4, 47.5),
        (-124.7, 48.0),
        (-124.73, 48.38),
    ]
)
strait = np.array([(-124.73, 48.38), (-123.4, 48.12), (-122.75, 48.12)])
puget = np.array([(-122.75, 48.12), (-122.45, 47.85), (-122.4, 47.55), (-122.45, 47.25), (-122.9, 47.05)])
island_south = np.array([(-123.4, 48.4), (-124.4, 48.55), (-125.2, 48.9), (-126.0, 49.5), (-126.5, 50.0)])
island_east = np.array([(-123.4, 48.4), (-123.5, 48.75), (-124.2, 49.3), (-125.0, 50.0), (-125.5, 50.5)])
border_us_ca = np.array([(-123.0, 49.0), (-116.5, 49.0)])
border_wa_or = np.array(
    [
        (-124.0, 46.25),
        (-123.5, 46.1),
        (-122.9, 45.65),
        (-122.3, 45.55),
        (-121.5, 45.65),
        (-120.5, 45.75),
        (-119.7, 45.95),
        (-118.5, 46.0),
        (-116.9, 46.1),
    ]
)

# Columns
LONGITUDE = "Longitude"  # role: lon
LATITUDE = "Latitude"  # role: lat
RICHNESS = "Species Richness"  # role: value

# Data
# Simulated bird species observation locations in Pacific Northwest
np.random.seed(42)
n_points = 7000
center_lon, center_lat = -121.5, 46.8
lon = np.random.normal(center_lon, 1.4, n_points)
lat = np.random.normal(center_lat, 1.1, n_points)

# Seattle urban birding hotspot (highest observer density)
idx1 = np.where(np.random.random(n_points) < 0.22)[0]
lon[idx1] = np.random.normal(-122.33, 0.10, len(idx1))
lat[idx1] = np.random.normal(47.61, 0.08, len(idx1))

# Portland urban birding area
idx2 = np.where(np.random.random(n_points) < 0.18)[0]
lon[idx2] = np.random.normal(-122.68, 0.09, len(idx2))
lat[idx2] = np.random.normal(45.52, 0.07, len(idx2))

# Cascade Range wilderness cluster
idx3 = np.where(np.random.random(n_points) < 0.13)[0]
lon[idx3] = np.random.normal(-121.2, 0.20, len(idx3))
lat[idx3] = np.random.normal(47.1, 0.20, len(idx3))

# Olympic Peninsula coastal hotspot
idx4 = np.where(np.random.random(n_points) < 0.10)[0]
lon[idx4] = np.random.normal(-123.7, 0.18, len(idx4))
lat[idx4] = np.random.normal(47.9, 0.20, len(idx4))

# Species richness score per observation (1–5); higher near urban birding hotspots.
# Demonstrates mean aggregation — switch reduce_C_function=np.sum for sum aggregation.
richness = np.random.uniform(1.0, 3.0, n_points)
richness[idx1] += np.random.uniform(1.5, 2.0, len(idx1))  # Seattle: high richness
richness[idx2] += np.random.uniform(1.0, 1.5, len(idx2))  # Portland: moderate-high
richness = np.clip(richness, 1.0, 5.0)

df = pd.DataFrame({LONGITUDE: lon, LATITUDE: lat, RICHNESS: richness})

# Keep observations on land: east of the coastline at their latitude
df = df[df[LONGITUDE] > np.interp(df[LATITUDE], coast[:, 1], coast[:, 0]) + 0.05]

# Plot
# Square canvas: 6 in x 6 in at 400 dpi = 2400 x 2400 px
fig, ax = plt.subplots(figsize=(6, 6), dpi=400)
fig.patch.set_facecolor(PAGE_BG)
ax.set_facecolor(PAGE_BG)

x_min, x_max = -126.5, -116.5
y_min, y_max = 43.0, 51.0
ax.set_xlim(x_min, x_max)
ax.set_ylim(y_min, y_max)
# Longitude degrees shrink with latitude: scale y so the map is not stretched
aspect = 1 / np.cos(np.radians(df[LATITUDE].mean()))
ax.set_aspect(aspect)

# Regular hexagons on screen: rows follow from the aspect-corrected extent
grid_x = 28
grid_y = round(grid_x * (y_max - y_min) * aspect / (x_max - x_min) / np.sqrt(3))

# Mean aggregation per hexbin cell (count: omit C/reduce_C_function; sum: np.sum)
hb = ax.hexbin(
    df[LONGITUDE],
    df[LATITUDE],
    C=df[RICHNESS],
    reduce_C_function=np.mean,
    gridsize=(grid_x, grid_y),
    extent=(x_min, x_max, y_min, y_max),
    mincnt=1,
    cmap=imprint_seq,
    alpha=0.85,
    edgecolors=PAGE_BG,
    linewidths=0.15,
    zorder=2,
)

# Base map drawn over the translucent cells
geo_kw = {"color": INK_SOFT, "lw": 1.1, "zorder": 3, "solid_capstyle": "round"}
for line in (coast, strait, puget, island_south, island_east):
    ax.plot(line[:, 0], line[:, 1], **geo_kw)
for line in (border_us_ca, border_wa_or):
    ax.plot(line[:, 0], line[:, 1], linestyle="--", **geo_kw)

# Labels sit on empty ground, cities with a leader to their hotspot
ax.text(-118.0, 50.4, "Canada", fontsize=9, color=INK_SOFT, ha="center", va="bottom")
ax.text(-116.7, 48.3, "WA", fontsize=9, color=INK_SOFT, ha="right", fontweight="medium")
ax.text(-116.7, 44.3, "OR", fontsize=9, color=INK_SOFT, ha="right", fontweight="medium")
leader = {"arrowstyle": "-", "color": INK_SOFT, "lw": 0.8, "shrinkA": 1, "shrinkB": 2}
city_kw = {"fontsize": 8, "color": INK, "fontstyle": "italic", "ha": "left", "va": "center", "arrowprops": leader}
ax.annotate("Seattle", xy=(-122.33, 47.61), xytext=(-126.2, 47.2), **city_kw)
ax.annotate("Portland", xy=(-122.68, 45.52), xytext=(-126.2, 44.9), **city_kw)

# Spines
sns.despine(ax=ax)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

# Axis labels and ticks
ax.set_xlabel("Longitude (°W)", fontsize=10, color=INK)
ax.set_ylabel("Latitude (°N)", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

# Colorbar
cbar = fig.colorbar(hb, ax=ax, shrink=0.6, pad=0.03, aspect=18)
cbar.set_label("Mean Species Richness", fontsize=9, color=INK, labelpad=6)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Title
title = "hexbin-map-geographic · python · seaborn · anyplot.ai"
n = len(title)
title_fontsize = max(8, round(12 * (67 / n if n > 67 else 1.0)))
ax.set_title(title, fontsize=title_fontsize, color=INK, fontweight="medium")

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
