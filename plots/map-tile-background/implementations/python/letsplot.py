"""anyplot.ai
map-tile-background: Map with Tile Background
Library: letsplot 4.10.1 | Python 3.13.13
Quality: pending | Updated: 2026-05-27
"""

import math
import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_livemap,
    geom_point,
    geom_polygon,
    geom_segment,
    gggrid,
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
BRAND = "#009E73"  # Imprint palette position 1 — the first (and only) series

# Simulated tile colors adapt to the theme
WATER = "#D3DDE0" if THEME == "light" else "#20282B"
TILE_BORDER = "#BFCBCF" if THEME == "light" else "#2D373B"
LAND = "#EFECE3" if THEME == "light" else "#2E2E29"
LAND_BORDER = "#CBC7B9" if THEME == "light" else "#46463E"
PARK = "#D5E2C8" if THEME == "light" else "#2A3828"

# Column constants
STATION = "station"  # role: label
LAT = "lat"  # role: latitude
LON = "lon"  # role: longitude
TRIPS = "trips"  # role: size (average trips per day)
TRIPS_LABEL = "Average daily trips"

# Data: bike-share stations around Lower and Midtown Manhattan, with Brooklyn, Queens and Jersey City
df = pd.DataFrame(
    [
        ("Penn Station", 40.7506, -73.9935, 1850),
        ("Grand Central", 40.7527, -73.9772, 1620),
        ("Union Square", 40.7359, -73.9911, 1580),
        ("Times Square", 40.7580, -73.9855, 1400),
        ("Chelsea Market", 40.7424, -74.0061, 1310),
        ("Washington Square", 40.7308, -73.9973, 1250),
        ("Columbus Circle", 40.7681, -73.9819, 1210),
        ("Hudson Yards", 40.7536, -74.0010, 1180),
        ("Williamsburg", 40.7143, -73.9610, 1130),
        ("Hell's Kitchen", 40.7640, -73.9920, 1090),
        ("East Village", 40.7265, -73.9815, 1020),
        ("Wall Street", 40.7074, -74.0113, 980),
        ("SoHo", 40.7233, -74.0030, 940),
        ("DUMBO", 40.7010, -73.9880, 910),
        ("Central Park South", 40.7678, -73.9718, 900),
        ("Lower East Side", 40.7180, -73.9880, 860),
        ("Lincoln Center", 40.7725, -73.9835, 820),
        ("Tribeca", 40.7195, -74.0089, 780),
        ("Battery Park", 40.7033, -74.0130, 760),
        ("Murray Hill", 40.7490, -73.9790, 700),
        ("Greenpoint", 40.7297, -73.9540, 640),
        ("Upper East Side", 40.7736, -73.9566, 600),
        ("Long Island City", 40.7447, -73.9485, 560),
        ("Upper West Side", 40.7870, -73.9720, 540),
        ("Grove Street, Jersey City", 40.7195, -74.0430, 520),
        ("Hoboken Terminal", 40.7359, -74.0330, 480),
    ],
    columns=[STATION, LAT, LON, TRIPS],
)

# Plot
TITLE = "map-tile-background · python · letsplot · anyplot.ai"
CAPTION = "Tile-style basemap (CARTO Positron style) | © OpenStreetMap contributors"
PAD = 0.012
lon_min, lon_max = df[LON].min() - 0.025, df[LON].max() + 0.033
lat_min, lat_max = df[LAT].min() - 0.015, df[LAT].max() + 0.015
lat_mid = (lat_min + lat_max) / 2

# Interactive HTML — geom_livemap fetches real tiles, fitted to the data bounds
map_tiles = tilesets.LETS_PLOT_DARK if THEME == "dark" else tilesets.CARTO_POSITRON

plot_interactive = (
    ggplot()
    + geom_livemap(location=[lon_min, lat_min, lon_max, lat_max], tiles=map_tiles)
    + geom_point(
        aes(x=LON, y=LAT, size=TRIPS),
        data=df,
        fill=BRAND,
        color=PAGE_BG,
        alpha=0.85,
        shape=21,
        stroke=2,
        tooltips=layer_tooltips().title(f"@{STATION}").line(f"{TRIPS_LABEL}|@{TRIPS}"),
    )
    + scale_size(range=[5, 18], name=TRIPS_LABEL)
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

# Static PNG — a simulated tile basemap (water, land, park, tile seams) for raster export
shapes = {
    "Manhattan": [
        (-74.0145, 40.7005),
        (-74.0160, 40.7080),
        (-74.0140, 40.7150),
        (-74.0130, 40.7250),
        (-74.0090, 40.7350),
        (-74.0075, 40.7450),
        (-74.0050, 40.7550),
        (-74.0000, 40.7650),
        (-73.9930, 40.7740),
        (-73.9850, 40.7870),
        (-73.9780, 40.7990),
        (-73.9750, 40.8100),
        (-73.9330, 40.8100),
        (-73.9345, 40.8000),
        (-73.9440, 40.7800),
        (-73.9590, 40.7600),
        (-73.9710, 40.7450),
        (-73.9740, 40.7250),
        (-73.9740, 40.7120),
        (-73.9830, 40.7090),
        (-73.9960, 40.7060),
        (-74.0030, 40.7010),
    ],
    "Brooklyn and Queens": [
        (-74.0020, 40.6800),
        (-74.0000, 40.6980),
        (-73.9950, 40.7030),
        (-73.9880, 40.7040),
        (-73.9780, 40.7015),
        (-73.9700, 40.7040),
        (-73.9650, 40.7140),
        (-73.9600, 40.7290),
        (-73.9570, 40.7430),
        (-73.9500, 40.7510),
        (-73.9440, 40.7580),
        (-73.9330, 40.7720),
        (-73.9200, 40.7830),
        (-73.8000, 40.7830),
        (-73.8000, 40.6800),
    ],
    "Jersey City and Hoboken": [
        (-74.0700, 40.6800),
        (-74.0430, 40.6800),
        (-74.0450, 40.6950),
        (-74.0350, 40.7100),
        (-74.0290, 40.7250),
        (-74.0270, 40.7380),
        (-74.0230, 40.7500),
        (-74.0170, 40.7650),
        (-74.0120, 40.7800),
        (-74.0050, 40.8000),
        (-74.0000, 40.8100),
        (-74.0700, 40.8100),
    ],
}
park_shape = [(-73.9730, 40.7644), (-73.9818, 40.7681), (-73.9582, 40.8003), (-73.9493, 40.7968)]


def polygon_frame(outline, name):
    return pd.DataFrame({LON: [p[0] for p in outline], LAT: [p[1] for p in outline], "area": name})


df_land = pd.concat([polygon_frame(outline, name) for name, outline in shapes.items()], ignore_index=True)
df_park = polygon_frame(park_shape, "Central Park")

# Tile seams: square on screen, so a latitude step is the longitude step times cos(latitude)
tile_lon = 0.02
tile_lat = tile_lon * math.cos(math.radians(lat_mid))
seams_lon = [lon_min + k * tile_lon for k in range(1, int((lon_max - lon_min) / tile_lon) + 1)]
seams_lat = [lat_min + k * tile_lat for k in range(1, int((lat_max - lat_min) / tile_lat) + 1)]
df_seams = pd.DataFrame(
    [{"x": x, "xend": x, "y": lat_min, "yend": lat_max} for x in seams_lon]
    + [{"x": lon_min, "xend": lon_max, "y": y, "yend": y} for y in seams_lat]
)

plot_static = (
    ggplot()
    + geom_polygon(aes(x=LON, y=LAT, group="area"), data=df_land, fill=LAND, color=LAND_BORDER, size=0.5)
    + geom_polygon(aes(x=LON, y=LAT, group="area"), data=df_park, fill=PARK, color=PARK, size=0.3)
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=df_seams, color=TILE_BORDER, size=0.3, alpha=0.7)
    + geom_point(aes(x=LON, y=LAT, size=TRIPS), data=df, fill=BRAND, color=PAGE_BG, alpha=0.85, shape=21, stroke=1.5)
    + scale_size(range=[4, 13], name=TRIPS_LABEL)
    + coord_fixed(ratio=1 / math.cos(math.radians(lat_mid)), xlim=[lon_min, lon_max], ylim=[lat_min, lat_max])
    + labs(title=TITLE, caption=CAPTION)
    + theme_void()
    + theme(
        plot_title=element_text(size=16, color=INK),
        plot_caption=element_text(size=10, color=INK_MUTED),
        legend_title=element_text(size=10, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_key=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),
        legend_position="bottom",
        panel_background=element_rect(fill=WATER, color=LAND_BORDER),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    )
)

# A fixed aspect leaves the canvas edges transparent: a one-panel grid paints the page color
plot_static = (
    gggrid([plot_static]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))
)

ggsave(plot_static, f"plot-{THEME}.png", path=".", scale=4)
