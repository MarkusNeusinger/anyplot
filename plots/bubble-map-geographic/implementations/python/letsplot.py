""" anyplot.ai
bubble-map-geographic: Bubble Map with Sized Geographic Markers
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-09
"""

import os

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
    ggplot,
    ggsave,
    ggsize,
    guide_legend,
    guides,
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
GRID = "#E6E3D8" if THEME == "light" else "#2C2C28"
LAND = "#E8E5DA" if THEME == "light" else "#2A2A26"
COAST = "#B8B4A6" if THEME == "light" else "#4E4D47"

# Imprint palette: all eight positions, one per region in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants: simplified continent outlines for the basemap (closed polygons, lon/lat)
CONTINENT_OUTLINES = {
    "N. America": (
        [
            -170,
            -168,
            -140,
            -125,
            -124,
            -117,
            -105,
            -97,
            -82,
            -77,
            -68,
            -55,
            -52,
            -80,
            -87,
            -97,
            -105,
            -125,
            -145,
            -165,
            -170,
        ],
        [60, 65, 70, 55, 48, 33, 25, 26, 25, 35, 45, 48, 45, 27, 30, 20, 22, 50, 60, 55, 60],
    ),
    "S. America": (
        [-80, -68, -60, -50, -35, -40, -50, -55, -68, -72, -75, -80, -82, -80],
        [10, 12, 5, 0, -5, -22, -35, -52, -55, -18, -5, 0, 8, 10],
    ),
    "Europe": (
        [-10, 0, 10, 20, 30, 40, 50, 60, 50, 35, 25, 20, 10, 0, -10, -10],
        [35, 37, 36, 35, 35, 40, 45, 55, 70, 70, 70, 65, 60, 50, 40, 35],
    ),
    "Africa": (
        [-17, -5, 10, 35, 50, 52, 43, 35, 30, 15, 0, -17, -17],
        [15, 37, 37, 32, 12, 0, -25, -35, -35, -25, 5, 20, 15],
    ),
    "Asia": (
        [60, 80, 100, 120, 140, 145, 140, 130, 105, 100, 80, 60, 45, 30, 25, 30, 35, 50, 60],
        [55, 70, 75, 70, 55, 45, 35, 30, 0, 5, 10, 25, 30, 35, 42, 55, 70, 70, 55],
    ),
    "Oceania": ([113, 130, 150, 155, 153, 145, 130, 115, 113], [-25, -12, -15, -25, -35, -40, -35, -35, -25]),
}

# Columns: set these to your table's column names
CITY = "City"  # role: label
LATITUDE = "Latitude"  # role: latitude
LONGITUDE = "Longitude"  # role: longitude
POPULATION = "Population (M)"  # role: value
REGION = "Region"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("cities.csv")
df = pd.DataFrame(
    {
        CITY: [
            "Tokyo",
            "Delhi",
            "Shanghai",
            "Sao Paulo",
            "Mexico City",
            "Cairo",
            "Mumbai",
            "Beijing",
            "Dhaka",
            "Osaka",
            "New York",
            "Karachi",
            "Buenos Aires",
            "Istanbul",
            "Lagos",
            "Rio de Janeiro",
            "Moscow",
            "Paris",
            "London",
            "Los Angeles",
            "Bangkok",
            "Seoul",
            "Lima",
            "Sydney",
            "Toronto",
            "Singapore",
            "Dubai",
            "Madrid",
            "Berlin",
            "Rome",
        ],
        LATITUDE: [
            35.68,
            28.61,
            31.23,
            -23.55,
            19.43,
            30.04,
            19.08,
            39.90,
            23.81,
            34.69,
            40.71,
            24.86,
            -34.60,
            41.01,
            6.52,
            -22.91,
            55.76,
            48.86,
            51.51,
            34.05,
            13.76,
            37.57,
            -12.05,
            -33.87,
            43.65,
            1.35,
            25.20,
            40.42,
            52.52,
            41.90,
        ],
        LONGITUDE: [
            139.69,
            77.21,
            121.47,
            -46.63,
            -99.13,
            31.24,
            72.88,
            116.41,
            90.41,
            135.50,
            -74.01,
            67.01,
            -58.38,
            28.98,
            3.38,
            -43.17,
            37.62,
            2.35,
            -0.13,
            -118.24,
            100.50,
            127.00,
            -77.04,
            151.21,
            -79.38,
            103.82,
            55.27,
            -3.70,
            13.40,
            12.50,
        ],
        POPULATION: [
            37.4,
            32.9,
            29.2,
            22.4,
            21.8,
            21.3,
            21.0,
            20.9,
            22.5,
            19.1,
            18.8,
            16.8,
            15.4,
            15.6,
            15.3,
            13.5,
            12.5,
            11.0,
            9.5,
            12.5,
            10.7,
            9.9,
            11.0,
            5.4,
            6.2,
            5.9,
            3.5,
            6.7,
            3.6,
            4.3,
        ],
        REGION: [
            "Asia",
            "Asia",
            "Asia",
            "S. America",
            "N. America",
            "Africa",
            "Asia",
            "Asia",
            "Asia",
            "Asia",
            "N. America",
            "Asia",
            "S. America",
            "Europe",
            "Africa",
            "S. America",
            "Europe",
            "Europe",
            "Europe",
            "N. America",
            "Asia",
            "Asia",
            "S. America",
            "Oceania",
            "N. America",
            "Asia",
            "Asia",
            "Europe",
            "Europe",
            "Europe",
        ],
    }
)

# Plot: reads only df and the constants above
basemap = pd.DataFrame(
    [
        {"continent": name, "lon": lon, "lat": lat}
        for name, (lons, lats) in CONTINENT_OUTLINES.items()
        for lon, lat in zip(lons, lats, strict=True)
    ]
)

# Largest bubbles first, so smaller ones are drawn on top
bubbles = df.sort_values(POPULATION, ascending=False)
regions = list(dict.fromkeys(df[REGION].dropna()))
region_colors = {region: IMPRINT_PALETTE[i] for i, region in enumerate(regions)}

title = "bubble-map-geographic · python · letsplot · anyplot.ai"

plot = (
    ggplot()
    + geom_polygon(
        aes(x="lon", y="lat", group="continent"), data=basemap, fill=LAND, color=COAST, size=0.3, tooltips="none"
    )
    + geom_point(
        aes(x=LONGITUDE, y=LATITUDE, size=POPULATION, color=REGION),
        data=bubbles,
        alpha=0.65,
        tooltips=layer_tooltips()
        .title(f"@{{{CITY}}}")
        .line(f"Population|@{{{POPULATION}}} million")
        .line(f"Region|@{{{REGION}}}"),
    )
    + scale_size(range=[2, 14], name=POPULATION)
    + scale_color_manual(values=region_colors, limits=regions, name=REGION)
    + guides(
        color=guide_legend(override_aes={"size": 5, "alpha": 0.65}),
        size=guide_legend(override_aes={"color": INK_SOFT, "alpha": 0.65}),
    )
    + labs(title=title, x=LONGITUDE, y=LATITUDE)
    # Quickmap-style aspect, 1 / cos(50°) ≈ 1.55: true shapes near the northern mid-latitudes,
    # and the fixed panel fills the 16:9 canvas without transparent bands
    + coord_fixed(ratio=1.55, xlim=[-180, 180], ylim=[-60, 80])
    + ggsize(800, 450)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=GRID, size=0.3),
        panel_grid_minor=element_blank(),
        plot_title=element_text(size=16, color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=11, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.3),
        legend_position="right",
    )
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
