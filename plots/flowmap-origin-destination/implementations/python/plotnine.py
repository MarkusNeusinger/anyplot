""" pyplots.ai
flowmap-origin-destination: Origin-Destination Flow Map
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-16
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_polygon,
    ggplot,
    labs,
    scale_color_gradient,
    scale_size_identity,
    theme,
    theme_minimal,
)


# Seed for reproducibility
np.random.seed(42)

# Major world cities for origin-destination flows (shipping/trade routes)
locations = {
    "Shanghai": (31.23, 121.47),
    "Singapore": (1.35, 103.82),
    "Rotterdam": (51.92, 4.48),
    "Los Angeles": (33.75, -118.24),
    "Dubai": (25.20, 55.27),
    "Hong Kong": (22.32, 114.17),
    "Tokyo": (35.68, 139.69),
    "New York": (40.71, -74.01),
    "Hamburg": (53.55, 9.99),
    "Busan": (35.18, 129.08),
    "Santos": (-23.96, -46.33),
    "Mumbai": (19.08, 72.88),
    "Sydney": (-33.87, 151.21),
    "Cape Town": (-33.92, 18.42),
    "Vancouver": (49.28, -123.12),
}

# Define trade/shipping flows with volume (in arbitrary units representing container volume)
flows_data = [
    ("Shanghai", "Rotterdam", 95),
    ("Shanghai", "Los Angeles", 88),
    ("Shanghai", "Singapore", 75),
    ("Singapore", "Rotterdam", 65),
    ("Hong Kong", "Los Angeles", 62),
    ("Busan", "Los Angeles", 58),
    ("Shanghai", "Hamburg", 55),
    ("Dubai", "Rotterdam", 52),
    ("Shanghai", "New York", 50),
    ("Tokyo", "Los Angeles", 48),
    ("Singapore", "Dubai", 45),
    ("Mumbai", "Rotterdam", 42),
    ("Hong Kong", "New York", 40),
    ("Rotterdam", "New York", 38),
    ("Santos", "Rotterdam", 35),
    ("Shanghai", "Sydney", 33),
    ("Cape Town", "Rotterdam", 30),
    ("Singapore", "Sydney", 28),
    ("Vancouver", "Tokyo", 25),
    ("Dubai", "Mumbai", 22),
]


def bezier_curve(p0, p1, curvature=0.3, n_points=50):
    """Generate points along a quadratic Bezier curve between two points."""
    # Calculate midpoint and perpendicular offset for control point
    mid_x = (p0[0] + p1[0]) / 2
    mid_y = (p0[1] + p1[1]) / 2

    # Calculate perpendicular direction
    dx = p1[0] - p0[0]
    dy = p1[1] - p0[1]
    length = np.sqrt(dx**2 + dy**2)

    # Perpendicular offset (positive for clockwise curve)
    perp_x = -dy / length if length > 0 else 0
    perp_y = dx / length if length > 0 else 0

    # Control point with curvature
    ctrl_x = mid_x + perp_x * length * curvature
    ctrl_y = mid_y + perp_y * length * curvature

    # Generate Bezier curve points
    t = np.linspace(0, 1, n_points)
    x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * ctrl_x + t**2 * p1[0]
    y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * ctrl_y + t**2 * p1[1]

    return x, y


# Build flow paths dataframe
flow_paths = []
for i, (origin, dest, flow) in enumerate(flows_data):
    origin_lat, origin_lon = locations[origin]
    dest_lat, dest_lon = locations[dest]

    # Generate curved path
    curve_x, curve_y = bezier_curve((origin_lon, origin_lat), (dest_lon, dest_lat), curvature=0.25, n_points=40)

    # Normalize flow for line width (scale to reasonable range)
    line_width = 0.3 + (flow / 95) * 2.0  # Range: 0.3 to 2.3

    for j, (x, y) in enumerate(zip(curve_x, curve_y, strict=False)):
        flow_paths.append(
            {"flow_id": i, "order": j, "x": x, "y": y, "flow": flow, "size": line_width, "route": f"{origin} → {dest}"}
        )

df_flows = pd.DataFrame(flow_paths)

# Build location points dataframe
location_points = []
for name, (lat, lon) in locations.items():
    location_points.append({"name": name, "lat": lat, "lon": lon})
df_locations = pd.DataFrame(location_points)

# Simplified continent outlines for basemap
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
au_lon = [113, 125, 135, 145, 152, 150, 140, 130, 115, 113]
au_lat = [-22, -15, -12, -15, -25, -38, -38, -33, -35, -22]
for i in range(len(au_lon)):
    continents.append({"continent": "Australia", "order": i, "lon": au_lon[i], "lat": au_lat[i]})

df_continents = pd.DataFrame(continents)

# Create the flow map visualization
plot = (
    ggplot()
    # Draw continent polygons as basemap
    + geom_polygon(
        aes(x="lon", y="lat", group="continent"),
        data=df_continents,
        fill="#E8E8E8",
        color="#B0B0B0",
        size=0.4,
        alpha=0.9,
    )
    # Draw flow arcs with width proportional to flow volume
    + geom_path(
        aes(x="x", y="y", group="flow_id", color="flow", size="size"), data=df_flows, alpha=0.55, lineend="round"
    )
    # Draw origin/destination points
    + geom_point(aes(x="lon", y="lat"), data=df_locations, color="#306998", size=4, alpha=0.9)
    # Scale settings
    + scale_size_identity()
    + scale_color_gradient(low="#FFD43B", high="#D62728", name="Flow Volume")
    + coord_fixed(ratio=1.3, xlim=(-180, 180), ylim=(-60, 80))
    + labs(
        title="Global Shipping Routes · flowmap-origin-destination · plotnine · pyplots.ai",
        x="Longitude (°)",
        y="Latitude (°)",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=22, weight="bold"),
        axis_title=element_text(size=18),
        axis_text=element_text(size=14),
        legend_title=element_text(size=16),
        legend_text=element_text(size=12),
        legend_position="right",
        panel_grid_major=element_line(color="#DDDDDD", size=0.3, alpha=0.4),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill="#D4E8F7", alpha=0.6),
    )
)

# Save at 300 DPI for 4800x2700 px output
plot.save("plot.png", dpi=300, verbose=False)
