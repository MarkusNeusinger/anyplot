""" pyplots.ai
map-tile-background: Map with Tile Background
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import io
import math
import urllib.request

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


# Helper functions to convert lat/lon to tile coordinates
def lat_lon_to_tile(lat, lon, zoom):
    """Convert latitude/longitude to tile x, y at given zoom level."""
    n = 2**zoom
    x = int((lon + 180) / 360 * n)
    lat_rad = math.radians(lat)
    y = int((1 - math.asinh(math.tan(lat_rad)) / math.pi) / 2 * n)
    return x, y


def tile_to_lat_lon(x, y, zoom):
    """Convert tile coordinates to latitude/longitude (NW corner)."""
    n = 2**zoom
    lon = x / n * 360 - 180
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat = math.degrees(lat_rad)
    return lat, lon


def fetch_tile(x, y, zoom, source="osm"):
    """Fetch a single map tile from tile server."""
    if source == "osm":
        url = f"https://tile.openstreetmap.org/{zoom}/{x}/{y}.png"

    headers = {"User-Agent": "pyplots.ai/1.0 (https://pyplots.ai; visualization demo)"}
    req = urllib.request.Request(url, headers=headers)

    with urllib.request.urlopen(req, timeout=10) as response:
        return Image.open(io.BytesIO(response.read()))


def get_map_tiles(lat_min, lat_max, lon_min, lon_max, zoom=10):
    """Fetch and stitch map tiles for a bounding box."""
    # Get tile range
    x_min, y_max = lat_lon_to_tile(lat_min, lon_min, zoom)
    x_max, y_min = lat_lon_to_tile(lat_max, lon_max, zoom)

    # Calculate tile dimensions
    tiles_x = x_max - x_min + 1
    tiles_y = y_max - y_min + 1

    # Create blank image
    tile_size = 256
    full_image = Image.new("RGB", (tiles_x * tile_size, tiles_y * tile_size))

    # Fetch and stitch tiles
    for x in range(x_min, x_max + 1):
        for y in range(y_min, y_max + 1):
            tile = fetch_tile(x, y, zoom)
            pos_x = (x - x_min) * tile_size
            pos_y = (y - y_min) * tile_size
            full_image.paste(tile, (pos_x, pos_y))

    # Calculate geographic extent of stitched image
    nw_lat, nw_lon = tile_to_lat_lon(x_min, y_min, zoom)
    se_lat, se_lon = tile_to_lat_lon(x_max + 1, y_max + 1, zoom)

    extent = [nw_lon, se_lon, se_lat, nw_lat]
    return np.array(full_image), extent


# Data: Tourist attractions in Rome with visitor counts
np.random.seed(42)

locations = {
    "Colosseum": (41.8902, 12.4922, 7200),
    "Vatican Museums": (41.9065, 12.4536, 6800),
    "Trevi Fountain": (41.9009, 12.4833, 5500),
    "Pantheon": (41.8986, 12.4769, 4800),
    "Roman Forum": (41.8925, 12.4853, 4200),
    "St. Peter's Basilica": (41.9022, 12.4539, 6500),
    "Spanish Steps": (41.9060, 12.4828, 3800),
    "Piazza Navona": (41.8992, 12.4730, 3200),
    "Castel Sant'Angelo": (41.9031, 12.4663, 2800),
    "Villa Borghese": (41.9137, 12.4855, 2400),
    "Trastevere": (41.8867, 12.4692, 2100),
    "Campo de' Fiori": (41.8956, 12.4722, 1800),
}

lats = np.array([loc[0] for loc in locations.values()])
lons = np.array([loc[1] for loc in locations.values()])
visitors = np.array([loc[2] for loc in locations.values()])  # Daily visitors (thousands)
names = list(locations.keys())

# Calculate bounds with padding
lat_margin = 0.015
lon_margin = 0.025
lat_min, lat_max = lats.min() - lat_margin, lats.max() + lat_margin
lon_min, lon_max = lons.min() - lon_margin, lons.max() + lon_margin

# Fetch map tiles
zoom = 14
map_img, extent = get_map_tiles(lat_min, lat_max, lon_min, lon_max, zoom)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Display map background
ax.imshow(map_img, extent=extent, aspect="auto", zorder=0)

# Scale point sizes based on visitor counts
min_size = 150
max_size = 800
sizes = min_size + (visitors - visitors.min()) / (visitors.max() - visitors.min()) * (max_size - min_size)

# Plot data points with Python colors
scatter = ax.scatter(
    lons, lats, c=visitors, s=sizes, cmap="YlOrRd", alpha=0.85, edgecolors="white", linewidth=2.5, zorder=5
)

# Add colorbar
cbar = plt.colorbar(scatter, ax=ax, shrink=0.75, pad=0.02)
cbar.set_label("Daily Visitors (thousands)", fontsize=16)
cbar.ax.tick_params(labelsize=14)

# Set axis limits to data extent
ax.set_xlim(lon_min, lon_max)
ax.set_ylim(lat_min, lat_max)

# Labels and title
ax.set_xlabel("Longitude", fontsize=20)
ax.set_ylabel("Latitude", fontsize=20)
ax.set_title("map-tile-background · matplotlib · pyplots.ai", fontsize=24, pad=15)
ax.tick_params(axis="both", labelsize=14)

# Format tick labels as coordinates
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x:.3f}°E"))
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, p: f"{y:.3f}°N"))

# Add OpenStreetMap attribution (required by license)
ax.text(
    0.99,
    0.01,
    "© OpenStreetMap contributors",
    transform=ax.transAxes,
    fontsize=10,
    ha="right",
    va="bottom",
    bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8, edgecolor="#cccccc"),
    zorder=10,
)

# Add context annotation
ax.text(
    0.01,
    0.99,
    "Rome Tourist Attractions\nMarker size = visitor volume",
    transform=ax.transAxes,
    fontsize=12,
    ha="left",
    va="top",
    bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.85, edgecolor="#cccccc"),
    zorder=10,
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
