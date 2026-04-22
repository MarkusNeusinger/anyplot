""" pyplots.ai
flowmap-origin-destination: Origin-Destination Flow Map
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-16
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_text,
    geom_curve,
    geom_point,
    geom_polygon,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_gradient,
    scale_size,
    theme,
    theme_void,
    xlim,
    ylim,
)


LetsPlot.setup_html()

# Data: Major trade flows between world regions (simplified)
np.random.seed(42)

# Define major hub cities with coordinates
hubs = {
    "Los Angeles": (-118.24, 34.05),
    "New York": (-74.01, 40.71),
    "London": (-0.13, 51.51),
    "Rotterdam": (4.48, 51.92),
    "Dubai": (55.27, 25.20),
    "Singapore": (103.82, 1.35),
    "Shanghai": (121.47, 31.23),
    "Tokyo": (139.69, 35.69),
    "Sydney": (151.21, -33.87),
    "Sao Paulo": (-46.63, -23.55),
}

# Create trade flow connections
flows = [
    ("Shanghai", "Los Angeles", 85),
    ("Shanghai", "Rotterdam", 72),
    ("Singapore", "Rotterdam", 65),
    ("Tokyo", "Los Angeles", 58),
    ("Rotterdam", "New York", 52),
    ("Dubai", "London", 48),
    ("Shanghai", "Singapore", 45),
    ("Los Angeles", "Tokyo", 42),
    ("Singapore", "Sydney", 38),
    ("Sao Paulo", "Rotterdam", 35),
    ("New York", "London", 32),
    ("Dubai", "Singapore", 30),
    ("Shanghai", "Dubai", 28),
    ("Rotterdam", "Dubai", 25),
    ("London", "New York", 22),
    ("Sydney", "Singapore", 20),
    ("Tokyo", "Shanghai", 18),
    ("Los Angeles", "Shanghai", 15),
]

# Build dataframe for flows
flow_data = []
for origin, dest, volume in flows:
    o_lon, o_lat = hubs[origin]
    d_lon, d_lat = hubs[dest]
    flow_data.append(
        {
            "origin_name": origin,
            "dest_name": dest,
            "origin_lon": o_lon,
            "origin_lat": o_lat,
            "dest_lon": d_lon,
            "dest_lat": d_lat,
            "flow": volume,
        }
    )

df_flows = pd.DataFrame(flow_data)

# Build dataframe for hub points
hub_data = [{"name": name, "lon": lon, "lat": lat} for name, (lon, lat) in hubs.items()]
df_hubs = pd.DataFrame(hub_data)

# Simple world boundary polygon (simplified coastline approximation)
world_coords = [
    # North America
    (-170, 70),
    (-140, 70),
    (-120, 60),
    (-100, 50),
    (-80, 45),
    (-70, 45),
    (-60, 50),
    (-55, 50),
    (-55, 45),
    (-80, 25),
    (-100, 20),
    (-120, 30),
    (-130, 50),
    (-170, 60),
    (-170, 70),
    # Break
    (None, None),
    # South America
    (-80, 10),
    (-60, 5),
    (-35, -5),
    (-40, -20),
    (-55, -25),
    (-70, -55),
    (-75, -45),
    (-80, -5),
    (-80, 10),
    (None, None),
    # Europe/Africa
    (-10, 60),
    (30, 70),
    (40, 65),
    (30, 45),
    (10, 35),
    (-10, 35),
    (-20, 15),
    (50, 10),
    (45, -35),
    (20, -35),
    (10, 5),
    (-20, 10),
    (-10, 60),
    (None, None),
    # Asia
    (30, 70),
    (70, 75),
    (180, 70),
    (160, 60),
    (140, 50),
    (130, 45),
    (120, 30),
    (105, 20),
    (90, 25),
    (70, 25),
    (55, 25),
    (45, 30),
    (35, 35),
    (30, 45),
    (30, 70),
    (None, None),
    # Australia
    (115, -20),
    (150, -10),
    (155, -25),
    (150, -40),
    (135, -35),
    (115, -35),
    (115, -20),
]

# Split into separate polygons
polygons = []
current_poly = []
for lon, lat in world_coords:
    if lon is None:
        if current_poly:
            polygons.append(current_poly)
            current_poly = []
    else:
        current_poly.append((lon, lat))
if current_poly:
    polygons.append(current_poly)

# Create world polygon dataframe
world_data = []
for i, poly in enumerate(polygons):
    for lon, lat in poly:
        world_data.append({"x": lon, "y": lat, "group": i})
df_world = pd.DataFrame(world_data)

# Create the plot
plot = (
    ggplot()
    # World background
    + geom_polygon(data=df_world, mapping=aes(x="x", y="y", group="group"), fill="#E8E8E8", color="#CCCCCC", size=0.3)
    # Flow arcs with curvature
    + geom_curve(
        data=df_flows,
        mapping=aes(x="origin_lon", y="origin_lat", xend="dest_lon", yend="dest_lat", size="flow", color="flow"),
        curvature=-0.3,
        alpha=0.6,
    )
    # Origin/destination hub points
    + geom_point(data=df_hubs, mapping=aes(x="lon", y="lat"), size=6, color="#306998", fill="#306998")
    # Scales
    + scale_size(range=[1, 6], name="Trade Volume")
    + scale_color_gradient(low="#FFD43B", high="#306998", name="Trade Volume")
    # Labels
    + labs(title="flowmap-origin-destination · letsplot · pyplots.ai")
    # Theme
    + theme_void()
    + theme(
        plot_title=element_text(size=24, hjust=0.5),
        legend_title=element_text(size=18),
        legend_text=element_text(size=14),
        legend_position="right",
        plot_background=element_blank(),
    )
    # Size and limits
    + ggsize(1600, 900)
    + xlim(-180, 180)
    + ylim(-60, 85)
)

# Save outputs
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
