""" anyplot.ai
map-projections: World Map with Different Projections
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 87/100 | Updated: 2026-11-26
"""

import os
import sys


# Remove this script's directory from sys.path to avoid shadowing the matplotlib package
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if p != "" and os.path.abspath(p) != _script_dir]
del _script_dir

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Map colors (theme-adaptive; semantic: land/ocean are not data series)
LAND_COLOR = "#E8E4D9" if THEME == "light" else "#3A3830"
OCEAN_COLOR = "#A8D5E5" if THEME == "light" else "#1A3348"
TISSOT_COLOR = "#009E73"  # Imprint palette position 1 (brand green)

# Projections to compare, each with its cell in a grid sized to the maps' aspect ratios:
# the square Mercator and Orthographic maps take a tall narrow column, the 2:1 maps are stacked
projections = [
    ("Mercator", ccrs.Mercator(), (slice(None), 0)),
    ("Robinson", ccrs.Robinson(), (0, 1)),
    ("Mollweide", ccrs.Mollweide(), (1, 1)),
    ("Orthographic", ccrs.Orthographic(central_longitude=0, central_latitude=30), (slice(None), 2)),
]

# Figure — 3200×1800 px (16:9)
fig = plt.figure(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
fig.suptitle("map-projections · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, y=0.98)
grid = fig.add_gridspec(
    2, 3, width_ratios=[1.3, 1.9, 1.1], left=0.05, right=0.98, top=0.88, bottom=0.04, hspace=0.2, wspace=0.14
)

for name, proj, cell in projections:
    ax = fig.add_subplot(grid[cell], projection=proj)
    ax.set_global()

    # Map features
    ax.add_feature(cfeature.OCEAN, facecolor=OCEAN_COLOR, zorder=0)
    ax.add_feature(cfeature.LAND, facecolor=LAND_COLOR, zorder=1)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.6, edgecolor=INK_SOFT, zorder=2)
    ax.add_feature(cfeature.BORDERS, linewidth=0.3, edgecolor=INK_SOFT, alpha=0.5, zorder=2)

    # Graticule with lat/lon labels where supported
    # Disable bottom labels for top-row subplots to prevent overlap with second-row titles
    labels = True if name in ("Mercator", "Robinson") else {"left": "y"}
    gl = ax.gridlines(draw_labels=labels, linewidth=0.5, color=INK_SOFT, alpha=0.4, linestyle="--")
    gl.top_labels = False
    gl.right_labels = False
    gl.bottom_labels = False
    gl.x_inline = False
    gl.xlabel_style = {"size": 8, "color": INK_MUTED}
    gl.ylabel_style = {"size": 8, "color": INK_MUTED}
    gl.xlocator = plt.FixedLocator(np.arange(-180, 181, 30))
    gl.ylocator = plt.FixedLocator(np.arange(-90, 91, 30))

    # Tissot indicatrices — visualise projection distortion of area/shape
    for lon in np.arange(-150, 180, 60):
        for lat in np.arange(-60, 90, 30):
            ax.tissot(
                rad_km=500,
                lons=lon,
                lats=lat,
                n_samples=64,
                facecolor=TISSOT_COLOR,
                edgecolor=TISSOT_COLOR,
                alpha=0.5 if THEME == "dark" else 0.4,
                linewidth=0.8,
                zorder=3,
            )

    ax.set_title(name, fontsize=10, fontweight="bold", color=INK, pad=6)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
