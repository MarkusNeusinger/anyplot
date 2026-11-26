"""anyplot.ai
scatter-map-geographic: Scatter Map with Geographic Points
Library: letsplot 4.11.0 | Python 3.14.10
Quality: pending | Updated: 2026-11-22
"""

import json
import os
import urllib.request

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_polygon,
    gggrid,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    scale_color_manual,
    scale_size,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
BASEMAP_BORDER = "#B0B0B0" if THEME == "light" else "#6B6A63"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
CITY = "City"  # role: label
LATITUDE = "Latitude"  # role: latitude
LONGITUDE = "Longitude"  # role: longitude
POPULATION = "Population (M)"  # role: size
REGION = "Region"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("cities.csv")
df = pd.DataFrame(
    [
        ("Tokyo", 35.68, 139.69, 37.4, "Asia"),
        ("Delhi", 28.61, 77.21, 32.9, "Asia"),
        ("Shanghai", 31.23, 121.47, 29.2, "Asia"),
        ("Sao Paulo", -23.55, -46.63, 22.4, "S. America"),
        ("Mexico City", 19.43, -99.13, 21.8, "N. America"),
        ("Cairo", 30.04, 31.24, 21.3, "Africa"),
        ("Mumbai", 19.08, 72.88, 21.0, "Asia"),
        ("Beijing", 39.9, 116.41, 20.9, "Asia"),
        ("Dhaka", 23.81, 90.41, 22.5, "Asia"),
        ("Osaka", 34.69, 135.5, 19.1, "Asia"),
        ("New York", 40.71, -74.01, 18.8, "N. America"),
        ("Karachi", 24.86, 67.01, 16.8, "Asia"),
        ("Buenos Aires", -34.6, -58.38, 15.4, "S. America"),
        ("Chongqing", 29.43, 106.91, 16.9, "Asia"),
        ("Istanbul", 41.01, 28.98, 15.6, "Europe"),
        ("Kolkata", 22.57, 88.36, 15.1, "Asia"),
        ("Manila", 14.6, 120.98, 14.4, "Asia"),
        ("Lagos", 6.52, 3.38, 15.3, "Africa"),
        ("Rio de Janeiro", -22.91, -43.17, 13.5, "S. America"),
        ("Tianjin", 39.34, 117.2, 13.6, "Asia"),
        ("Kinshasa", -4.44, 15.27, 17.0, "Africa"),
        ("Guangzhou", 23.13, 113.26, 14.3, "Asia"),
        ("Los Angeles", 34.05, -118.24, 12.5, "N. America"),
        ("Moscow", 55.76, 37.62, 12.5, "Europe"),
        ("Shenzhen", 22.54, 114.06, 13.4, "Asia"),
        ("Lahore", 31.56, 74.35, 13.5, "Asia"),
        ("Bangalore", 12.97, 77.59, 13.2, "Asia"),
        ("Paris", 48.86, 2.35, 11.0, "Europe"),
        ("Bogota", 4.71, -74.07, 11.3, "S. America"),
        ("Jakarta", -6.21, 106.85, 11.2, "Asia"),
        ("Chennai", 13.08, 80.27, 11.5, "Asia"),
        ("Lima", -12.05, -77.04, 11.0, "S. America"),
        ("Bangkok", 13.76, 100.5, 10.7, "Asia"),
        ("Seoul", 37.57, 127.0, 9.9, "Asia"),
        ("Nagoya", 35.18, 136.91, 9.5, "Asia"),
        ("Hyderabad", 17.39, 78.49, 10.5, "Asia"),
        ("London", 51.51, -0.13, 9.5, "Europe"),
        ("Tehran", 35.69, 51.39, 9.4, "Asia"),
        ("Chicago", 41.88, -87.63, 8.9, "N. America"),
        ("Chengdu", 30.57, 104.07, 9.4, "Asia"),
        ("Nanjing", 32.06, 118.8, 9.0, "Asia"),
        ("Wuhan", 30.59, 114.31, 8.3, "Asia"),
        ("Ho Chi Minh City", 10.82, 106.63, 9.1, "Asia"),
        ("Luanda", -8.84, 13.23, 8.9, "Africa"),
        ("Ahmedabad", 23.02, 72.57, 8.4, "Asia"),
        ("Kuala Lumpur", 3.14, 101.69, 8.3, "Asia"),
        ("Hong Kong", 22.32, 114.17, 7.5, "Asia"),
        ("Hangzhou", 30.27, 120.15, 8.2, "Asia"),
        ("Sydney", -33.87, 151.21, 5.3, "Oceania"),
    ],
    columns=[CITY, LATITUDE, LONGITUDE, POPULATION, REGION],
)

# Basemap: Natural Earth 110m land polygons (public domain), one polygon id per exterior ring
LAND_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_land.geojson"
with urllib.request.urlopen(LAND_URL, timeout=60) as response:
    land = json.load(response)
rings = [
    ring[0]
    for feature in land["features"]
    for ring in (
        feature["geometry"]["coordinates"]
        if feature["geometry"]["type"] == "MultiPolygon"
        else [feature["geometry"]["coordinates"]]
    )
]
basemap = pd.DataFrame(
    [(ring_id, lon, lat) for ring_id, ring in enumerate(rings) for lon, lat in ring], columns=["ring", "lon", "lat"]
)

# Plot
regions = list(dict.fromkeys(df[REGION]))
region_colors = [IMPRINT_PALETTE[i] for i in range(len(regions))]

plot = (
    ggplot()
    + geom_polygon(aes(x="lon", y="lat", group="ring"), data=basemap, fill=ELEVATED_BG, color=BASEMAP_BORDER, size=0.15)
    + geom_point(
        aes(x=LONGITUDE, y=LATITUDE, color=REGION, size=POPULATION),
        data=df,
        alpha=0.85,
        tooltips=layer_tooltips()
        .title(f"@{{{CITY}}}")
        .line(f"{POPULATION}|@{{{POPULATION}}}")
        .line(f"{REGION}|@{{{REGION}}}"),
    )
    + scale_color_manual(values=region_colors, breaks=regions, name=REGION)
    + scale_size(range=[2, 9], name=POPULATION)
    + labs(title="scatter-map-geographic · python · letsplot · anyplot.ai", x="Longitude (°)", y="Latitude (°)")
    + coord_fixed(ratio=1.0, xlim=[-180, 180], ylim=[-60, 80])
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=16, color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.3),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=12, color=INK),
        legend_position="bottom",
        panel_grid_major=element_line(color=GRID, size=0.2),
        panel_grid_minor=element_blank(),
    )
)

# One-panel grid paints the whole canvas in the page color around the fixed-aspect plot
plot = gggrid([plot]) + ggsize(800, 450) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

# Save PNG (scale 4 gives 3200 x 1800 px) and interactive HTML
ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, filename=f"plot-{THEME}.html", path=".")
