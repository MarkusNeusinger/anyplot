""" anyplot.ai
bubble-map-geographic: Bubble Map with Sized Geographic Markers
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-22
"""

import os

import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_polygon,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_color_manual,
    scale_size,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
CITY = "City"  # role: label
LATITUDE = "Latitude (°)"  # role: latitude
LONGITUDE = "Longitude (°)"  # role: longitude
POPULATION = "Population (millions)"  # role: value
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
            "Kolkata",
            "Lagos",
            "Rio de Janeiro",
            "Los Angeles",
            "Moscow",
            "Paris",
            "Bangkok",
            "Seoul",
            "London",
            "Lima",
            "Chicago",
            "Santiago",
            "Sydney",
            "Toronto",
            "Singapore",
            "Dubai",
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
            22.57,
            6.52,
            -22.91,
            34.05,
            55.76,
            48.86,
            13.76,
            37.57,
            51.51,
            -12.05,
            41.88,
            -33.45,
            -33.87,
            43.65,
            1.35,
            25.20,
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
            88.36,
            3.38,
            -43.17,
            -118.24,
            37.62,
            2.35,
            100.50,
            127.00,
            -0.13,
            -77.04,
            -87.63,
            -70.67,
            151.21,
            -79.38,
            103.82,
            55.27,
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
            15.1,
            15.3,
            13.5,
            12.5,
            12.5,
            11.0,
            10.7,
            9.9,
            9.5,
            11.0,
            8.9,
            6.8,
            5.3,
            6.3,
            5.9,
            3.4,
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
            "Asia",
            "Africa",
            "S. America",
            "N. America",
            "Europe",
            "Europe",
            "Asia",
            "Asia",
            "Europe",
            "S. America",
            "N. America",
            "S. America",
            "Oceania",
            "N. America",
            "Asia",
            "Asia",
        ],
    }
)

# Basemap: simplified continent outlines as (longitude, latitude) vertices
continents = {
    "N. America": (
        [-170, -168, -140, -125, -124, -117, -105, -97, -82, -77, -68, -55, -52, -80, -87, -97, -105, -125, -145, -165],
        [60, 65, 70, 55, 48, 33, 25, 26, 25, 35, 45, 48, 45, 27, 30, 20, 22, 50, 60, 55],
    ),
    "S. America": (
        [-80, -68, -60, -50, -35, -40, -50, -55, -68, -72, -75, -80, -82],
        [10, 12, 5, 0, -5, -22, -35, -52, -55, -18, -5, 0, 8],
    ),
    "Europe": (
        [-10, 0, 10, 20, 30, 40, 50, 60, 50, 35, 25, 20, 10, 0, -10],
        [35, 37, 36, 35, 35, 40, 45, 55, 70, 70, 70, 65, 60, 50, 40],
    ),
    "Africa": ([-17, -5, 10, 35, 50, 52, 43, 35, 30, 15, 0, -17], [15, 37, 37, 32, 12, 0, -25, -35, -35, -25, 5, 20]),
    "Asia": (
        [60, 80, 100, 120, 140, 145, 140, 130, 105, 100, 80, 60, 45, 30, 25, 30, 35, 50],
        [55, 70, 75, 70, 55, 45, 35, 30, 0, 5, 10, 25, 30, 35, 42, 55, 70, 70],
    ),
    "Australia": ([113, 125, 135, 145, 152, 150, 140, 130, 115], [-22, -15, -12, -15, -25, -38, -38, -33, -35]),
}

# Plot: reads only df, the basemap and the constants above
land = pd.DataFrame(
    [
        {"continent": name, "order": i, "lon": lon, "lat": lat}
        for name, (lons, lats) in continents.items()
        for i, (lon, lat) in enumerate(zip(lons, lats, strict=True))
    ]
)

# Largest bubbles first, so smaller ones are drawn on top
bubbles = df.sort_values(POPULATION, ascending=False)
regions = df[REGION].unique().tolist()
top = df[POPULATION].max()
size_breaks = [round(top * share) for share in (0.1, 0.35, 0.7, 1.0)]

plot = (
    ggplot()
    # Quiet basemap: ocean in the page color, land marked only by faint coastline strokes
    + geom_polygon(
        aes(x="lon", y="lat", group="continent"), data=land, fill="none", color=INK_SOFT, size=0.3, alpha=0.45
    )
    + geom_point(aes(x=LONGITUDE, y=LATITUDE, color=REGION, size=POPULATION), data=bubbles, alpha=0.7, stroke=0.3)
    # Size by area (scale_size maps value to area) with a floor so the smallest city stays visible
    + scale_size(range=(2.5, 14), breaks=size_breaks, name=POPULATION)
    + scale_color_manual(values=IMPRINT_PALETTE, limits=regions, name=REGION)
    + scale_x_continuous(breaks=range(-180, 181, 60), expand=(0, 0))
    + scale_y_continuous(breaks=range(-60, 81, 30), expand=(0, 0))
    + coord_fixed(ratio=1.0, xlim=(-180, 180), ylim=(-60, 80))
    + guides(
        size=guide_legend(order=1, override_aes={"color": INK_SOFT, "alpha": 0.7}),
        color=guide_legend(order=2, override_aes={"size": 5, "alpha": 0.85}),
    )
    + labs(
        title="World City Populations · bubble-map-geographic · python · plotnine · anyplot.ai", x=LONGITUDE, y=LATITUDE
    )
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        # Graticule: faint lines every 30-60 degrees
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.12),
        panel_grid_minor=element_blank(),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=10, weight="bold", color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=9, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color="none"),
        legend_key=element_rect(fill=ELEVATED_BG, color="none"),
        legend_position="right",
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
