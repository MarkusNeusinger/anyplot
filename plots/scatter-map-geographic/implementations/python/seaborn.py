""" pyplots.ai
scatter-map-geographic: Scatter Map with Geographic Points
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-10
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Simplified world coastline polygons (major continents outline)
# Each polygon is a list of (lon, lat) coordinates
WORLD_COASTLINES = [
    # North America (simplified)
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
    # South America (simplified)
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
    # Europe (simplified)
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
    # Africa (simplified)
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
    # Asia (simplified, excluding Russia)
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
    # Australia (simplified)
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
    # Antarctica hint (just a line)
    [(-180, -60), (-120, -65), (-60, -60), (0, -68), (60, -65), (120, -68), (180, -60)],
]

# Data: Major world cities with population (earthquake epicenters scenario would also work)
np.random.seed(42)

cities_data = {
    "city": [
        "Tokyo",
        "New York",
        "London",
        "Sydney",
        "Paris",
        "Dubai",
        "Singapore",
        "Mumbai",
        "Cairo",
        "São Paulo",
        "Toronto",
        "Shanghai",
        "Moscow",
        "Seoul",
        "Los Angeles",
        "Berlin",
        "Bangkok",
        "Jakarta",
        "Cape Town",
        "Buenos Aires",
        "Mexico City",
        "Istanbul",
        "Lagos",
        "Chicago",
        "Hong Kong",
    ],
    "latitude": [
        35.7,
        40.7,
        51.5,
        -33.9,
        48.9,
        25.2,
        1.3,
        19.1,
        30.0,
        -23.6,
        43.7,
        31.2,
        55.8,
        37.6,
        34.1,
        52.5,
        13.8,
        -6.2,
        -33.9,
        -34.6,
        19.4,
        41.0,
        6.5,
        41.9,
        22.3,
    ],
    "longitude": [
        139.7,
        -74.0,
        -0.1,
        151.2,
        2.4,
        55.3,
        103.8,
        72.9,
        31.2,
        -46.6,
        -79.4,
        121.5,
        37.6,
        127.0,
        -118.2,
        13.4,
        100.5,
        106.8,
        18.4,
        -58.4,
        -99.1,
        29.0,
        3.4,
        -87.6,
        114.2,
    ],
    "population": [
        37.4,
        18.8,
        9.5,
        5.3,
        11.0,
        3.4,
        5.7,
        21.0,
        20.9,
        22.4,
        6.3,
        27.8,
        12.5,
        9.8,
        12.5,
        3.7,
        10.7,
        10.6,
        4.6,
        15.4,
        21.8,
        15.5,
        15.4,
        8.9,
        7.5,
    ],
    "region": [
        "Asia",
        "North America",
        "Europe",
        "Oceania",
        "Europe",
        "Asia",
        "Asia",
        "Asia",
        "Africa",
        "South America",
        "North America",
        "Asia",
        "Europe",
        "Asia",
        "North America",
        "Europe",
        "Asia",
        "Asia",
        "Africa",
        "South America",
        "North America",
        "Europe",
        "Africa",
        "North America",
        "Asia",
    ],
}

df = pd.DataFrame(cities_data)

# Set seaborn theme
sns.set_theme(style="whitegrid", context="talk", font_scale=1.1)

# Create figure with appropriate size for 4800x2700 output
fig, ax = plt.subplots(figsize=(16, 9))

# Set map extent (world map)
ax.set_xlim(-180, 180)
ax.set_ylim(-75, 85)
ax.set_aspect("equal")

# Draw simplified coastlines as background
for coastline in WORLD_COASTLINES:
    if len(coastline) > 2:
        lons = [p[0] for p in coastline]
        lats = [p[1] for p in coastline]
        ax.fill(lons, lats, color="#e8e8e8", edgecolor="#b0b0b0", linewidth=1, alpha=0.8, zorder=1)

# Draw ocean background
ax.set_facecolor("#d4e8f7")

# Create color palette for regions
region_palette = {
    "Asia": "#306998",  # Python Blue
    "Europe": "#FFD43B",  # Python Yellow
    "North America": "#E07B53",
    "South America": "#5AAE61",
    "Africa": "#9D6AB8",
    "Oceania": "#2DB5AE",
}

# Scale population for marker sizes (visible at 4800x2700)
# Population range: ~3 to ~37 million -> marker size 150-800
min_pop, max_pop = df["population"].min(), df["population"].max()
df["marker_size"] = 150 + (df["population"] - min_pop) / (max_pop - min_pop) * 650

# Plot scatter points using seaborn
sns.scatterplot(
    data=df,
    x="longitude",
    y="latitude",
    hue="region",
    size="population",
    sizes=(150, 800),
    palette=region_palette,
    alpha=0.8,
    edgecolor="white",
    linewidth=1.5,
    ax=ax,
    zorder=3,
    legend="full",
)

# Customize legend
handles, labels = ax.get_legend_handles_labels()
# Separate region and size legends
legend = ax.legend(
    handles[:7],
    labels[:7],  # Region legend (includes title)
    loc="lower left",
    fontsize=16,
    title="Region",
    title_fontsize=18,
    framealpha=0.95,
    edgecolor="#cccccc",
)
ax.add_artist(legend)

# Add separate size legend
size_legend_elements = [
    plt.scatter([], [], s=150, c="gray", alpha=0.6, label="5M"),
    plt.scatter([], [], s=400, c="gray", alpha=0.6, label="20M"),
    plt.scatter([], [], s=800, c="gray", alpha=0.6, label="35M+"),
]
size_legend = ax.legend(
    handles=size_legend_elements,
    loc="lower right",
    fontsize=16,
    title="Population",
    title_fontsize=18,
    framealpha=0.95,
    edgecolor="#cccccc",
)

# Labels and styling
ax.set_xlabel("Longitude (°)", fontsize=20)
ax.set_ylabel("Latitude (°)", fontsize=20)
ax.set_title("scatter-map-geographic · seaborn · pyplots.ai", fontsize=26, fontweight="bold", pad=20)
ax.tick_params(axis="both", labelsize=16)

# Subtle grid
ax.grid(True, alpha=0.3, linestyle="--", color="#888888")
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
