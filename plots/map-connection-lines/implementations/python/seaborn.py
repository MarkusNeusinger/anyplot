""" pyplots.ai
map-connection-lines: Connection Lines Map (Origin-Destination)
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-21
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D


# Set seaborn style and context for large canvas
sns.set_theme(style="whitegrid")
sns.set_context("talk", font_scale=1.2)

# Sample data: Major international flight routes
np.random.seed(42)

routes = pd.DataFrame(
    {
        "origin": [
            "New York",
            "London",
            "Tokyo",
            "Sydney",
            "Dubai",
            "Singapore",
            "Los Angeles",
            "Paris",
            "Hong Kong",
            "Frankfurt",
            "New York",
            "London",
            "Dubai",
            "Singapore",
            "Tokyo",
        ],
        "origin_lat": [
            40.7128,
            51.5074,
            35.6762,
            -33.8688,
            25.2048,
            1.3521,
            34.0522,
            48.8566,
            22.3193,
            50.1109,
            40.7128,
            51.5074,
            25.2048,
            1.3521,
            35.6762,
        ],
        "origin_lon": [
            -74.0060,
            -0.1278,
            139.6503,
            151.2093,
            55.2708,
            103.8198,
            -118.2437,
            2.3522,
            114.1694,
            8.6821,
            -74.0060,
            -0.1278,
            55.2708,
            103.8198,
            139.6503,
        ],
        "dest": [
            "London",
            "Dubai",
            "Singapore",
            "Hong Kong",
            "Singapore",
            "Sydney",
            "Tokyo",
            "New York",
            "Tokyo",
            "Dubai",
            "Paris",
            "New York",
            "Sydney",
            "Tokyo",
            "Los Angeles",
        ],
        "dest_lat": [
            51.5074,
            25.2048,
            1.3521,
            22.3193,
            1.3521,
            -33.8688,
            35.6762,
            40.7128,
            35.6762,
            25.2048,
            48.8566,
            40.7128,
            -33.8688,
            35.6762,
            34.0522,
        ],
        "dest_lon": [
            -0.1278,
            55.2708,
            103.8198,
            114.1694,
            103.8198,
            151.2093,
            139.6503,
            -74.0060,
            139.6503,
            55.2708,
            2.3522,
            -74.0060,
            151.2093,
            139.6503,
            -118.2437,
        ],
        "passengers": [850, 620, 480, 390, 520, 410, 680, 790, 550, 430, 720, 810, 350, 490, 640],
    }
)

# Normalize passenger counts for line width (2-8 range)
routes["line_width"] = (
    2
    + (routes["passengers"] - routes["passengers"].min())
    / (routes["passengers"].max() - routes["passengers"].min())
    * 6
)

# Get unique airports for point plotting
airports_origin = routes[["origin", "origin_lat", "origin_lon"]].rename(
    columns={"origin": "city", "origin_lat": "lat", "origin_lon": "lon"}
)
airports_dest = routes[["dest", "dest_lat", "dest_lon"]].rename(
    columns={"dest": "city", "dest_lat": "lat", "dest_lon": "lon"}
)
airports = pd.concat([airports_origin, airports_dest]).drop_duplicates(subset="city")

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Draw simple world map outline (simplified coastline representation)
continents_x = [
    [-170, -130, -120, -100, -80, -70, -60, -80, -100, -120, -140, -170, -170],  # North America
    [-80, -70, -60, -40, -35, -40, -55, -70, -80, -80],  # South America
    [-10, 0, 10, 30, 40, 30, 20, 10, 0, -10, -10],  # Europe
    [-20, 0, 20, 40, 50, 40, 20, 0, -20, -20],  # Africa
    [40, 60, 80, 100, 120, 140, 150, 140, 120, 100, 80, 60, 40, 40],  # Asia
    [110, 120, 140, 150, 155, 150, 140, 120, 110, 110],  # Australia
]
continents_y = [
    [70, 70, 50, 50, 30, 25, 30, 15, 15, 30, 50, 60, 70],  # North America
    [10, 10, 0, -5, -20, -35, -55, -55, -20, 10],  # South America
    [35, 40, 45, 50, 60, 70, 70, 60, 50, 45, 35],  # Europe
    [35, 35, 30, 20, 0, -20, -35, -35, -20, 35],  # Africa
    [45, 50, 55, 60, 70, 70, 55, 40, 20, 10, 20, 30, 35, 45],  # Asia
    [-15, -15, -20, -25, -35, -40, -35, -30, -20, -15],  # Australia
]

for cx, cy in zip(continents_x, continents_y, strict=True):
    ax.fill(cx, cy, color="#E8E8E8", edgecolor="#CCCCCC", linewidth=1, alpha=0.5, zorder=0)

# Draw connection lines with varying width based on passenger volume (inline curve calculation)
n_points = 50
t = np.linspace(0, 1, n_points)

for _, row in routes.iterrows():
    lon1, lat1 = row["origin_lon"], row["origin_lat"]
    lon2, lat2 = row["dest_lon"], row["dest_lat"]

    # Calculate midpoint and curve height based on distance
    mid_lon = (lon1 + lon2) / 2
    mid_lat = (lat1 + lat2) / 2
    dist = np.sqrt((lon2 - lon1) ** 2 + (lat2 - lat1) ** 2)
    curve_height = dist * 0.15

    # Quadratic Bezier curve interpolation
    lons = (1 - t) ** 2 * lon1 + 2 * (1 - t) * t * mid_lon + t**2 * lon2
    lats = (1 - t) ** 2 * lat1 + 2 * (1 - t) * t * (mid_lat + curve_height) + t**2 * lat2

    ax.plot(lons, lats, color="#306998", linewidth=row["line_width"], alpha=0.4, solid_capstyle="round", zorder=1)

# Plot airport points using seaborn scatterplot
sns.scatterplot(
    data=airports,
    x="lon",
    y="lat",
    s=400,
    color="#FFD43B",
    edgecolor="#306998",
    linewidth=2,
    ax=ax,
    zorder=3,
    legend=False,
)

# Add city labels with custom offsets to avoid overlap in crowded regions
label_offsets = {
    "London": (-45, 12),
    "Paris": (-35, -18),
    "Frankfurt": (10, 12),
    "Hong Kong": (-55, -15),
    "Tokyo": (10, 10),
    "Singapore": (10, -15),
    "Dubai": (10, 10),
    "Sydney": (10, 10),
    "New York": (10, 10),
    "Los Angeles": (-70, -15),
}

for _, row in airports.iterrows():
    offset = label_offsets.get(row["city"], (10, 10))
    ax.annotate(
        row["city"],
        xy=(row["lon"], row["lat"]),
        xytext=offset,
        textcoords="offset points",
        fontsize=14,
        fontweight="bold",
        color="#333333",
        zorder=4,
    )

# Styling with degree units on axis labels
ax.set_xlabel("Longitude (°)", fontsize=20)
ax.set_ylabel("Latitude (°)", fontsize=20)
ax.set_title("map-connection-lines · seaborn · pyplots.ai", fontsize=24, fontweight="bold")
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim(-180, 180)
ax.set_ylim(-60, 80)
ax.set_aspect("equal", adjustable="box")
ax.grid(True, alpha=0.3, linestyle="--")

# Add legend showing actual passenger ranges (not categorical)
min_pass, max_pass = routes["passengers"].min(), routes["passengers"].max()
legend_elements = [
    Line2D([0], [0], color="#306998", linewidth=2, alpha=0.6, label=f"{min_pass}k passengers"),
    Line2D([0], [0], color="#306998", linewidth=5, alpha=0.6, label=f"{(min_pass + max_pass) // 2}k passengers"),
    Line2D([0], [0], color="#306998", linewidth=8, alpha=0.6, label=f"{max_pass}k passengers"),
]
ax.legend(handles=legend_elements, loc="lower left", fontsize=14, title="Annual Passengers", title_fontsize=16)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
