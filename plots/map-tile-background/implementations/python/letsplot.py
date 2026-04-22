""" pyplots.ai
map-tile-background: Map with Tile Background
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-20
"""

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_rect,
    element_text,
    geom_livemap,
    geom_point,
    geom_polygon,
    geom_rect,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_size,
    theme,
    theme_void,
    tilesets,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data: European city landmarks with annual visitor counts (thousands)
cities_data = {
    "city": [
        "Paris",
        "London",
        "Berlin",
        "Rome",
        "Madrid",
        "Amsterdam",
        "Vienna",
        "Prague",
        "Barcelona",
        "Munich",
        "Brussels",
        "Zurich",
        "Milan",
        "Dublin",
        "Copenhagen",
        "Stockholm",
        "Oslo",
        "Helsinki",
        "Warsaw",
        "Budapest",
    ],
    "lat": [
        48.86,
        51.51,
        52.52,
        41.90,
        40.42,
        52.37,
        48.21,
        50.08,
        41.39,
        48.14,
        50.85,
        47.38,
        45.46,
        53.35,
        55.68,
        59.33,
        59.91,
        60.17,
        52.23,
        47.50,
    ],
    "lon": [
        2.35,
        -0.13,
        13.40,
        12.50,
        -3.70,
        4.90,
        16.37,
        14.44,
        2.17,
        11.58,
        4.35,
        8.54,
        9.19,
        -6.26,
        12.57,
        18.07,
        10.75,
        24.94,
        21.01,
        19.04,
    ],
    "visitors": [
        38000,
        32000,
        14000,
        17000,
        12000,
        9000,
        8000,
        9500,
        12000,
        8500,
        5500,
        4000,
        8000,
        6000,
        4500,
        5000,
        3500,
        3000,
        4000,
        5500,
    ],
}

df = pd.DataFrame(cities_data)

# ============================================================
# INTERACTIVE HTML VERSION: Uses geom_livemap with real tiles
# ============================================================
# Configure CARTO Positron tiles for clean basemap
plot_interactive = (
    ggplot()
    + geom_livemap(
        location=[-12, 35, 32, 72],  # Europe bounding box [lon_min, lat_min, lon_max, lat_max]
        zoom=4,
        tiles=tilesets.CARTO_POSITRON,  # Real tile provider
    )
    + geom_point(
        aes(x="lon", y="lat", size="visitors"),
        data=df,
        color="#306998",
        fill="#FFD43B",
        alpha=0.85,
        shape=21,
        stroke=1.5,
        tooltips=layer_tooltips().title("@city").line("Visitors|@visitors K/year"),
    )
    + scale_size(range=[6, 22], name="Visitors (thousands)")
    + labs(title="European Tourism · map-tile-background · letsplot · pyplots.ai")
    + ggsize(1600, 900)
    + theme(
        plot_title=element_text(size=24, face="bold"),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        legend_position="right",
        plot_inset=0,  # Remove livemap border inset
    )
)

# Save interactive HTML with real tile background
ggsave(plot_interactive, "plot.html", path=".")

# ============================================================
# STATIC PNG VERSION: Simulated tile appearance for export
# ============================================================
# Tile-style basemap: Create grid cells to simulate map tile appearance
tiles = []
tile_size = 5  # 5-degree tiles
for lon in range(-15, 35, tile_size):
    for lat in range(35, 75, tile_size):
        tiles.append({"xmin": lon, "xmax": lon + tile_size, "ymin": lat, "ymax": lat + tile_size})
df_tiles = pd.DataFrame(tiles)

# European coastline approximation (styled like vector tiles)
# Mainland Europe
europe_main = pd.DataFrame(
    {
        "lon": [
            -10,
            -9,
            -8,
            -5,
            -2,
            0,
            3,
            5,
            8,
            10,
            12,
            15,
            18,
            20,
            22,
            25,
            28,
            30,
            30,
            28,
            25,
            22,
            20,
            18,
            15,
            12,
            10,
            8,
            5,
            3,
            0,
            -3,
            -5,
            -8,
            -10,
        ],
        "lat": [
            36,
            37,
            40,
            43,
            44,
            46,
            47,
            48,
            49,
            50,
            51,
            52,
            55,
            58,
            60,
            62,
            65,
            68,
            70,
            70,
            70,
            70,
            68,
            65,
            60,
            55,
            52,
            50,
            48,
            47,
            45,
            42,
            40,
            37,
            36,
        ],
        "region": ["Europe_Main"] * 35,
    }
)

# Scandinavia (Norway/Sweden/Finland)
scandinavia = pd.DataFrame(
    {
        "lon": [5, 8, 10, 12, 15, 18, 22, 25, 28, 30, 28, 25, 22, 18, 15, 12, 10, 8, 5],
        "lat": [58, 58, 59, 60, 62, 65, 68, 70, 70, 68, 65, 62, 60, 58, 57, 56, 56, 57, 58],
        "region": ["Scandinavia"] * 19,
    }
)

# British Isles (Great Britain)
britain = pd.DataFrame(
    {
        "lon": [-6, -5, -4, -3, -1, 0, 1, 2, 1, 0, -1, -3, -4, -5, -6],
        "lat": [50, 50, 51, 51, 52, 53, 54, 55, 56, 57, 58, 58, 56, 54, 50],
        "region": ["Britain"] * 15,
    }
)

# Ireland
ireland = pd.DataFrame(
    {"lon": [-10, -9, -7, -6, -6, -7, -9, -10], "lat": [52, 53, 55, 54, 52, 51, 51, 52], "region": ["Ireland"] * 8}
)

# Italy
italy = pd.DataFrame(
    {
        "lon": [8, 10, 12, 14, 16, 18, 18, 16, 14, 12, 10, 8],
        "lat": [44, 44, 42, 40, 38, 40, 42, 44, 45, 46, 46, 44],
        "region": ["Italy"] * 12,
    }
)

# Greece/Balkans
balkans = pd.DataFrame(
    {
        "lon": [20, 22, 24, 26, 28, 28, 26, 24, 22, 20],
        "lat": [36, 37, 38, 40, 42, 45, 44, 42, 40, 36],
        "region": ["Balkans"] * 10,
    }
)

df_land = pd.concat([europe_main, scandinavia, britain, ireland, italy, balkans], ignore_index=True)

# Create static map with tile-simulated background for PNG export
plot_static = (
    ggplot()
    # Layer 1: Tile grid background (simulates tile mosaic like CARTO Positron)
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        data=df_tiles,
        fill="#F2F2F0",  # Light gray - CARTO Positron style
        color="#E0E0E0",  # Subtle tile borders
        size=0.2,
        alpha=0.9,
    )
    # Layer 2: Land mass polygons (styled like vector tiles)
    + geom_polygon(
        aes(x="lon", y="lat", group="region"),
        data=df_land,
        fill="#E8E5DB",  # Tan/beige for land (tile style)
        color="#C0B8A8",  # Darker outline
        size=0.6,
        alpha=0.95,
    )
    # Layer 3: City markers with visitor data
    + geom_point(
        aes(x="lon", y="lat", size="visitors"),
        data=df,
        color="#306998",
        fill="#FFD43B",
        alpha=0.85,
        shape=21,
        stroke=1.5,
        tooltips=layer_tooltips().title("@city").line("Visitors|@visitors K/year"),
    )
    + scale_size(range=[6, 22], name="Visitors (thousands)")
    + labs(
        title="European Tourism · map-tile-background · letsplot · pyplots.ai",
        caption="Map tiles simulated (CARTO Positron style) | © OpenStreetMap contributors",
    )
    + ggsize(1600, 900)
    + theme_void()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        plot_caption=element_text(size=12, color="#666666"),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        legend_position="right",
        plot_background=element_rect(fill="#F8F8F6"),
    )
)

# Save PNG (scale 3x for 4800 x 2700 px)
ggsave(plot_static, "plot.png", path=".", scale=3)
