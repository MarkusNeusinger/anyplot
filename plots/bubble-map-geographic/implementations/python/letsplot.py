""" pyplots.ai
bubble-map-geographic: Bubble Map with Sized Geographic Markers
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-10
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data: Major world cities with population (millions)
# Bubble size represents population magnitude - the primary visual encoding
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

df = pd.DataFrame(cities_data)

# Simplified continent outlines for basemap (closed polygons)
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
au_lon = [113, 130, 150, 155, 153, 145, 130, 115, 113]
au_lat = [-25, -12, -15, -25, -35, -40, -35, -35, -25]
for i in range(len(au_lon)):
    continents.append({"continent": "Oceania", "order": i, "lon": au_lon[i], "lat": au_lat[i]})

df_continents = pd.DataFrame(continents)

# Create the geographic bubble map
# Size is the PRIMARY visual encoding - use scale_size to map area proportionally
plot = (
    ggplot()  # noqa: F405
    + geom_polygon(  # noqa: F405
        aes(x="lon", y="lat", group="continent"),  # noqa: F405
        data=df_continents,
        fill="#E5E5E5",
        color="#A0A0A0",
        size=0.4,
        alpha=0.8,
    )
    + geom_point(  # noqa: F405
        aes(x="longitude", y="latitude", size="population", color="region"),  # noqa: F405
        data=df,
        alpha=0.65,
        stroke=0.8,
        tooltips=layer_tooltips()  # noqa: F405
        .title("@city")
        .line("Population|@population million")
        .line("Region|@region"),
    )
    # Scale bubble area proportionally - larger range for bubble emphasis
    + scale_size(range=[4, 28], name="Population (M)", breaks=[5, 10, 20, 30])  # noqa: F405
    + scale_color_manual(  # noqa: F405
        values=["#306998", "#DC2626", "#2CA02C", "#9467BD", "#FFD43B", "#17BECF"], name="Region"
    )
    + labs(  # noqa: F405
        title="World City Populations · bubble-map-geographic · letsplot · pyplots.ai", x="Longitude", y="Latitude"
    )
    + coord_fixed(ratio=1.0, xlim=[-180, 180], ylim=[-60, 80])  # noqa: F405
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=26, face="bold"),  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        legend_title=element_text(size=18),  # noqa: F405
        legend_text=element_text(size=14),  # noqa: F405
        legend_position="right",
        panel_grid_major=element_line(color="#D0D0D0", size=0.3),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        plot_background=element_rect(fill="#F8F8F8"),  # noqa: F405
    )
)

# Save PNG (scale 3x to get 4800 x 2700 px)
export_ggsave(plot, filename="plot.png", path=".", scale=3)

# Save HTML for interactive version
export_ggsave(plot, filename="plot.html", path=".")
