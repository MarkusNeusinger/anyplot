"""anyplot.ai
scatter-map-geographic: Scatter Map with Geographic Points
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-18
"""

import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (first series always brand green)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Seaborn theme (setup belongs in the head)
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
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Constants
# Simplified world coastline polygons (basemap, longitude/latitude pairs)
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
LATITUDE = "Latitude (°)"  # role: latitude
LONGITUDE = "Longitude (°)"  # role: longitude
VOLCANO_TYPE = "Volcano type"  # role: value
ELEVATION = "Summit elevation (m)"  # role: size
NAME = "Volcano"  # role: label

# Data: replace this block with your own table, for example df = pd.read_csv("volcanoes.csv")
df = pd.DataFrame(
    {
        NAME: [
            "Fuji",
            "Etna",
            "Vesuvius",
            "Kilimanjaro",
            "Mauna Loa",
            "Kilauea",
            "Popocatépetl",
            "Cotopaxi",
            "Villarrica",
            "Mount St. Helens",
            "Rainier",
            "Krakatau",
            "Merapi",
            "Tambora",
            "Pinatubo",
            "Yellowstone",
            "Eyjafjallajökull",
            "Teide",
            "Piton de la Fournaise",
            "Nyiragongo",
            "Ol Doinyo Lengai",
            "Taal",
            "Ngauruhoe",
            "Aso",
            "Sakurajima",
            "Santorini",
            "Fogo",
            "Fernandina",
            "Katla",
        ],
        LATITUDE: [
            35.36,
            37.75,
            40.82,
            -3.07,
            19.48,
            19.42,
            19.02,
            -0.68,
            -39.42,
            46.20,
            46.85,
            -6.10,
            -7.54,
            -8.25,
            15.13,
            44.43,
            63.63,
            28.27,
            -21.24,
            -1.52,
            -2.76,
            14.00,
            -39.16,
            32.88,
            31.59,
            36.40,
            14.95,
            -0.37,
            63.63,
        ],
        LONGITUDE: [
            138.73,
            14.99,
            14.43,
            37.35,
            -155.60,
            -155.29,
            -98.62,
            -78.44,
            -71.93,
            -122.18,
            -121.76,
            105.42,
            110.44,
            118.00,
            120.35,
            -110.67,
            -19.62,
            -16.64,
            55.71,
            29.25,
            35.91,
            120.99,
            175.63,
            131.10,
            130.66,
            25.40,
            -24.35,
            -91.55,
            -19.05,
        ],
        ELEVATION: [
            3776,
            3357,
            1281,
            5895,
            4169,
            1247,
            5426,
            5897,
            2847,
            2549,
            4392,
            813,
            2910,
            2850,
            1486,
            2805,
            1651,
            3715,
            2632,
            3470,
            2962,
            311,
            2291,
            1592,
            1117,
            367,
            2829,
            1476,
            1512,
        ],
        VOLCANO_TYPE: [
            "Stratovolcano",
            "Stratovolcano",
            "Stratovolcano",
            "Stratovolcano",
            "Shield",
            "Shield",
            "Stratovolcano",
            "Stratovolcano",
            "Stratovolcano",
            "Stratovolcano",
            "Stratovolcano",
            "Caldera",
            "Stratovolcano",
            "Caldera",
            "Stratovolcano",
            "Caldera",
            "Stratovolcano",
            "Stratovolcano",
            "Shield",
            "Stratovolcano",
            "Stratovolcano",
            "Caldera",
            "Stratovolcano",
            "Caldera",
            "Stratovolcano",
            "Caldera",
            "Stratovolcano",
            "Shield",
            "Caldera",
        ],
    }
)

# Plot: reads only df and the constants above
types = df[VOLCANO_TYPE].unique()
type_colors = {t: IMPRINT_PALETTE[i] for i, t in enumerate(types)}

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

# Basemap: quiet land masses behind the points
land_color = "#E8E8E0" if THEME == "light" else "#2A2A26"
land_edge = "#A8A7A0" if THEME == "light" else "#505050"
for coastline in WORLD_COASTLINES:
    lons = [lon for lon, _ in coastline]
    lats = [lat for _, lat in coastline]
    ax.fill(lons, lats, color=land_color, edgecolor=land_edge, linewidth=0.4, alpha=0.7, zorder=1)

sns.scatterplot(
    data=df,
    x=LONGITUDE,
    y=LATITUDE,
    hue=VOLCANO_TYPE,
    size=ELEVATION,
    sizes=(20, 160),
    palette=type_colors,
    alpha=0.8,
    edgecolor=PAGE_BG,
    linewidth=0.5,
    ax=ax,
    zorder=3,
)

# Split seaborn's combined legend into a type legend and an elevation legend
handles, labels = ax.get_legend_handles_labels()
split = labels.index(ELEVATION)
type_legend = ax.legend(
    handles[1:split], labels[1:split], loc="lower left", fontsize=7, title_fontsize=8, framealpha=0.9
)
ax.add_artist(type_legend)
type_legend.set_title(VOLCANO_TYPE)
size_legend = ax.legend(
    handles[split + 1 :],
    labels[split + 1 :],
    title=ELEVATION,
    loc="lower center",
    bbox_to_anchor=(0.6, 0),
    ncol=len(labels) - split - 1,
    fontsize=7,
    title_fontsize=8,
    framealpha=0.9,
)
# Size keys are neutral grey: visible on both surfaces
for key in size_legend.legend_handles:
    key.set_markerfacecolor(INK_SOFT)
    key.set_markeredgecolor(INK_SOFT)
    key.set_alpha(0.7)

# Map extent in degrees (fixed domain of the coordinates)
ax.set_xlim(-180, 180)
ax.set_ylim(-60, 85)
ax.set_aspect("equal")

ax.set_title("scatter-map-geographic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(LONGITUDE, fontsize=10)
ax.set_ylabel(LATITUDE, fontsize=10)
ax.tick_params(axis="both", labelsize=8)

ax.grid(True, alpha=0.10, linestyle="-", linewidth=0.5, color=INK_SOFT)
ax.set_axisbelow(True)
sns.despine(ax=ax)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
