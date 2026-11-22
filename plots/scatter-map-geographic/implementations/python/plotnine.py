"""anyplot.ai
scatter-map-geographic: Scatter Map with Geographic Points
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-11-22
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
    scale_size_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
BASEMAP_COLOR = "#E8E3D8" if THEME == "light" else "#2A2A26"
BASEMAP_EDGE = "#C0B5A8" if THEME == "light" else "#4A4945"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants: simplified continent outlines (longitudes, latitudes) for the basemap
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
    "Oceania": ([113, 125, 145, 153, 148, 140, 130, 115, 113], [-20, -14, -16, -28, -40, -38, -32, -34, -20]),
}

CITY = "City"  # role: label
LATITUDE = "Latitude (°)"  # role: latitude
LONGITUDE = "Longitude (°)"  # role: longitude
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
        ("Los Angeles", 34.05, -118.24, 12.5, "N. America"),
        ("Moscow", 55.76, 37.62, 12.5, "Europe"),
        ("Paris", 48.86, 2.35, 11.0, "Europe"),
        ("Bangkok", 13.76, 100.5, 10.7, "Asia"),
        ("Seoul", 37.57, 127.0, 9.9, "Asia"),
        ("London", 51.51, -0.13, 9.5, "Europe"),
        ("Lima", -12.05, -77.04, 11.0, "S. America"),
        ("Chicago", 41.88, -87.63, 8.9, "N. America"),
        ("Cape Town", -33.93, 18.42, 4.8, "Africa"),
        ("Sydney", -33.87, 151.21, 5.3, "Oceania"),
        ("Toronto", 43.65, -79.38, 6.3, "N. America"),
    ],
    columns=[CITY, LATITUDE, LONGITUDE, POPULATION, REGION],
)

# Plot
df_continents = pd.DataFrame(
    [
        {"continent": name, "order": i, "lon": lon, "lat": lat}
        for name, (lons, lats) in CONTINENT_OUTLINES.items()
        for i, (lon, lat) in enumerate(zip(lons, lats, strict=True))
    ]
)

plot = (
    ggplot()
    + geom_polygon(
        aes(x="lon", y="lat", group="continent"),
        data=df_continents,
        fill=BASEMAP_COLOR,
        color=BASEMAP_EDGE,
        size=0.25,
        alpha=0.6,
    )
    + geom_point(aes(x=LONGITUDE, y=LATITUDE, color=REGION, size=POPULATION), data=df, alpha=0.8, stroke=0.25)
    + scale_color_manual(values=IMPRINT_PALETTE, limits=sorted(df[REGION].unique()))
    + scale_size_continuous(range=(2, 10))
    + labs(title="scatter-map-geographic · python · plotnine · anyplot.ai", x=LONGITUDE, y=LATITUDE)
    + guides(size=guide_legend(override_aes={"color": INK_SOFT}))
    + coord_fixed(ratio=1.0, xlim=(-180, 180), ylim=(-60, 80))
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_title=element_text(size=12, color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=9, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color="none"),
        legend_key=element_rect(fill=ELEVATED_BG, color="none"),
        legend_position="right",
        panel_grid_major=element_line(color=INK, size=0.15, alpha=0.08),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill=PAGE_BG, color=None),
        plot_background=element_rect(fill=PAGE_BG, color=None),
        panel_border=element_blank(),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
