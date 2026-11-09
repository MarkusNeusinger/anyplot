"""anyplot.ai
bubble-map-geographic: Bubble Map with Sized Geographic Markers
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-09
"""

import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.ticker import MaxNLocator


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — canonical order, first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Constants
MAP_LON = (-180, 180)  # world extent of the basemap
MAP_LAT = (-58, 80)  # inhabited latitudes; the polar caps only add empty height
MAX_BUBBLE_AREA = 600  # marker area (pt²) of the largest value; area is proportional to the value

# Simplified world coastlines, one "lon,lat lon,lat ..." outline per landmass
WORLD_COASTLINES = [
    # North America
    "-166,68 -156,71.3 -141,69.6 -128,70 -115,68.5 -95,68 -85,69.5 -80,63 -94,59 -92,57 -82,55 -79,51.5 "
    "-77,60 -70,59 -64,60 -61,56 -56,52 -60,47 -66,44.5 -70,43 -70.5,41.5 -74,40.5 -76,37 -75.5,35.2 "
    "-81,31.5 -80,27 -80.5,25.2 -82.7,28 -84,30 -89,30.2 -94,29.5 -97.5,26 -97.8,22 -96,19 -91,18.7 "
    "-90.4,21 -87,21.5 -88,16 -84,15.8 -83.5,11 -81.5,9 -77.5,8.5 -79.5,7.5 -80.5,7.3 -83,8.3 -86,11.5 "
    "-91,13.8 -94,16 -96.5,15.7 -101,17.5 -105.5,20.5 -105.3,23 -108,25.5 -110.5,28 -112.8,31 -114.8,31.8 "
    "-114.2,29.5 -112.5,27 -111,24.5 -109.9,23 -112,25 -114.2,28 -115.9,30.5 -117.1,32.5 -118.5,34 "
    "-120.6,34.5 -122.5,37.5 -124,40.5 -124.5,43 -124,46.5 -124.7,48.4 -123,49 -127.5,51 -130,54.5 "
    "-134,58 -140,59.8 -146,61 -152,59.5 -158,56.5 -163,55 -158,58.5 -162,60 -165,62.5 -164.5,64.5 -168,65.6",
    # Greenland
    "-73,78 -60,82 -30,83.5 -20,81.5 -18,76 -22,70 -32,68 -40,65 -43,60 -48,61 -52,65 -54,70 -58,75.5 -66,76",
    # Cuba, Hispaniola
    "-84.9,21.9 -82,23.2 -77.5,22.2 -74.2,20.2 -77.7,19.9 -81,21.6",
    "-74.4,18.4 -72.8,19.9 -70,19.7 -68.4,18.6 -71.3,17.6",
    # South America
    "-77.5,8.5 -75.5,10.8 -72,11.8 -68,10.5 -62,10.6 -60,8.5 -57,6 -52,5 -50,1.5 -48,-1 -44,-2.5 -39,-3.5 "
    "-35,-6 -35,-9 -38.5,-13 -39,-17.5 -40.5,-21 -42,-23 -44.5,-23.3 -47,-24.5 -48.5,-26.5 -48.7,-28.5 "
    "-51,-31 -53.5,-34 -56.5,-34.8 -58.5,-34.2 -57.3,-36 -57.6,-38 -62,-39 -62.5,-41 -65,-42 -65.5,-45 "
    "-67.5,-46.5 -66,-48 -68.5,-51 -68.5,-52.5 -68,-54.8 -71,-54 -74,-52 -75.5,-48 -74,-44 -73.5,-40 "
    "-73.5,-37 -71.7,-33 -71.4,-30 -70.5,-25 -70.2,-18.5 -75,-15.5 -76.3,-13.5 -77.3,-12 -78.5,-9 "
    "-80.8,-5.5 -81.3,-4.2 -80,-2.5 -80.5,-0.5 -80,1 -78.8,1.8 -77.3,4 -77.4,6.5",
    # Eurasia: Mediterranean, Black Sea, Arabia, India, Southeast Asia, China, Korea, Siberia, Scandinavia
    "-5.6,36 -2,36.7 0,38.7 0.5,40.5 3.2,42 3.5,43.3 6,43.1 8.5,44.4 10.5,43 12.5,41.5 15.6,40 15.6,38 "
    "16.5,39.5 17.2,39 18.5,40.2 17,41 14,42.5 12.4,44.5 12.3,45.4 13.7,45.6 15,44.5 17,43 19.5,42 "
    "19.4,40.3 21,38 22.5,36.5 22.8,37.5 24,38 22.7,40.5 24,40.8 26,40.6 27.5,40.9 29,40.98 29.05,41.1 "
    "28,42.5 28.6,44 29.7,45.2 30.7,46.5 32,46.4 33.5,44.5 35.5,45.1 37.5,47 39.5,47 38,44.5 41.5,41.6 "
    "39,41 36,41.7 33,42 31,41.1 29.2,41.15 29.1,40.7 27,40.4 26.2,40 26.5,38.5 27.3,37 28.5,36.6 30.5,36.3 "
    "32.5,36.1 34.5,36.8 36,36.5 35.9,35 35,33 34.3,31.3 34.9,29.5 36.5,26 39,21.5 42.7,15 43.4,12.7 "
    "45,12.8 48.5,14 52,15.6 55.5,17.5 57.8,19 59.8,22.5 58.7,23.6 56.4,24.9 56.1,26.1 54.5,24.2 51.6,24.5 "
    "50,26.5 48,29.5 50.2,30.2 51.5,27.8 54,26.7 56.5,27.1 57.5,25.7 61.5,25.2 66.5,25.3 67,24.7 67.5,24 "
    "68.5,23.5 70,22.5 69,22.3 70.5,20.8 72.6,21.1 72.7,19.5 72.8,18.8 73.4,16 74.8,12.8 76.3,9.5 "
    "77.5,8.1 78.2,8.9 79.3,10.3 79.9,12 80.3,15.5 82.3,17 84.8,19.3 87,21.5 88.2,21.7 89.5,21.8 91,22.5 "
    "92.3,20.7 94.3,16 97.6,16.5 98.5,13 98.3,9 100.3,6 103.5,1.4 104.2,1.5 103.4,4.5 102.3,6.1 100.6,8.5 "
    "99.2,10.5 100,13.4 100.9,13.4 102.5,12 105,8.7 106.8,10.4 109.2,11.6 109.3,13.5 108.5,15.5 106,18.5 "
    "106.6,20.3 108,21.5 110,21 111.5,21.6 113.5,22.2 114.3,22.3 116.5,22.9 119,25.3 121.5,28.2 122,30.5 "
    "121.9,31.7 120.9,32.6 119.5,34.5 120.3,36.1 122.5,37.2 120.9,37.7 119,37.3 118,38.5 117.6,39 "
    "119.4,39.8 121.2,40.9 122.2,40.4 121.2,39 124.2,39.9 125.2,38.5 126.4,37.4 126.3,35 126.5,34.4 "
    "127.6,34.7 129.3,35.2 129.4,36.5 128.5,38.4 127.5,39.8 129.7,40.9 129.8,42.4 131,42.7 133,42.8 "
    "135.5,43.9 138.5,47 140.5,50 141.4,53 137,54 135.2,54.8 137.5,56.5 142,59 146,59.4 151,59.2 156,61.5 "
    "156,57.5 156.7,51 160,54 163,56 162,58 164,60 170,60 177,62.5 180,65 180,69.5 170,70 160,69.6 "
    "150,71.5 140,72.5 130,71 128,72.8 113,73.5 110,76.5 104,77.7 95,76 87,75 80,73.5 73,71 72.5,68.5 "
    "69,66.5 66,69.5 60,69 55,68.4 44,68.4 41,66.5 36,64.5 34.5,66.4 40,67.8 41,69.5 33,69.4 28,71 20,70 "
    "14,68 10.5,64.5 5,62 5.3,59 7,58 8.5,58.2 10.5,59.5 11.2,58.5 12.5,56.5 14.3,55.5 16.5,56.5 "
    "18.5,59.5 17.5,62 21.5,65 25.5,65 21.5,62.5 22,60.3 25,60.3 30,60 28,59.5 23.5,59.3 24,57.5 21,56.8 "
    "21,55.3 19,54.4 14.5,53.9 12,54.2 10.8,54 10,54.5 10.6,57.7 8.5,57 8.6,55 8.7,53.8 7,53.5 5,53 "
    "4,51.8 2,51 1.5,50 0,49.5 -1.5,49.7 -1.5,48.7 -4.7,48.5 -2.5,47.3 -1.2,46 -1.4,43.6 -3,43.4 -8,43.7 "
    "-9.3,43 -8.8,41.5 -9.5,38.8 -8.9,37 -7.5,37.2 -6.3,36.7",
    # Great Britain, Ireland, Iceland
    "-5.7,50 -3,50.5 0.5,50.8 1.6,52.3 0.3,53.4 -0.5,54.5 -1.5,55.5 -2,56.3 -1.8,57.6 -3.3,58.6 -5,58.6 "
    "-6.2,57 -5.6,55.4 -4.8,54.8 -3.2,54.9 -3,53.3 -4.6,53.2 -4.2,52.3 -5.2,51.7 -3.2,51.4",
    "-6,52.2 -6.2,53.9 -5.6,54.6 -6.2,55.3 -7.5,55.3 -8.6,54.6 -10,54.2 -9.9,53.4 -10.4,52.2 -9.6,51.5 -8,51.6",
    "-24,65.5 -22,66.4 -16,66.5 -13.6,65.2 -15,64.3 -18.7,63.4 -22.7,63.8",
    # Japan: Honshu, Kyushu, Shikoku, Hokkaido; Sakhalin
    "131,34.4 132.5,35.5 135.5,35.6 136.9,37.3 139.5,38.5 140,40 140,41.4 141.5,41.4 142,39.5 141,38.2 "
    "140.9,36.9 140.8,35.7 140.3,35.1 139.8,35.3 139.1,35.2 138.5,34.7 137,34.6 136.8,34.3 136,33.5 "
    "135.1,33.9 135.3,34.5 134.5,34.7 133,34.4 132,33.9 131,33.9",
    "129.8,33.5 131,33.9 131.8,33 131.3,31.4 130.2,31.2 129.6,32.8",
    "132.5,33.9 134,34.3 134.7,33.8 134.2,33.2 133,32.8 132.5,33.3",
    "139.9,42.5 141.2,41.8 143.3,42 145.5,43.3 144.5,44 141.8,45.4 141.5,43.3 140.5,43.2",
    "141.8,46 143.5,46.5 142.5,49 143,51 143.2,54 142.2,54.2 142,51 142,48",
    # Taiwan, Hainan, Sri Lanka
    "120.1,23 120.9,22 121.9,24.6 121.5,25.3 120.7,24.5",
    "108.6,19.2 110.5,20.1 111,19.6 110,18.2 109,18.4",
    "79.8,6 79.9,8.5 80.3,9.8 81.2,8.5 81.9,7 81.3,6.2 80.4,5.9",
    # Philippines: Luzon, Mindanao
    "119.8,16.3 120.4,18.5 122.2,18.5 122,16.5 121.6,15.8 122,14 124,13 124,12.5 122.5,13.2 121,13.6 "
    "120.6,14.2 120.9,14.45 120.6,14.8",
    "122,7 123.5,8.5 125.5,9.7 126.5,8 126,6.3 125,5.6 124,6.5 123.5,7.7 122.2,6.9",
    # Borneo, Sumatra, Java, New Guinea
    "109,1.5 110,-1.5 111,-3 114.5,-4 116.5,-2.5 118,1 119,5 117,7 115.5,5 113,3 110.5,1.7",
    "95.3,5.6 97.5,5.2 100.3,2.3 104,-1 106,-3 105.8,-5.8 104.5,-5.8 102,-4 100.3,-0.8 98.5,1.8",
    "105.2,-6.8 106.5,-6 108.3,-6.2 111,-6.4 112.6,-6.9 114.5,-7.8 114.4,-8.7 111,-8.2 106.5,-7.4",
    "131,-1.5 134,-1 137,-1.5 141,-2.6 145.8,-5 147.5,-6.2 150,-10.3 147,-9.5 143.5,-9 142,-9.2 "
    "138.5,-8.3 137.8,-5.3 135,-4.4 132.5,-4",
    # Africa, Madagascar
    "-5.9,35.8 -2,35.1 3,36.8 10,37.3 11,35.5 10.2,34 11.5,33.2 15.2,32.3 19,30.3 20,32 23,32.6 25,31.6 "
    "29,30.9 32.3,31.3 34.2,31.3 34.9,29.5 34.3,27.9 32.7,29.8 33.6,27.5 35.5,24 37.3,21 38.5,18 "
    "39.7,15.3 41.5,13.6 43.3,12.3 44.5,10.4 51.2,11.8 50.8,10 48,5 44,1 41.5,-1.8 40,-4 39.3,-7 "
    "40.5,-10.5 40.5,-15 36.8,-18 35.5,-21.5 35.5,-24 32.8,-26 32.5,-28.7 30.5,-31 27.5,-33.5 25,-34 "
    "22,-34.2 20,-34.8 18.4,-34 17.8,-31.5 16.5,-28.6 15.2,-27 14.5,-22.5 11.8,-17 12.4,-13 13.8,-10.7 "
    "12.2,-6 12,-5 9.3,-1 9.8,3 8.5,4.5 6,4.3 4.5,6.2 2.5,6.3 1,5.9 -2,4.8 -4.5,5.2 -7.5,4.4 -9.5,5.4 "
    "-13,7.8 -13.8,9.5 -15.5,11.5 -16.8,13 -17.4,14.7 -16.5,16 -16,19 -17,21 -16,23.8 -14.5,26 "
    "-13.2,27.7 -9.8,29.5 -9.6,32 -6.8,34",
    "44,-25 43.3,-22 44.4,-16.2 47,-15.3 49.3,-12 50.4,-15.5 49.4,-18 47.2,-25",
    # Australia, Tasmania, New Zealand
    "113.5,-22 114,-26 115,-30 115.7,-32.5 115,-34.3 118,-35 123.5,-33.9 126,-32.3 131,-31.5 134.2,-32.8 "
    "135.9,-34.8 137.5,-34.5 138.5,-35.6 140,-37.5 143.5,-38.8 146.3,-39 148,-37.8 150,-37.5 150.2,-35.7 "
    "151.25,-34 151.4,-33.5 152.5,-32 153.6,-28.5 153,-25.5 150.8,-22.5 149,-20.5 146.3,-18.5 145.3,-15 "
    "143.5,-14 142.5,-10.7 141.5,-13 141.6,-16.5 140,-17.7 137.7,-16 135.5,-14.8 136.8,-12.2 132.5,-11.5 "
    "130,-13 129.5,-15 127.8,-14.3 125.8,-14.5 123.5,-16.5 122.2,-18 121,-19.6 117,-20.6",
    "144.6,-40.7 148.3,-40.9 148,-43.2 146.5,-43.6 145.2,-42.2",
    "172.7,-34.4 174.5,-36 175.9,-37.5 178.5,-37.7 177,-39.3 175,-41.5 174.6,-39.8 173.8,-39.2 174.5,-38",
    "172.6,-40.5 174.3,-41.5 173,-43.7 171,-45 169,-46.6 166.5,-46 167,-45 171.3,-42",
]

# Columns: set these to your table's column names
CITY = "City"  # role: label
LATITUDE = "Latitude (°)"  # role: latitude
LONGITUDE = "Longitude (°)"  # role: longitude
POPULATION = "Population (millions)"  # role: value
CONTINENT = "Continent"  # role: category

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
            "Manila",
            "Lagos",
            "Rio de Janeiro",
            "Guangzhou",
            "Los Angeles",
            "Moscow",
            "Paris",
            "Bangkok",
            "London",
            "Lima",
            "Seoul",
            "Sydney",
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
            14.60,
            6.52,
            -22.91,
            23.13,
            34.05,
            55.76,
            48.86,
            13.76,
            51.51,
            -12.05,
            37.57,
            -33.87,
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
            120.98,
            3.38,
            -43.17,
            113.26,
            -118.24,
            37.62,
            2.35,
            100.50,
            -0.13,
            -77.04,
            127.00,
            151.21,
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
            15.5,
            15.4,
            14.9,
            14.4,
            14.4,
            13.6,
            13.5,
            12.5,
            12.5,
            11.1,
            10.7,
            9.5,
            10.9,
            9.8,
            5.4,
        ],
        CONTINENT: [
            "Asia",
            "Asia",
            "Asia",
            "South America",
            "North America",
            "Africa",
            "Asia",
            "Asia",
            "Asia",
            "Asia",
            "North America",
            "Asia",
            "South America",
            "Europe",
            "Asia",
            "Asia",
            "Africa",
            "South America",
            "Asia",
            "North America",
            "Europe",
            "Europe",
            "Asia",
            "Europe",
            "South America",
            "Asia",
            "Oceania",
        ],
    }
)

# Plot: reads only df and the constants above
continents = list(df[CONTINENT].dropna().unique())
continent_palette = {c: IMPRINT_PALETTE[i] for i, c in enumerate(continents)}
value_max = df[POPULATION].max()

# Larger bubbles first, so smaller ones are drawn on top and never hidden
plot_df = df.sort_values(POPULATION, ascending=False)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
ax.set_xlim(*MAP_LON)
ax.set_ylim(*MAP_LAT)
ax.set_aspect("equal")

# Basemap: land in a quiet translucent neutral, ocean on the page background
for coastline in WORLD_COASTLINES:
    lons, lats = zip(*(map(float, point.split(",")) for point in coastline.split()), strict=True)
    ax.fill(lons, lats, facecolor=MUTED, alpha=0.18, edgecolor=MUTED, linewidth=0.5, zorder=1)

# Bubble area proportional to population: size_norm from 0 keeps area ∝ value
sns.scatterplot(
    data=plot_df,
    x=LONGITUDE,
    y=LATITUDE,
    hue=CONTINENT,
    hue_order=continents,
    size=POPULATION,
    sizes=(0, MAX_BUBBLE_AREA),
    size_norm=(0, value_max),
    palette=continent_palette,
    alpha=0.6,
    edgecolor=PAGE_BG,
    linewidth=0.8,
    legend=False,
    ax=ax,
    zorder=3,
)

# Legends side by side below the map, so the map can use the full width
continent_handles = [
    plt.scatter([], [], s=60, color=continent_palette[c], alpha=0.6, edgecolor=PAGE_BG, linewidth=0.8)
    for c in continents
]
continent_legend = fig.legend(
    continent_handles,
    continents,
    loc="lower right",
    bbox_to_anchor=(0.58, 0.02),
    ncol=-(-len(continents) // 2),
    fontsize=8,
    title=CONTINENT,
    title_fontsize=8,
    framealpha=0.95,
    columnspacing=1.2,
)

# Size legend: reference bubbles drawn like the data marks, at nice values within the data range
ref_values = [v for v in MaxNLocator(nbins=4).tick_values(0, value_max) if 0 < v <= value_max]
size_handles = [
    plt.scatter([], [], s=MAX_BUBBLE_AREA * v / value_max, color=MUTED, alpha=0.6, edgecolor=PAGE_BG, linewidth=0.8)
    for v in ref_values
]
fig.legend(
    size_handles,
    [f"{v:g}" for v in ref_values],
    loc="lower left",
    bbox_to_anchor=(0.6, 0.02),
    ncol=len(ref_values),
    fontsize=8,
    title=POPULATION,
    title_fontsize=8,
    framealpha=0.95,
    columnspacing=1.6,
    handletextpad=0.9,
    borderpad=0.7,
    handleheight=3.6,  # row tall enough for the largest reference bubble, clear of the title
)

# Style
ax.set_xlabel(LONGITUDE, fontsize=10)
ax.set_ylabel(LATITUDE, fontsize=10)
ax.set_title("bubble-map-geographic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8)
ax.grid(True, linestyle="--", linewidth=0.5)
ax.set_axisbelow(True)

fig.subplots_adjust(left=0.07, right=0.98, top=0.93, bottom=0.25)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
