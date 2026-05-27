""" anyplot.ai
scatter-map-geographic: Scatter Map with Geographic Points
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-18
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot import ggsave


LetsPlot.setup_html()  # noqa: F405

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette - first series always #009E73
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]

# Data: Major world cities with population and region
np.random.seed(42)

cities_data = {
    "city": [
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
        "Chongqing",
        "Istanbul",
        "Kolkata",
        "Manila",
        "Lagos",
        "Rio de Janeiro",
        "Tianjin",
        "Kinshasa",
        "Guangzhou",
        "Los Angeles",
        "Moscow",
        "Shenzhen",
        "Lahore",
        "Bangalore",
        "Paris",
        "Bogota",
        "Jakarta",
        "Chennai",
        "Lima",
        "Bangkok",
        "Seoul",
        "Nagoya",
        "Hyderabad",
        "London",
        "Tehran",
        "Chicago",
        "Chengdu",
        "Nanjing",
        "Wuhan",
        "Ho Chi Minh City",
        "Luanda",
        "Ahmedabad",
        "Kuala Lumpur",
        "Hong Kong",
        "Hangzhou",
        "Sydney",
    ],
    "latitude": [
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
        29.43,
        41.01,
        22.57,
        14.60,
        6.52,
        -22.91,
        39.34,
        -4.44,
        23.13,
        34.05,
        55.76,
        22.54,
        31.56,
        12.97,
        48.86,
        4.71,
        -6.21,
        13.08,
        -12.05,
        13.76,
        37.57,
        35.18,
        17.39,
        51.51,
        35.69,
        41.88,
        30.57,
        32.06,
        30.59,
        10.82,
        -8.84,
        23.02,
        3.14,
        22.32,
        30.27,
        -33.87,
    ],
    "longitude": [
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
        106.91,
        28.98,
        88.36,
        120.98,
        3.38,
        -43.17,
        117.20,
        15.27,
        113.26,
        -118.24,
        37.62,
        114.06,
        74.35,
        77.59,
        2.35,
        -74.07,
        106.85,
        80.27,
        -77.04,
        100.50,
        127.00,
        136.91,
        78.49,
        -0.13,
        51.39,
        -87.63,
        104.07,
        118.80,
        114.31,
        106.63,
        13.23,
        72.57,
        101.69,
        114.17,
        120.15,
        151.21,
    ],
    "population": [
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
        16.9,
        15.6,
        15.1,
        14.4,
        15.3,
        13.5,
        13.6,
        17.0,
        14.3,
        12.5,
        12.5,
        13.4,
        13.5,
        13.2,
        11.0,
        11.3,
        11.2,
        11.5,
        11.0,
        10.7,
        9.9,
        9.5,
        10.5,
        9.5,
        9.4,
        8.9,
        9.4,
        9.0,
        8.3,
        9.1,
        8.9,
        8.4,
        8.3,
        7.5,
        8.2,
        5.3,
    ],
    "region": [
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
        "Asia",
        "Europe",
        "Asia",
        "Asia",
        "Africa",
        "S. America",
        "Asia",
        "Africa",
        "Asia",
        "N. America",
        "Europe",
        "Asia",
        "Asia",
        "Asia",
        "Europe",
        "S. America",
        "Asia",
        "Asia",
        "S. America",
        "Asia",
        "Asia",
        "Asia",
        "Asia",
        "Europe",
        "Asia",
        "N. America",
        "Asia",
        "Asia",
        "Asia",
        "Asia",
        "Africa",
        "Asia",
        "Asia",
        "Asia",
        "Asia",
        "Oceania",
    ],
}

df = pd.DataFrame(cities_data)

# Continent basemap with Australia/Oceania
continents = []

# North America
na_lon = [
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
]
na_lat = [60, 65, 70, 55, 48, 33, 25, 26, 25, 35, 45, 48, 45, 27, 30, 20, 22, 50, 60, 55, 60]
for i in range(len(na_lon)):
    continents.append({"continent": "N. America", "order": i, "lon": na_lon[i], "lat": na_lat[i]})

# South America
sa_lon = [-80, -68, -60, -50, -35, -40, -50, -55, -68, -72, -75, -80, -82, -80]
sa_lat = [10, 12, 5, 0, -5, -22, -35, -52, -55, -18, -5, 0, 8, 10]
for i in range(len(sa_lon)):
    continents.append({"continent": "S. America", "order": i, "lon": sa_lon[i], "lat": sa_lat[i]})

# Europe
eu_lon = [-10, 0, 10, 20, 30, 40, 50, 60, 50, 35, 25, 20, 10, 0, -10, -10]
eu_lat = [35, 37, 36, 35, 35, 40, 45, 55, 70, 70, 70, 65, 60, 50, 40, 35]
for i in range(len(eu_lon)):
    continents.append({"continent": "Europe", "order": i, "lon": eu_lon[i], "lat": eu_lat[i]})

# Africa
af_lon = [-17, -5, 10, 35, 50, 52, 43, 35, 30, 15, 0, -17, -17]
af_lat = [15, 37, 37, 32, 12, 0, -25, -35, -35, -25, 5, 20, 15]
for i in range(len(af_lon)):
    continents.append({"continent": "Africa", "order": i, "lon": af_lon[i], "lat": af_lat[i]})

# Asia
as_lon = [60, 80, 100, 120, 140, 145, 140, 130, 105, 100, 80, 60, 45, 30, 25, 30, 35, 50, 60]
as_lat = [55, 70, 75, 70, 55, 45, 35, 30, 0, 5, 10, 25, 30, 35, 42, 55, 70, 70, 55]
for i in range(len(as_lon)):
    continents.append({"continent": "Asia", "order": i, "lon": as_lon[i], "lat": as_lat[i]})

# Australia/Oceania
au_lon = [112, 130, 155, 168, 155, 145, 130, 115, 112]
au_lat = [-10, -10, -5, 0, -20, -35, -40, -30, -10]
for i in range(len(au_lon)):
    continents.append({"continent": "Oceania", "order": i, "lon": au_lon[i], "lat": au_lat[i]})

df_continents = pd.DataFrame(continents)

# Region color mapping using Okabe-Ito
region_colors = {
    "Asia": IMPRINT[0],  # #009E73
    "Europe": IMPRINT[1],  # #C475FD
    "N. America": IMPRINT[2],  # #4467A3
    "S. America": IMPRINT[3],  # #BD8233
    "Africa": IMPRINT[4],  # #AE3030
    "Oceania": IMPRINT[5],  # #2ABCCD
}

# Basemap color
basemap_fill = "#FFFDF6" if THEME == "light" else "#242420"
basemap_border = "#B0B0B0" if THEME == "light" else "#6B6A63"

# Create the geographic scatter map
plot = (
    ggplot()  # noqa: F405
    + geom_polygon(  # noqa: F405
        aes(x="lon", y="lat", group="continent"),  # noqa: F405
        data=df_continents,
        fill=basemap_fill,
        color=basemap_border,
        size=0.3,
        alpha=0.6,
    )
    + geom_point(  # noqa: F405
        aes(x="longitude", y="latitude", color="region", size="population"),  # noqa: F405
        data=df,
        alpha=0.85,
        tooltips=layer_tooltips()  # noqa: F405
        .title("@city")
        .line("Population|@population M")
        .line("Region|@region"),
    )
    + scale_color_manual(values=list(region_colors.values()), name="Region")  # noqa: F405
    + scale_size(range=[4, 18], name="Population (M)")  # noqa: F405
    + labs(  # noqa: F405
        title="scatter-map-geographic · python · letsplot · anyplot.ai", x="Longitude", y="Latitude"
    )
    + coord_fixed(ratio=1.0, xlim=[-180, 180], ylim=[-60, 80])  # noqa: F405
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
        panel_background=element_rect(fill=PAGE_BG),  # noqa: F405
        plot_title=element_text(size=24, color=INK),  # noqa: F405
        axis_title=element_text(size=20, color=INK),  # noqa: F405
        axis_text=element_text(size=16, color=INK_SOFT),  # noqa: F405
        axis_line=element_line(color=INK_SOFT, size=0.5),  # noqa: F405
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),  # noqa: F405
        legend_text=element_text(size=16, color=INK_SOFT),  # noqa: F405
        legend_title=element_text(size=18, color=INK),  # noqa: F405
        legend_position="bottom",
        panel_grid_major=element_line(color=INK_SOFT, size=0.2),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
    )
)

# Save PNG (scale 3x to get 4800 x 2700 px)
ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=3)

# Save HTML for interactive version
ggsave(plot, filename=f"plot-{THEME}.html", path=".")
