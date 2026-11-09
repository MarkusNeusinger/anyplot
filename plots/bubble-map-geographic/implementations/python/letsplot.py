"""anyplot.ai
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
    scale_size_area,
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

# Constants: simplified coastlines for the basemap, "lon lat" vertices of closed rings
LAND_OUTLINES = {
    "North America": (
        "-168 66, -163 69, -156 71.3, -141 69.6, -128 70, -115 68.5, -95 68, -82 69, -80 63, -93 61, -94 58.5, "
        "-87 55.5, -82 55, -79 51.5, -76 56, -78 60, -71 61, -65 60, -61 56, -56 52, -60 48, -64 49, -61 46, "
        "-66 44, -70 43, -70.5 41.7, -72 41, -74 40.4, -75 39, -76 37, -75.5 35.2, -78 33.8, -81 31.5, -80.5 28, "
        "-80 25.5, -81.5 25.2, -82.7 28, -84 30, -89 30.2, -94 29.5, -97.3 27.5, -97.5 24, -97.5 21.5, -96 19, "
        "-94.5 18.2, -91 19, -90.5 21, -87 21.5, -88 16, -84 15.8, -83.3 11, -81.5 9, -79 9.5, -77.5 8.5, "
        "-78 7.5, -80.5 7.5, -83 8.3, -85.7 10, -87.5 13, -91.5 14, -94.5 16, -98 16.3, -101 17.5, -105.5 20, "
        "-105.5 22, -109.5 23, -112 25, -115 28, -117 32.5, -118.4 34, -120.6 34.6, -122.5 37.5, -124.3 40.5, "
        "-124 46, -124.7 48.4, -127 50.5, -130 54.5, -133 57.5, -137 58.5, -141 60, -147 61, -152 59.5, "
        "-158 56.5, -163 55, -158 58.5, -162 59.8, -165 61.5, -166 64, -168 66"
    ),
    "Greenland": (
        "-73 78, -60 82, -35 83.5, -20 82, -18 77, -21 70, -26 68, -35 65.5, -42 60, -48 61, -52 65, -54 69, "
        "-58 75, -66 76.5, -73 78"
    ),
    "Baffin Island": "-62 66.5, -66 62, -71 62.5, -78 64.5, -74 68, -83 70, -90 72, -80 73.7, -70 70.5, -62 66.5",
    "Victoria Island": "-118 69, -101 68.5, -101 72.5, -117 73, -118 69",
    "Cuba": "-85 21.9, -82 23.2, -77.5 21.8, -74.2 20.2, -77.7 19.9, -80.5 22, -85 21.9",
    "South America": (
        "-77 8.5, -72 12, -67 10.7, -62 10.7, -60 8.5, -57 6, -52 5, -50 1.5, -48 -1, -44 -2.5, -40 -3, "
        "-35 -5.5, -35 -9, -38.5 -13, -39 -17.5, -40.5 -21, -42 -23, -44.5 -23.3, -46.5 -24, -48.5 -26, "
        "-48.7 -28.5, -51 -31, -53 -33.8, -55 -34.9, -57.5 -35, -57 -37, -58 -38.5, -62 -39, -62.5 -41, "
        "-65 -42.5, -65.5 -45, -67.5 -46.5, -66 -48, -69 -51, -68.5 -52.5, -70 -55, -74 -52, -75.5 -47, "
        "-74 -43, -73.5 -37, -71.5 -32, -71.3 -28, -70.5 -23, -70.3 -18.5, -72 -17, -76 -14, -77.5 -12, "
        "-79 -8, -81.2 -5.5, -80.5 -2.5, -80 0, -79.5 1.5, -78 3, -77.5 6, -77 8.5"
    ),
    "Africa": (
        "-17 21, -16 24, -13 27.5, -10 29.5, -9.5 32, -6 35.8, -2 35.1, 3 36.8, 10 37.2, 11 33.5, 15 32.3, "
        "20 30.5, 20 32.5, 25 31.7, 29 30.9, 32 31.3, 32.5 29.9, 34 27, 37 21, 39 15.5, 43 12.5, 44.5 10.5, "
        "51 11.8, 51 10.5, 48 4.5, 41 -2, 39.5 -6, 40.5 -11, 40.5 -15, 35.5 -22, 32.8 -26, 30 -31, 27 -33.8, "
        "22 -34.2, 18.5 -34.2, 18 -31.5, 15 -27, 14.5 -22.5, 12 -17, 13.7 -11, 12.3 -6, 9 -1, 9.8 3.5, "
        "8.5 4.5, 6 4.3, 3.4 6.2, 1 6, -2 4.8, -7.5 4.4, -11.5 6.9, -13.5 9.5, -16.7 12.5, -17.5 14.7, "
        "-16.5 19, -17 21"
    ),
    "Madagascar": "49.3 -12, 50.5 -15.5, 47.5 -25, 45 -25.5, 43.5 -22, 44.5 -16, 49.3 -12",
    "Eurasia": (
        "-5.6 36, -9 37, -8.8 42, -9.3 43, -1.8 43.4, -1.2 46, -4.5 47.8, -1.5 48.7, 1.5 50, 3 51, 4.5 52.5, "
        "5 53.4, 8.5 53.8, 8.5 55.5, 8 57, 10.5 57.7, 10.5 56, 12.5 56, 12 54.3, 14 54, 18.5 54.8, 21 55, "
        "21 57, 24 57.3, 24 59.4, 29.5 60, 23 60, 21.5 61.5, 21.5 63.5, 25 65, 22 65.8, 17.5 62.5, 19 60, "
        "16.5 57, 14 55.5, 12.5 56.5, 11 59, 8 58, 5.5 59, 5 62, 10 64, 14 67.5, 18 69.8, 25 71, 31 70, "
        "41 67, 33 66, 37 64, 44 66, 53 68.5, 60 69, 68 69, 73 72.5, 80 73.5, 87 75, 100 77.5, 105 77.5, "
        "113 73.5, 130 71, 140 72.5, 150 71.5, 160 69.5, 170 70, 180 69, 180 65, 178 64.5, 173 61, 166 60, "
        "163 57, 160 54, 156.5 51, 156 57, 160 61.5, 155 59.3, 143 59.3, 137 54, 141 52.5, 140 48, "
        "135 43.5, 131 42.5, 129.5 41, 129.5 36, 126.5 34.5, 126.2 37.7, 125 39.5, 121.5 39, 122 40.5, "
        "118 39, 117.7 38.3, 119 37.2, 122.5 37, 120 34.5, 121.8 31.5, 122 30, 119.5 25.5, 117 23.5, 113 22, "
        "110 21, 108 21.5, 106 20, 106.5 17.5, 108.5 15, 109.3 12, 107 10.5, 105 8.6, 103 10.5, 100.5 13.5, "
        "99.2 10, 100.3 7, 103.4 3.5, 104.3 1.3, 103.5 1.15, 101.3 2.8, 100.4 5.5, 98.3 8, 98.5 13, "
        "97.5 16.5, 94.5 16, 94 19, 92 21, 90 22, 87 21.5, 85.5 19.5, 80.3 15.5, 80 10.5, 77.5 8, 76 10, "
        "74.8 13, 73 17, 72.6 19, 72.6 21.5, 70 21, 68.5 23, 66.6 24.6, 62 25.2, 57.5 25.5, 56.5 27, "
        "54 26.6, 51.5 27.8, 48.5 30, 48 29, 50 26, 51.5 25.5, 51.5 24, 54 24.2, 55.5 25.6, 56 26.3, "
        "56.3 24.5, 59.8 22.4, 57.8 19, 55 17, 52.2 15.8, 45 13, 43.2 13, 42.6 16, 39 21.5, 34.8 28, "
        "34.9 29.5, 32.6 29.9, 32.3 31.3, 34.3 31.4, 35 32.8, 35.9 35.5, 36 36.8, 34 36.2, 32.5 36.1, "
        "30.5 36.5, 28 36.7, 27.3 37, 26.3 39.5, 26.5 40.6, 26.1 40.8, 23 40.5, 24 38, 22.5 36.5, 21 38, "
        "19.5 40, 19.5 42, 15.5 44, 13.6 45.6, 12.3 45.3, 12.5 44, 14 42, 16 41, 18.5 40.2, 16.5 38, "
        "15.6 38, 16 39.5, 15.5 40.2, 12.2 41.5, 10.5 43, 8.8 44.4, 6.5 43.1, 3.2 43.3, 3.2 42, 0.8 41, "
        "0 39.5, -0.5 38.5, -2 36.7, -5.6 36"
    ),
    "Great Britain": (
        "-5.7 50, -3 50.6, 1.3 51.1, 1.7 52.6, 0.3 53.4, -0.5 54.5, -1.6 55.6, -2 57, -1.8 57.6, -4 57.6, "
        "-3 58.6, -5 58.6, -6.2 57.5, -5.6 56, -4.9 55, -3 54.8, -3.3 54, -3 53.3, -4.5 53.3, -4.2 52.3, "
        "-5.3 51.8, -3 51.4, -4.5 51, -5.7 50"
    ),
    "Ireland": "-6 52.2, -6.2 53.9, -5.5 54.6, -7 55.3, -8.3 55.2, -10 54, -10.2 51.6, -8 51.6, -6 52.2",
    "Iceland": "-24 65.5, -22 66.4, -16 66.5, -13.6 65, -18 63.4, -22.5 63.8, -24 65.5",
    "Sri Lanka": "79.8 9.8, 81.8 7.5, 81.3 6.2, 80 6, 79.8 9.8",
    "Honshu": (
        "130 31.2, 131.5 31.5, 132 33.5, 135.5 33.5, 136.8 34.3, 138.8 34.6, 139.8 35, 140.9 36, 141 38.3, "
        "142 39.5, 141.5 41.4, 140 40.7, 139.8 39, 138.5 37.8, 137 37, 136.5 36, 135.5 35.6, 133 35.5, "
        "131 34.5, 129.7 33.3, 130 31.2"
    ),
    "Hokkaido": "140 41.5, 141.5 42.5, 143.5 42, 145.5 43.3, 144.5 44, 142 45.4, 141.5 43.5, 140 42.5, 140 41.5",
    "Taiwan": "120.1 23, 121 25.2, 122 25, 120.8 22, 120.1 23",
    "Luzon": "120 18.5, 122.3 18.5, 122 14, 124 13, 121 13.8, 120.6 15, 120 18.5",
    "Sumatra": "95.3 5.6, 98 4, 102 1, 106 -3, 105.7 -5.9, 102 -4, 98.5 0, 95.3 5.6",
    "Java": "105.2 -6.8, 108 -6.3, 112 -6.9, 114.5 -7.7, 110 -8.2, 105.2 -6.8",
    "Borneo": "109 1.5, 111 2, 115 5, 117.5 7, 119 5, 117.5 1, 116 -4, 111 -3, 109 -1, 109 1.5",
    "New Guinea": "131 -1.5, 135 -3.3, 141 -2.6, 146 -5.5, 150 -10.5, 147 -10, 143 -9, 141 -9.2, 138 -8.4, 134 -4, 131 -1.5",
    "Australia": (
        "113.5 -22, 114 -26.5, 115 -34, 118 -35, 122 -34, 126 -32.3, 131 -31.5, 135 -34.8, 137.5 -33, "
        "138 -35.7, 140.5 -38, 144 -38.3, 146.5 -39, 150 -37.5, 151.3 -34.5, 152.4 -32.4, 153.5 -28, "
        "153 -25, 150.5 -22, 146 -19, 145.5 -15, 143.5 -14, 142.5 -10.7, 141.5 -13, 141.5 -17, 139 -17.5, "
        "136 -15, 137 -12, 132.5 -11.2, 129.5 -15, 127 -14, 125 -15.5, 122 -17.5, 120 -20, 116.5 -20.7, "
        "113.5 -22"
    ),
    "Tasmania": "144.6 -40.7, 148.3 -40.9, 148 -43.2, 146 -43.6, 144.6 -40.7",
    "NZ North Island": (
        "172.7 -34.4, 174.5 -36, 178.5 -37.7, 177 -39.3, 175 -41.5, 174.6 -39.8, 173.8 -39.2, 174.6 -37, 172.7 -34.4"
    ),
    "NZ South Island": "172.7 -40.5, 174.3 -41.7, 171.2 -44.5, 169 -46.6, 166.5 -46, 168 -44, 172.7 -40.5",
}
# Inland seas, drawn over the land in the page colour
SEA_OUTLINES = {
    "Black Sea": (
        "28 41.3, 29.1 41.2, 31.5 41.2, 35 42, 38 41, 41.5 41.5, 41.7 42.7, 39.5 44, 37.5 45, 36.5 45.3, "
        "35 45, 33.5 44.5, 32.5 45.5, 31.5 46.6, 30.5 46.4, 29.7 45.2, 28.6 44, 28 42.5, 28 41.3"
    ),
    "Caspian Sea": (
        "47 44.5, 49 46.5, 52 46.8, 53.2 45, 51 44.5, 51.3 43, 52.8 41.5, 53 39.5, 54 37.3, 51 36.7, "
        "49 37.5, 49.5 40.5, 48 42, 47 44.5"
    ),
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
land, seas = (
    pd.DataFrame(
        [
            {"shape": name, "lon": float(vertex.split()[0]), "lat": float(vertex.split()[1])}
            for name, ring in outlines.items()
            for vertex in ring.split(",")
        ]
    )
    for outlines in (LAND_OUTLINES, SEA_OUTLINES)
)

# Largest bubbles first, so smaller ones are drawn on top
bubbles = df.sort_values(POPULATION, ascending=False)
regions = list(dict.fromkeys(df[REGION].dropna()))
region_colors = {region: IMPRINT_PALETTE[i] for i, region in enumerate(regions)}

title = "bubble-map-geographic · python · letsplot · anyplot.ai"

plot = (
    ggplot()
    + geom_polygon(aes(x="lon", y="lat", group="shape"), data=land, fill=LAND, color=COAST, size=0.3, tooltips="none")
    + geom_polygon(
        aes(x="lon", y="lat", group="shape"), data=seas, fill=PAGE_BG, color=COAST, size=0.3, tooltips="none"
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
    # Bubble area proportional to the value: twice the population, twice the area
    + scale_size_area(max_size=17, name=POPULATION)
    + scale_color_manual(values=region_colors, limits=regions, name=REGION)
    + guides(
        color=guide_legend(override_aes={"size": 5, "alpha": 0.65}),
        size=guide_legend(override_aes={"color": INK_SOFT, "alpha": 0.65}),
    )
    + labs(title=title, x=f"{LONGITUDE} (°)", y=f"{LATITUDE} (°)")
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
