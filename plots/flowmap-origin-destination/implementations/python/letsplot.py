"""anyplot.ai
flowmap-origin-destination: Origin-Destination Flow Map
Library: letsplot | Python 3.13
Quality: 91/100 | Updated: 2026-05-20
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_rect,
    element_text,
    geom_curve,
    geom_point,
    geom_polygon,
    geom_text,
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

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
CONTINENT_FILL = "#E0DDD6" if THEME == "light" else "#2E2E2B"
CONTINENT_BORDER = "#C8C5BE" if THEME == "light" else "#4A4A47"
HUB_COLOR = "#306998"

# Data
np.random.seed(42)

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

label_offsets = {
    "Los Angeles": (-5, 4),
    "New York": (4, 2),
    "London": (-14, 2),
    "Rotterdam": (4, 2),
    "Dubai": (4, 2),
    "Singapore": (4, -5),
    "Shanghai": (4, 2),
    "Tokyo": (4, 2),
    "Sydney": (4, -5),
    "Sao Paulo": (-14, -5),
}

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

hub_data = []
for name, (lon, lat) in hubs.items():
    lx, ly = label_offsets.get(name, (4, 2))
    hub_data.append({"name": name, "lon": lon, "lat": lat, "label_lon": lon + lx, "label_lat": lat + ly})
df_hubs = pd.DataFrame(hub_data)

# Simplified world polygons
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

world_data = []
for i, poly in enumerate(polygons):
    for lon, lat in poly:
        world_data.append({"x": lon, "y": lat, "group": i})
df_world = pd.DataFrame(world_data)

# Plot
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    plot_title=element_text(size=16, hjust=0.5, color=INK),
    legend_title=element_text(size=12, color=INK),
    legend_text=element_text(size=10, color=INK_SOFT),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_position="right",
)

plot = (
    ggplot()
    + geom_polygon(
        data=df_world, mapping=aes(x="x", y="y", group="group"), fill=CONTINENT_FILL, color=CONTINENT_BORDER, size=0.3
    )
    + geom_curve(
        data=df_flows,
        mapping=aes(x="origin_lon", y="origin_lat", xend="dest_lon", yend="dest_lat", size="flow", color="flow"),
        curvature=-0.3,
        alpha=0.6,
    )
    + geom_point(data=df_hubs, mapping=aes(x="lon", y="lat"), size=7, color=HUB_COLOR, fill=HUB_COLOR)
    + geom_text(data=df_hubs, mapping=aes(x="label_lon", y="label_lat", label="name"), size=8, color=INK_SOFT)
    + scale_size(range=[1, 6], name="Trade Volume")
    + scale_color_gradient(low="#FFD43B", high="#306998", name="Trade Volume")
    + labs(title="flowmap-origin-destination · python · letsplot · anyplot.ai")
    + theme_void()
    + anyplot_theme
    + ggsize(800, 450)
    + xlim(-180, 180)
    + ylim(-60, 85)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
