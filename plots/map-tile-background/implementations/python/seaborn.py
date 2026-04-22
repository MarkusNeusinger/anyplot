""" pyplots.ai
map-tile-background: Map with Tile Background
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import io
import math
import urllib.request

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from PIL import Image


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

# Calculate bounds with padding
lat_margin = 0.15
lon_margin = 0.2
min_lat = df["lat"].min() - lat_margin
max_lat = df["lat"].max() + lat_margin
min_lon = df["lon"].min() - lon_margin
max_lon = df["lon"].max() + lon_margin

# Tile parameters
zoom = 10  # Good detail for city-level view
tile_size = 256
n_tiles = 2**zoom

# Convert bounds to tile coordinates (Web Mercator)
x_min = int((min_lon + 180.0) / 360.0 * n_tiles)
x_max = int((max_lon + 180.0) / 360.0 * n_tiles)
y_min = int((1.0 - math.asinh(math.tan(math.radians(max_lat))) / math.pi) / 2.0 * n_tiles)
y_max = int((1.0 - math.asinh(math.tan(math.radians(min_lat))) / math.pi) / 2.0 * n_tiles)

tiles_x = x_max - x_min + 1
tiles_y = y_max - y_min + 1

# Fetch and stitch tiles from OpenStreetMap
stitched = Image.new("RGB", (tiles_x * tile_size, tiles_y * tile_size))
headers = {"User-Agent": "pyplots.ai/1.0 (educational visualization)"}

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

# Calculate actual bounds of stitched tiles
actual_min_lon = x_min / n_tiles * 360.0 - 180.0
actual_max_lon = (x_max + 1) / n_tiles * 360.0 - 180.0
actual_max_lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y_min / n_tiles))))
actual_min_lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y_max + 1) / n_tiles))))

# Convert data points to pixel coordinates (Web Mercator projection)
pixel_x_list = []
pixel_y_list = []
for _, row in df.iterrows():
    # X coordinate (linear in longitude)
    x_pct = (row["lon"] - actual_min_lon) / (actual_max_lon - actual_min_lon)

    # Y coordinate (Mercator projection)
    lat_rad = math.radians(row["lat"])
    y_merc = math.log(math.tan(math.pi / 4 + lat_rad / 2))
    y_min_merc = math.log(math.tan(math.pi / 4 + math.radians(actual_min_lat) / 2))
    y_max_merc = math.log(math.tan(math.pi / 4 + math.radians(actual_max_lat) / 2))
    y_pct = 1 - (y_merc - y_min_merc) / (y_max_merc - y_min_merc)

    pixel_x_list.append(x_pct * stitched.width)
    pixel_y_list.append(y_pct * stitched.height)

df["pixel_x"] = pixel_x_list
df["pixel_y"] = pixel_y_list

# Set seaborn style
sns.set_theme(style="white")

# Create figure matching tile image aspect ratio
fig_width = 16
fig_height = fig_width * stitched.height / stitched.width
fig, ax = plt.subplots(figsize=(fig_width, fig_height))

# Display tile background
ax.imshow(stitched, extent=[0, stitched.width, stitched.height, 0], aspect="auto", zorder=0)

# Plot data points with seaborn
sns.scatterplot(
    data=df,
    x="pixel_x",
    y="pixel_y",
    size="temperature",
    hue="temperature",
    sizes=(200, 800),
    palette="coolwarm",
    edgecolor="white",
    linewidth=2,
    alpha=0.85,
    ax=ax,
    legend=False,
    zorder=2,
)

# Add station labels
for _, row in df.iterrows():
    ax.annotate(
        row["name"],
        (row["pixel_x"], row["pixel_y"]),
        xytext=(8, -8),
        textcoords="offset points",
        fontsize=11,
        color="#222222",
        fontweight="bold",
        bbox={"boxstyle": "round,pad=0.2", "facecolor": "white", "edgecolor": "none", "alpha": 0.8},
        zorder=3,
    )

# Create colorbar for temperature
sm = plt.cm.ScalarMappable(
    cmap="coolwarm", norm=plt.Normalize(vmin=df["temperature"].min(), vmax=df["temperature"].max())
)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, shrink=0.6, pad=0.02, aspect=25)
cbar.set_label("Temperature (°C)", fontsize=18, labelpad=15)
cbar.ax.tick_params(labelsize=14)

# Hide axes (map has its own reference)
ax.set_xticks([])
ax.set_yticks([])
ax.set_xlabel("")
ax.set_ylabel("")

# Title
ax.set_title(
    "Bay Area Weather Stations · map-tile-background · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20
)

# OpenStreetMap attribution (required by license)
ax.text(
    0.99,
    0.01,
    "© OpenStreetMap contributors",
    transform=ax.transAxes,
    fontsize=10,
    ha="right",
    va="bottom",
    color="#333333",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "none", "alpha": 0.8},
    zorder=4,
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
