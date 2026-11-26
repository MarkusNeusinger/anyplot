"""anyplot.ai
hexbin-map-geographic: Hexagonal Binning Map
Library: seaborn 0.13.2 | Python 3.14.10
Quality: pending | Updated: 2026-11-26
"""

import os

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

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

# imprint_seq: Imprint sequential ramp (fields stops) for colored cells
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.368, "#009E73"), (0.582, "#4467A3"), (1.0, "#002850")]
    if THEME == "light"
    else [(0.0, "#00573D"), (0.467, "#009E73"), (1.0, "#CDD9FF")]
)
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", SEQ_FIELDS)

# Constants: Pacific Northwest base map (lon, lat), simplified coastlines and borders
OUTER_COAST = np.array(
    [
        (-124.45, 43.0),
        (-124.35, 43.7),
        (-124.1, 44.6),
        (-123.95, 45.5),
        (-124.0, 46.25),
        (-124.05, 46.7),
        (-124.15, 46.95),
        (-124.3, 47.3),
        (-124.65, 47.9),
        (-124.72, 48.38),
        (-124.0, 48.2),
        (-123.1, 48.12),
        (-122.75, 48.12),
    ]
)
PUGET_SOUND = np.array([(-122.75, 48.12), (-122.65, 47.85), (-122.55, 47.5), (-122.55, 47.25), (-122.9, 47.08)])
SOUND_EAST = np.array([(-122.9, 47.08), (-122.42, 47.27), (-122.38, 47.6), (-122.2, 47.98), (-122.5, 48.75)])
VANCOUVER_ISLAND = np.array(
    [
        (-126.5, 50.0),
        (-126.2, 49.75),
        (-125.4, 49.3),
        (-124.8, 48.85),
        (-124.0, 48.55),
        (-123.4, 48.4),
        (-123.4, 48.7),
        (-123.9, 49.2),
        (-124.9, 49.9),
        (-125.5, 50.3),
        (-126.5, 50.75),
    ]
)
BC_COAST = np.array([(-123.0, 49.0), (-123.2, 49.45), (-123.9, 50.0), (-124.8, 50.5), (-125.5, 51.0)])
BORDER_49N = np.array([(-123.0, 49.0), (-116.5, 49.0)])
WA_OR_BORDER = np.array(
    [
        (-124.0, 46.25),
        (-123.5, 46.15),
        (-122.9, 45.65),
        (-122.3, 45.55),
        (-121.5, 45.65),
        (-120.5, 45.75),
        (-119.7, 45.9),
        (-118.5, 46.0),
        (-116.9, 46.1),
    ]
)

# Columns
LONGITUDE = "Longitude (°W)"  # role: lon
LATITUDE = "Latitude (°N)"  # role: lat
RICHNESS = "Species Richness"  # role: value

# Data
# Simulated bird species observation locations in the Pacific Northwest
rng = np.random.default_rng(42)
n_points = 7000
lon = rng.normal(-121.5, 1.4, n_points)
lat = rng.normal(46.8, 1.1, n_points)

# Seattle urban birding hotspot (highest observer density)
idx1 = np.where(rng.random(n_points) < 0.22)[0]
lon[idx1] = rng.normal(-122.33, 0.10, len(idx1))
lat[idx1] = rng.normal(47.61, 0.08, len(idx1))

# Portland urban birding area
idx2 = np.where(rng.random(n_points) < 0.18)[0]
lon[idx2] = rng.normal(-122.68, 0.09, len(idx2))
lat[idx2] = rng.normal(45.52, 0.07, len(idx2))

# Cascade Range wilderness cluster
idx3 = np.where(rng.random(n_points) < 0.13)[0]
lon[idx3] = rng.normal(-121.2, 0.20, len(idx3))
lat[idx3] = rng.normal(47.1, 0.20, len(idx3))

# Olympic Peninsula coastal hotspot
idx4 = np.where(rng.random(n_points) < 0.10)[0]
lon[idx4] = rng.normal(-123.7, 0.18, len(idx4))
lat[idx4] = rng.normal(47.9, 0.20, len(idx4))

# Species richness score per observation (1-5); higher near urban birding hotspots
richness = rng.uniform(1.0, 3.0, n_points)
richness[idx1] += rng.uniform(1.5, 2.0, len(idx1))
richness[idx2] += rng.uniform(1.0, 1.5, len(idx2))
richness = np.clip(richness, 1.0, 5.0)

# Observations happen on land: east of the outer coast, south of the Strait of Juan de Fuca
# (west of Puget Sound) and south of the 49th parallel
coast_lon = np.interp(lat, OUTER_COAST[:, 1], OUTER_COAST[:, 0])
on_land = (lon > coast_lon + 0.08) & (lat < 49.0) & ((lat < 48.1) | (lon > -122.75))

df = pd.DataFrame({LONGITUDE: lon, LATITUDE: lat, RICHNESS: richness})[on_land].reset_index(drop=True)

# Plot
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

x_min, x_max = -126.5, -116.5
y_min, y_max = 43.0, 51.0
ax.set_xlim(x_min, x_max)
ax.set_ylim(y_min, y_max)
# Equirectangular map: one degree of longitude is cos(latitude) as long as one of latitude
lat_stretch = 1 / np.cos(np.radians((y_min + y_max) / 2))
ax.set_aspect(lat_stretch)

# Regular hexagons on screen: rows of cells follow the displayed height-to-width ratio
n_cols = 24
n_rows = round(n_cols * (y_max - y_min) * lat_stretch / (x_max - x_min) / np.sqrt(3))

# Mean richness per hexagon, translucent so the base map shows through
hexes = ax.hexbin(
    df[LONGITUDE],
    df[LATITUDE],
    C=df[RICHNESS],
    reduce_C_function=np.mean,
    gridsize=(n_cols, n_rows),
    extent=(x_min, x_max, y_min, y_max),
    mincnt=1,
    cmap=imprint_seq,
    alpha=0.85,
    edgecolors=PAGE_BG,
    linewidths=0.2,
    zorder=2,
)

# Base map above the cells
geo_kw = {"color": INK_SOFT, "alpha": 0.8, "lw": 1.1, "zorder": 3, "solid_capstyle": "round"}
for line in (OUTER_COAST, PUGET_SOUND, SOUND_EAST, VANCOUVER_ISLAND, BC_COAST):
    ax.plot(line[:, 0], line[:, 1], **geo_kw)
for line in (BORDER_49N, WA_OR_BORDER):
    ax.plot(line[:, 0], line[:, 1], linestyle="--", **{**geo_kw, "lw": 0.9})

# Labels sit on empty ground or open ocean; the page-colored outline keeps them legible
halo = [pe.withStroke(linewidth=2.5, foreground=PAGE_BG)]
ax.text(-118.0, 49.3, "CANADA", fontsize=8, color=INK_SOFT, ha="center", va="center", path_effects=halo, zorder=10)
ax.text(-117.5, 48.75, "WA", fontsize=8, color=INK_SOFT, ha="center", va="center", path_effects=halo, zorder=10)
ax.text(-118.8, 43.5, "OREGON", fontsize=8, color=INK_SOFT, ha="center", va="center", path_effects=halo, zorder=10)
ax.text(-125.5, 44.0, "Pacific Ocean", fontsize=8, color=INK_SOFT, ha="center", style="italic", zorder=10)

# City callouts from the open ocean, pointing at the two hotspots
arrow_kw = {"arrowstyle": "-", "color": INK_SOFT, "lw": 0.8, "shrinkA": 2, "shrinkB": 0}
ax.annotate(
    "Seattle",
    xy=(-122.5, 47.45),
    xytext=(-125.9, 46.9),
    fontsize=8,
    color=INK,
    ha="center",
    arrowprops=arrow_kw,
    zorder=10,
)
ax.annotate(
    "Portland",
    xy=(-122.8, 45.45),
    xytext=(-125.9, 45.0),
    fontsize=8,
    color=INK,
    ha="center",
    arrowprops=arrow_kw,
    zorder=10,
)

# Colorbar naming the statistic
cbar = fig.colorbar(hexes, ax=ax, shrink=0.6, pad=0.03, aspect=22)
cbar.set_label("Mean Species Richness", fontsize=10, color=INK, labelpad=6)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Style
ax.set_title("hexbin-map-geographic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(LONGITUDE, fontsize=10)
ax.set_ylabel(LATITUDE, fontsize=10)
ax.tick_params(axis="both", labelsize=8)
sns.despine(ax=ax)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
