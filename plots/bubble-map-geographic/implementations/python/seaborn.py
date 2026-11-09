"""anyplot.ai
bubble-map-geographic: Bubble Map with Sized Geographic Markers
Library: seaborn 0.13.2 | Python 3.14.9
Quality: 81/100 | Updated: 2026-11-09
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
MAP_LAT = (-70, 85)
MAX_BUBBLE_AREA = 600  # marker area (pt²) of the largest value; area is proportional to the value

# Simplified world coastline polygons (major continents outline), as (lon, lat)
WORLD_COASTLINES = [
    # North America
    [
        (-168, 66),
        (-141, 70),
        (-130, 70),
        (-120, 60),
        (-125, 50),
        (-125, 40),
        (-117, 33),
        (-105, 25),
        (-97, 26),
        (-82, 25),
        (-81, 30),
        (-75, 35),
        (-70, 42),
        (-67, 45),
        (-60, 47),
        (-55, 52),
        (-60, 60),
        (-65, 68),
        (-80, 70),
        (-100, 73),
        (-120, 75),
        (-145, 72),
        (-168, 66),
    ],
    # South America
    [
        (-82, 10),
        (-77, 0),
        (-80, -5),
        (-70, -15),
        (-60, -5),
        (-50, 0),
        (-35, -5),
        (-40, -23),
        (-55, -35),
        (-68, -55),
        (-75, -50),
        (-75, -40),
        (-70, -20),
        (-80, -5),
        (-82, 10),
    ],
    # Europe
    [
        (-10, 36),
        (-10, 45),
        (-5, 48),
        (0, 52),
        (5, 55),
        (10, 58),
        (20, 60),
        (28, 70),
        (35, 70),
        (30, 60),
        (25, 55),
        (20, 50),
        (15, 45),
        (20, 40),
        (25, 35),
        (35, 35),
        (28, 42),
        (20, 38),
        (10, 38),
        (-10, 36),
    ],
    # Africa
    [
        (-17, 15),
        (-17, 28),
        (-5, 36),
        (10, 38),
        (20, 33),
        (35, 30),
        (45, 12),
        (52, 12),
        (45, 0),
        (42, -10),
        (35, -25),
        (25, -34),
        (18, -35),
        (12, -20),
        (15, -5),
        (5, 5),
        (-10, 5),
        (-17, 15),
    ],
    # Asia
    [
        (35, 30),
        (45, 42),
        (52, 45),
        (70, 42),
        (80, 30),
        (75, 15),
        (90, 22),
        (100, 15),
        (105, 22),
        (110, 5),
        (120, 25),
        (130, 35),
        (140, 45),
        (145, 55),
        (135, 70),
        (100, 78),
        (70, 75),
        (50, 70),
        (30, 70),
        (35, 50),
        (45, 45),
        (35, 30),
    ],
    # Australia
    [
        (113, -22),
        (120, -18),
        (135, -12),
        (145, -15),
        (152, -25),
        (150, -38),
        (140, -38),
        (130, -33),
        (115, -35),
        (113, -22),
    ],
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
    lons, lats = zip(*coastline, strict=True)
    ax.fill(lons, lats, facecolor=MUTED, alpha=0.18, edgecolor=MUTED, linewidth=0.6, zorder=1)

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

# Continent legend
continent_handles = [
    plt.scatter([], [], s=60, color=continent_palette[c], alpha=0.6, edgecolor=PAGE_BG, linewidth=0.8)
    for c in continents
]
continent_legend = ax.legend(
    continent_handles,
    continents,
    loc="upper left",
    bbox_to_anchor=(1.02, 1.0),
    fontsize=8,
    title=CONTINENT,
    title_fontsize=8,
    framealpha=0.95,
    labelspacing=0.35,
)
ax.add_artist(continent_legend)

# Size legend: reference bubbles drawn like the data marks, at nice values within the data range
ref_values = [v for v in MaxNLocator(nbins=4).tick_values(0, value_max) if 0 < v <= value_max]
size_handles = [
    plt.scatter([], [], s=MAX_BUBBLE_AREA * v / value_max, color=MUTED, alpha=0.6, edgecolor=PAGE_BG, linewidth=0.8)
    for v in ref_values
]
ax.legend(
    size_handles,
    [f"{v:g}" for v in ref_values],
    loc="lower left",
    bbox_to_anchor=(1.02, 0.0),
    fontsize=8,
    title=POPULATION,
    title_fontsize=8,
    framealpha=0.95,
    labelspacing=1.35,
    borderpad=0.7,
)

# Style
ax.set_xlabel(LONGITUDE, fontsize=10)
ax.set_ylabel(LATITUDE, fontsize=10)
ax.set_title("bubble-map-geographic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8)
ax.grid(True, linestyle="--", linewidth=0.5)
ax.set_axisbelow(True)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
