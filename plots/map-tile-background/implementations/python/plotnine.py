""" pyplots.ai
map-tile-background: Map with Tile Background
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-20
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_label,
    geom_point,
    geom_polygon,
    geom_rect,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_size_continuous,
    theme,
    theme_minimal,
)


# Seed for reproducibility
np.random.seed(42)

# San Francisco Bay Area landmarks with visitor counts (thousands per year)
landmarks_data = {
    "name": [
        "Golden Gate Bridge",
        "Alcatraz Island",
        "Fisherman's Wharf",
        "Pier 39",
        "Cable Cars",
        "Chinatown",
        "Union Square",
        "Ferry Building",
        "Palace of Fine Arts",
        "Coit Tower",
        "AT&T Park",
        "Exploratorium",
        "de Young Museum",
        "California Academy",
        "Lombard Street",
    ],
    "lat": [
        37.8199,
        37.8267,
        37.8080,
        37.8087,
        37.7873,
        37.7941,
        37.7879,
        37.7955,
        37.8020,
        37.8024,
        37.7786,
        37.8016,
        37.7714,
        37.7699,
        37.8021,
    ],
    "lon": [
        -122.4783,
        -122.4230,
        -122.4177,
        -122.4098,
        -122.4119,
        -122.4070,
        -122.4075,
        -122.3935,
        -122.4486,
        -122.4058,
        -122.3893,
        -122.3976,
        -122.4687,
        -122.4663,
        -122.4187,
    ],
    "visitors": [10500, 1700, 12000, 10000, 7000, 2000, 15000, 6000, 2000, 500, 3500, 1000, 1200, 2500, 2000],
    "category": [
        "Landmark",
        "Historic",
        "Tourism",
        "Tourism",
        "Transport",
        "Cultural",
        "Shopping",
        "Tourism",
        "Landmark",
        "Landmark",
        "Sports",
        "Museum",
        "Museum",
        "Museum",
        "Landmark",
    ],
}

df = pd.DataFrame(landmarks_data)

# Simulated tile-style background using grid rectangles
# This creates a visual effect similar to map tiles
lon_min, lon_max = -122.52, -122.36
lat_min, lat_max = 37.755, 37.84

# Create grid cells that simulate map tiles (10x8 grid)
n_tiles_x = 10
n_tiles_y = 8
tile_width = (lon_max - lon_min) / n_tiles_x
tile_height = (lat_max - lat_min) / n_tiles_y

# Generate tile background with terrain-like coloring
tiles = []
tile_id = 0
for i in range(n_tiles_x):
    for j in range(n_tiles_y):
        x_center = lon_min + tile_width * (i + 0.5)
        y_center = lat_min + tile_height * (j + 0.5)

        # Determine terrain type based on position (simulating land/water)
        # Water on east side (bay) and portions of north (golden gate strait)
        is_water = (
            (x_center > -122.39 and y_center < 37.79)
            or (x_center > -122.44 and y_center > 37.825)
            or (x_center > -122.37)
        )

        tiles.append(
            {
                "xmin": lon_min + tile_width * i,
                "xmax": lon_min + tile_width * (i + 1),
                "ymin": lat_min + tile_height * j,
                "ymax": lat_min + tile_height * (j + 1),
                "terrain": "water" if is_water else "land",
                "tile_id": tile_id,
            }
        )
        tile_id += 1

df_tiles = pd.DataFrame(tiles)

# Coastline polygon (San Francisco peninsula outline for visible area)
coast_coords = [
    (-122.52, 37.755),
    (-122.48, 37.755),
    (-122.42, 37.76),
    (-122.39, 37.77),
    (-122.37, 37.785),
    (-122.36, 37.80),
    (-122.38, 37.815),
    (-122.42, 37.82),
    (-122.46, 37.825),
    (-122.50, 37.82),
    (-122.52, 37.80),
    (-122.52, 37.755),
]

coastline = [{"region": "sf", "order": i, "lon": c[0], "lat": c[1]} for i, c in enumerate(coast_coords)]
df_coast = pd.DataFrame(coastline)

# Category color palette (colorblind-safe)
category_colors = {
    "Cultural": "#9467BD",
    "Historic": "#8C564B",
    "Landmark": "#306998",
    "Museum": "#2CA02C",
    "Shopping": "#FFD43B",
    "Sports": "#D62728",
    "Tourism": "#17BECF",
    "Transport": "#FF7F0E",
}

# Prepare label data with individual position adjustments to avoid overlap
# Select top attractions by visitor count
top_attractions = df[df["visitors"] >= 10000].copy()

# Create label positions with nudge offsets to prevent overlap
# Labels positioned with significant separation to avoid any touching
label_positions = {
    "Golden Gate Bridge": {"nudge_x": 0.01, "nudge_y": 0.016},
    "Fisherman's Wharf": {"nudge_x": -0.055, "nudge_y": 0.02},
    "Pier 39": {"nudge_x": 0.045, "nudge_y": -0.025},
    "Union Square": {"nudge_x": 0.025, "nudge_y": 0.015},
}

# Build label dataframe with adjusted positions
label_records = []
for _, row in top_attractions.iterrows():
    pos = label_positions.get(row["name"], {"nudge_x": 0, "nudge_y": 0.012})
    label_records.append({"name": row["name"], "lon": row["lon"] + pos["nudge_x"], "lat": row["lat"] + pos["nudge_y"]})
label_df = pd.DataFrame(label_records)

# Create the map visualization
plot = (
    ggplot()
    # Layer 1: Tile background rectangles
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="terrain"),
        data=df_tiles,
        color="#AAAAAA",
        size=0.15,
        alpha=0.8,
    )
    + scale_fill_manual(values={"water": "#B8D4E8", "land": "#E8E4D8"}, guide=None)
    # Layer 2: Coastline outline for geographic context
    + geom_polygon(
        aes(x="lon", y="lat", group="region"), data=df_coast, fill="none", color="#444444", size=1.2, alpha=1.0
    )
    # Layer 3: Data points with size encoding for visitor counts
    + geom_point(aes(x="lon", y="lat", color="category", size="visitors"), data=df, alpha=0.85, stroke=1.2)
    + scale_size_continuous(range=(5, 20), name="Visitors\n(thousands/yr)")
    + scale_color_manual(values=category_colors, name="Category")
    # Layer 4: Labels for top landmarks (positions pre-adjusted in label_df)
    + geom_label(
        aes(x="lon", y="lat", label="name"), data=label_df, size=9, alpha=0.9, fill="white", label_padding=0.25
    )
    # Attribution for simulated tile background (spec requirement)
    + annotate(
        "text",
        x=lon_max - 0.01,
        y=lat_min + 0.005,
        label="Simulated tiles | Data: SF landmarks",
        size=7,
        ha="right",
        va="bottom",
        color="#666666",
        alpha=0.8,
    )
    # Coordinate system with proper aspect ratio for geographic accuracy
    + coord_fixed(ratio=1.3, xlim=(lon_min, lon_max), ylim=(lat_min, lat_max))
    + labs(title="SF Landmarks · map-tile-background · plotnine · pyplots.ai", x="Longitude (°)", y="Latitude (°)")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=20, weight="bold", ha="center"),
        axis_title=element_text(size=18),
        axis_text=element_text(size=14),
        legend_title=element_text(size=14),
        legend_text=element_text(size=11),
        legend_position="right",
        legend_box_spacing=0.1,
        legend_key_size=16,
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill="none"),
        plot_margin=0.02,
    )
)

# Save at 300 DPI for 4800x2700 px output
plot.save("plot.png", dpi=300, verbose=False)
