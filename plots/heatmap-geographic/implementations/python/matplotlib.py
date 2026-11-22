"""anyplot.ai
heatmap-geographic: Geographic Heatmap for Spatial Density
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-19
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

# Imprint palette: sequential map built from positions 1 and 3
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]])

# Constants
GRID_RESOLUTION = 150  # cells per axis of the density grid
SIGMA = 3  # Gaussian smoothing radius in grid cells (KDE bandwidth)
MIN_DENSITY_SHARE = 0.06  # cells below this share of the peak stay transparent
# Simplified California outline (lon, lat): Pacific coast, then the eastern border back north
COAST = [
    (-124.2, 41.9),
    (-124.4, 40.4),
    (-123.8, 39.4),
    (-123.0, 38.3),
    (-122.5, 37.8),
    (-122.4, 37.2),
    (-121.9, 36.6),
    (-121.3, 35.7),
    (-120.7, 35.1),
    (-120.6, 34.5),
    (-119.3, 34.3),
    (-118.5, 34.0),
    (-118.4, 33.8),
    (-117.9, 33.6),
    (-117.3, 33.0),
    (-117.1, 32.55),
]
BORDER = [
    (-117.1, 32.55),
    (-114.7, 32.7),
    (-114.5, 33.9),
    (-114.7, 35.0),
    (-120.0, 39.0),
    (-120.0, 42.0),
    (-124.2, 41.9),
]

# Columns: set these to your table's column names
LATITUDE = "Latitude"  # role: latitude
LONGITUDE = "Longitude"  # role: longitude
AQI = "Air Quality Index"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("sensors.csv")
rng = np.random.default_rng(42)
n_points = 500
clusters = [  # (lat, lon, lat spread, lon spread, share of stations)
    (36.5, -121.5, 0.8, 0.5, 1 / 3),
    (34.0, -118.0, 0.6, 0.7, 1 / 3),
    (38.5, -122.5, 0.5, 0.4, 1 / 3),
]
parts = []
for lat, lon, lat_sd, lon_sd, share in clusters:
    n = round(n_points * share)
    parts.append(pd.DataFrame({LATITUDE: rng.normal(lat, lat_sd, n), LONGITUDE: rng.normal(lon, lon_sd, n)}))
df = pd.concat(parts, ignore_index=True)
df[AQI] = np.clip(rng.gamma(shape=2.5, scale=28, size=len(df)), 5, 150)

# Plot: reads only df and the constants above
lon_min, lon_max = -125.0, -114.0  # map extent (California)
lat_min, lat_max = 32.5, 42.0

# Weighted 2D histogram, smoothed with a Gaussian kernel (KDE approximation)
heatmap, _, _ = np.histogram2d(
    df[LONGITUDE],
    df[LATITUDE],
    bins=[np.linspace(lon_min, lon_max, GRID_RESOLUTION), np.linspace(lat_min, lat_max, GRID_RESOLUTION)],
    weights=df[AQI],
)
half = int(3 * SIGMA)
kernel = np.exp(-(np.arange(-half, half + 1) ** 2) / (2 * SIGMA**2))
kernel /= kernel.sum()
smooth = np.apply_along_axis(lambda v: np.convolve(v, kernel, mode="same"), 0, heatmap)
smooth = np.apply_along_axis(lambda v: np.convolve(v, kernel, mode="same"), 1, smooth)
masked = np.ma.masked_where(smooth < MIN_DENSITY_SHARE * smooth.max(), smooth)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

im = ax.imshow(
    masked.T,
    extent=[lon_min, lon_max, lat_min, lat_max],
    origin="lower",
    aspect="auto",
    cmap=imprint_seq,
    alpha=0.8,
    interpolation="bilinear",
    zorder=2,
)

coast_x, coast_y = zip(*COAST, strict=True)
border_x, border_y = zip(*BORDER, strict=True)
ax.plot(coast_x, coast_y, color=INK_SOFT, linewidth=1.4, label="Coastline", zorder=3)
ax.plot(border_x, border_y, color=INK_SOFT, linewidth=1.4, linestyle=(0, (4, 2)), label="State border", zorder=3)
ax.scatter(df[LONGITUDE], df[LATITUDE], s=5, color=INK, alpha=0.35, edgecolors="none", label="Sensor", zorder=4)

cbar = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
cbar.set_label(f"{AQI} (weighted density)", fontsize=10, color=INK)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Style
ax.set_title("heatmap-geographic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(LONGITUDE, fontsize=10, color=INK)
ax.set_ylabel(LATITUDE, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.set_xlim(lon_min, lon_max)
ax.set_ylim(lat_min, lat_max)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(INK_SOFT)
ax.grid(True, alpha=0.12, color=INK, linewidth=0.6, zorder=1)

leg = ax.legend(loc="lower left", fontsize=8)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.subplots_adjust(left=0.08, right=0.97, top=0.92, bottom=0.11)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
