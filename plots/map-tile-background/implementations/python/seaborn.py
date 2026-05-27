""" anyplot.ai
map-tile-background: Map with Tile Background
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-27
"""

import io
import math
import os
import sys
import urllib.request


# Remove script directory from sys.path to prevent sibling .py files from
# shadowing installed packages (e.g. matplotlib.py → import matplotlib collision)
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _here]

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# imprint_seq colormap for temperature (single-polarity continuous data)
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

# Apply seaborn theme
sns.set_theme(style="white", rc={"figure.facecolor": PAGE_BG, "axes.facecolor": PAGE_BG, "text.color": INK})

# Data: Weather stations in the San Francisco Bay Area
np.random.seed(42)
stations_data = {
    "name": [
        "SF Downtown",
        "Oakland Airport",
        "San Jose",
        "Berkeley",
        "Fremont",
        "Palo Alto",
        "Hayward",
        "Richmond",
        "Concord",
        "Walnut Creek",
        "Livermore",
        "Redwood City",
        "Mountain View",
        "Sunnyvale",
        "Santa Clara",
    ],
    "lat": [
        37.7749,
        37.7213,
        37.3382,
        37.8716,
        37.5485,
        37.4419,
        37.6688,
        37.9358,
        37.9780,
        37.9101,
        37.6819,
        37.4852,
        37.3861,
        37.3688,
        37.3541,
    ],
    "lon": [
        -122.4194,
        -122.2208,
        -121.8863,
        -122.2727,
        -121.9886,
        -122.1430,
        -122.0808,
        -122.3477,
        -122.0311,
        -122.0652,
        -121.7680,
        -122.2364,
        -122.0839,
        -122.0363,
        -121.9552,
    ],
    "temperature": [18.5, 17.2, 22.1, 16.8, 20.5, 19.3, 18.9, 15.6, 24.2, 23.1, 25.8, 18.7, 21.4, 22.0, 21.8],
}
df = pd.DataFrame(stations_data)

# Map bounds with padding
lat_margin = 0.15
lon_margin = 0.2
min_lat = df["lat"].min() - lat_margin
max_lat = df["lat"].max() + lat_margin
min_lon = df["lon"].min() - lon_margin
max_lon = df["lon"].max() + lon_margin

# Tile parameters (Web Mercator, zoom=10)
zoom = 10
tile_size = 256
n_tiles = 2**zoom

x_min = int((min_lon + 180.0) / 360.0 * n_tiles)
x_max = int((max_lon + 180.0) / 360.0 * n_tiles)
y_min = int((1.0 - math.asinh(math.tan(math.radians(max_lat))) / math.pi) / 2.0 * n_tiles)
y_max = int((1.0 - math.asinh(math.tan(math.radians(min_lat))) / math.pi) / 2.0 * n_tiles)

tiles_x = x_max - x_min + 1
tiles_y = y_max - y_min + 1

# Fetch and stitch tiles from OpenStreetMap
stitched = Image.new("RGB", (tiles_x * tile_size, tiles_y * tile_size))
headers = {"User-Agent": "anyplot.ai/1.0 (educational visualization)"}

for tx in range(x_min, x_max + 1):
    for ty in range(y_min, y_max + 1):
        url = f"https://tile.openstreetmap.org/{zoom}/{tx}/{ty}.png"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                tile = Image.open(io.BytesIO(response.read()))
        except Exception:
            tile = Image.new("RGB", (256, 256), (220, 220, 220))
        px = (tx - x_min) * tile_size
        py = (ty - y_min) * tile_size
        stitched.paste(tile, (px, py))

# Actual bounds of stitched tiles
actual_min_lon = x_min / n_tiles * 360.0 - 180.0
actual_max_lon = (x_max + 1) / n_tiles * 360.0 - 180.0
actual_max_lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y_min / n_tiles))))
actual_min_lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y_max + 1) / n_tiles))))

# Convert station coordinates to pixel positions (Web Mercator projection)
pixel_x_list = []
pixel_y_list = []
for _, row in df.iterrows():
    x_pct = (row["lon"] - actual_min_lon) / (actual_max_lon - actual_min_lon)
    lat_rad = math.radians(row["lat"])
    y_merc = math.log(math.tan(math.pi / 4 + lat_rad / 2))
    y_min_merc = math.log(math.tan(math.pi / 4 + math.radians(actual_min_lat) / 2))
    y_max_merc = math.log(math.tan(math.pi / 4 + math.radians(actual_max_lat) / 2))
    y_pct = 1 - (y_merc - y_min_merc) / (y_max_merc - y_min_merc)
    pixel_x_list.append(x_pct * stitched.width)
    pixel_y_list.append(y_pct * stitched.height)

df["pixel_x"] = pixel_x_list
df["pixel_y"] = pixel_y_list

t_min, t_max = df["temperature"].min(), df["temperature"].max()

# Plot — canonical 3200×1800 canvas
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Display tile background
ax.imshow(stitched, extent=[0, stitched.width, stitched.height, 0], aspect="auto", zorder=0)

# Plot weather stations: dual encoding (size + color) for temperature
sns.scatterplot(
    data=df,
    x="pixel_x",
    y="pixel_y",
    size="temperature",
    sizes=(150, 600),
    hue="temperature",
    palette=imprint_seq,
    hue_norm=(t_min, t_max),
    edgecolor="white",
    linewidth=1.5,
    alpha=0.90,
    ax=ax,
    legend=False,
    zorder=2,
)

# Station labels with per-station offsets to prevent overlap in dense clusters
label_offsets = {
    "Mountain View": (-70, -14),
    "Sunnyvale": (8, -14),
    "Santa Clara": (8, 8),
    "San Jose": (8, 8),
    "Palo Alto": (-65, 8),
    "Redwood City": (-72, -12),
    "Fremont": (8, -12),
    "Livermore": (8, 8),
}
default_offset = (8, -8)

for _, row in df.iterrows():
    offx, offy = label_offsets.get(row["name"], default_offset)
    ax.annotate(
        row["name"],
        (row["pixel_x"], row["pixel_y"]),
        xytext=(offx, offy),
        textcoords="offset points",
        fontsize=7,
        color=INK,
        fontweight="bold",
        bbox={"boxstyle": "round,pad=0.2", "facecolor": ELEVATED_BG, "edgecolor": "none", "alpha": 0.85},
        zorder=3,
    )

# Colorbar for temperature
norm = plt.Normalize(vmin=t_min, vmax=t_max)
sm = plt.cm.ScalarMappable(cmap=imprint_seq, norm=norm)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, shrink=0.55, pad=0.02, aspect=20)
cbar.set_label("Temperature (°C)", fontsize=10, color=INK, labelpad=10)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Hide map axes and spines
ax.set_xticks([])
ax.set_yticks([])
ax.set_xlabel("")
ax.set_ylabel("")
for spine in ax.spines.values():
    spine.set_visible(False)

# Title — fontsize scaled for 79-char string: round(12 * 67/79) = 10pt
title = "Bay Area Weather Stations · map-tile-background · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=10, fontweight="medium", color=INK, pad=10)

# OSM attribution (required by license)
ax.text(
    0.99,
    0.01,
    "© OpenStreetMap contributors",
    transform=ax.transAxes,
    fontsize=6,
    ha="right",
    va="bottom",
    color=INK,
    bbox={"boxstyle": "round,pad=0.3", "facecolor": ELEVATED_BG, "edgecolor": "none", "alpha": 0.85},
    zorder=4,
)

plt.tight_layout()
plt.savefig(os.path.join(_here, f"plot-{THEME}.png"), dpi=400)
