"""anyplot.ai
map-tile-background: Map with Tile Background
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-05-27
"""

import os

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

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"  # anyplot palette position 1 — ALWAYS first series

# Tile and land polygon colors adapt to theme
TILE_BG = "#E8E8E6" if THEME == "light" else "#2A2A27"
TILE_BORDER = "#D0D0CE" if THEME == "light" else "#3A3A37"
LAND_FILL = "#D5D1C8" if THEME == "light" else "#38382F"
LAND_BORDER = "#B5B1A4" if THEME == "light" else "#4A4A40"

# Data: European cities with annual visitor counts (thousands)
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

TITLE = "map-tile-background · python · letsplot · anyplot.ai"

# Interactive HTML version — geom_livemap with real tile provider
map_tiles = tilesets.LETS_PLOT_DARK if THEME == "dark" else tilesets.CARTO_POSITRON

plot_interactive = (
    ggplot()
    + geom_livemap(location=[-12, 35, 32, 72], zoom=4, tiles=map_tiles)
    + geom_point(
        aes(x="lon", y="lat", size="visitors"),
        data=df,
        fill=BRAND,
        color=PAGE_BG,
        alpha=0.85,
        shape=21,
        stroke=2,
        tooltips=layer_tooltips().title("@city").line("Visitors|@visitors K/year"),
    )
    + scale_size(range=[6, 22], name="Visitors (thousands)")
    + labs(title=TITLE)
    + ggsize(800, 450)
    + theme(
        plot_title=element_text(size=16, color=INK),
        legend_title=element_text(size=10, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_position="right",
    )
)

ggsave(plot_interactive, f"plot-{THEME}.html", path=".")

# Static PNG version — simulated tile-style background for raster export
tiles_rows = []
tile_size = 5
for lon_val in range(-15, 35, tile_size):
    for lat_val in range(35, 75, tile_size):
        tiles_rows.append({"xmin": lon_val, "xmax": lon_val + tile_size, "ymin": lat_val, "ymax": lat_val + tile_size})
df_tiles = pd.DataFrame(tiles_rows)

# Approximate European landmass polygons (CARTO Positron–style outlines)
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
scandinavia = pd.DataFrame(
    {
        "lon": [5, 8, 10, 12, 15, 18, 22, 25, 28, 30, 28, 25, 22, 18, 15, 12, 10, 8, 5],
        "lat": [58, 58, 59, 60, 62, 65, 68, 70, 70, 68, 65, 62, 60, 58, 57, 56, 56, 57, 58],
        "region": ["Scandinavia"] * 19,
    }
)
britain = pd.DataFrame(
    {
        "lon": [-6, -5, -4, -3, -1, 0, 1, 2, 1, 0, -1, -3, -4, -5, -6],
        "lat": [50, 50, 51, 51, 52, 53, 54, 55, 56, 57, 58, 58, 56, 54, 50],
        "region": ["Britain"] * 15,
    }
)
ireland = pd.DataFrame(
    {"lon": [-10, -9, -7, -6, -6, -7, -9, -10], "lat": [52, 53, 55, 54, 52, 51, 51, 52], "region": ["Ireland"] * 8}
)
italy = pd.DataFrame(
    {
        "lon": [8, 10, 12, 14, 16, 18, 18, 16, 14, 12, 10, 8],
        "lat": [44, 44, 42, 40, 38, 40, 42, 44, 45, 46, 46, 44],
        "region": ["Italy"] * 12,
    }
)
balkans = pd.DataFrame(
    {
        "lon": [20, 22, 24, 26, 28, 28, 26, 24, 22, 20],
        "lat": [36, 37, 38, 40, 42, 45, 44, 42, 40, 36],
        "region": ["Balkans"] * 10,
    }
)
df_land = pd.concat([europe_main, scandinavia, britain, ireland, italy, balkans], ignore_index=True)

plot_static = (
    ggplot()
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        data=df_tiles,
        fill=TILE_BG,
        color=TILE_BORDER,
        size=0.2,
        alpha=0.9,
    )
    + geom_polygon(
        aes(x="lon", y="lat", group="region"), data=df_land, fill=LAND_FILL, color=LAND_BORDER, size=0.6, alpha=0.95
    )
    + geom_point(
        aes(x="lon", y="lat", size="visitors"),
        data=df,
        fill=BRAND,
        color=PAGE_BG,
        alpha=0.85,
        shape=21,
        stroke=2,
        tooltips=layer_tooltips().title("@city").line("Visitors|@visitors K/year"),
    )
    + scale_size(range=[6, 22], name="Visitors (thousands)")
    + labs(title=TITLE, caption="Tile-style basemap (CARTO Positron style) | © OpenStreetMap contributors")
    + ggsize(800, 450)
    + theme_void()
    + theme(
        plot_title=element_text(size=16, color=INK),
        plot_caption=element_text(size=8, color=INK_MUTED),
        legend_title=element_text(size=10, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="right",
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    )
)

ggsave(plot_static, f"plot-{THEME}.png", path=".", scale=4)
