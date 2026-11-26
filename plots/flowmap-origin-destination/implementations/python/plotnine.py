"""anyplot.ai
flowmap-origin-destination: Origin-Destination Flow Map
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-20
"""

import os

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
    geom_text,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_color_manual,
    scale_size_identity,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
OCEAN_BG = "#DDE9F2" if THEME == "light" else "#111A22"
LAND_FILL = "#D0CCC4" if THEME == "light" else "#363632"
LAND_COLOR = "#AEA9A1" if THEME == "light" else "#525248"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants: simplified continent outlines (lon, lat) for the basemap, true for any flow data
CONTINENTS = {
    "N. America": (
        [
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
        ],
        [60, 65, 70, 55, 48, 33, 25, 26, 25, 35, 45, 48, 45, 27, 30, 20, 22, 50, 60, 55, 60],
    ),
    "S. America": (
        [-80, -68, -60, -50, -35, -40, -50, -55, -68, -72, -75, -80, -82, -80],
        [10, 12, 5, 0, -5, -22, -35, -52, -55, -18, -5, 0, 8, 10],
    ),
    "Europe": (
        [-10, 0, 10, 20, 30, 40, 50, 60, 50, 35, 25, 20, 10, 0, -10, -10],
        [35, 37, 36, 35, 35, 40, 45, 55, 70, 70, 70, 65, 60, 50, 40, 35],
    ),
    "Africa": (
        [-17, -5, 10, 35, 50, 52, 43, 35, 30, 15, 0, -17, -17],
        [15, 37, 37, 32, 12, 0, -25, -35, -35, -25, 5, 20, 15],
    ),
    "Asia": (
        [60, 80, 100, 120, 140, 145, 140, 130, 105, 100, 80, 60, 45, 30, 25, 30, 35, 50, 60],
        [55, 70, 75, 70, 55, 45, 35, 30, 0, 5, 10, 25, 30, 35, 42, 55, 70, 70, 55],
    ),
    "Australia": (
        [113, 125, 135, 145, 152, 150, 140, 130, 115, 113],
        [-22, -15, -12, -15, -25, -38, -38, -33, -35, -22],
    ),
}
WIDTH_MIN, WIDTH_MAX = 0.3, 2.5  # arc line width range, proportional to flow
CURVE_BEND = 0.25  # Bezier control-point offset as a share of the arc length
LABEL_GAP = 4.5  # minimum vertical spacing (degrees) between labels that sit close together
LABEL_NEAR_LON = 18  # labels closer than this in longitude are stacked

# Columns: set these to your table's column names
ORIGIN = "Origin"  # role: origin_name
DEST = "Destination"  # role: dest_name
ORIGIN_LAT = "Origin latitude"  # role: origin_lat
ORIGIN_LON = "Origin longitude"  # role: origin_lon
DEST_LAT = "Destination latitude"  # role: dest_lat
DEST_LON = "Destination longitude"  # role: dest_lon
FLOW = "Annual migrants (k)"  # role: flow
REGION = "Origin region"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("flows.csv")
# International migration flows (thousands of people per year) between world cities
cities = {
    "New York": (40.71, -74.01),
    "London": (51.51, -0.13),
    "Paris": (48.85, 2.35),
    "Dubai": (25.20, 55.27),
    "Sydney": (-33.87, 151.21),
    "Toronto": (43.65, -79.38),
    "Singapore": (1.35, 103.82),
    "Tokyo": (35.68, 139.69),
    "São Paulo": (-23.55, -46.63),
    "Mumbai": (19.08, 72.88),
    "Lagos": (6.45, 3.40),
    "Cairo": (30.04, 31.24),
    "Berlin": (52.52, 13.40),
    "Los Angeles": (34.05, -118.24),
}
regions = {
    "Mumbai": "Asia",
    "Tokyo": "Asia",
    "Singapore": "Asia",
    "Lagos": "Africa",
    "Cairo": "Africa",
    "São Paulo": "Americas",
    "New York": "Americas",
    "Toronto": "Americas",
    "London": "Europe",
    "Paris": "Europe",
    "Berlin": "Europe",
}
flows = [
    ("Mumbai", "Dubai", 142),
    ("Lagos", "London", 98),
    ("São Paulo", "New York", 85),
    ("Cairo", "Dubai", 78),
    ("Tokyo", "Los Angeles", 72),
    ("London", "Sydney", 68),
    ("Mumbai", "London", 65),
    ("New York", "Toronto", 60),
    ("Paris", "London", 55),
    ("Singapore", "Sydney", 48),
    ("Lagos", "Paris", 44),
    ("Berlin", "London", 40),
    ("Cairo", "London", 38),
    ("Tokyo", "Sydney", 35),
    ("Mumbai", "Singapore", 32),
    ("São Paulo", "London", 30),
    ("Lagos", "Dubai", 27),
    ("Toronto", "London", 24),
]
df = pd.DataFrame(
    {
        ORIGIN: [o for o, _, _ in flows],
        DEST: [d for _, d, _ in flows],
        ORIGIN_LAT: [cities[o][0] for o, _, _ in flows],
        ORIGIN_LON: [cities[o][1] for o, _, _ in flows],
        DEST_LAT: [cities[d][0] for _, d, _ in flows],
        DEST_LON: [cities[d][1] for _, d, _ in flows],
        FLOW: [f for _, _, f in flows],
        REGION: [regions[o] for o, _, _ in flows],
    }
)

# Plot: reads only df and the constants above
# Quadratic Bezier arc per flow, bent sideways by CURVE_BEND of its length
flow_min, flow_max = df[FLOW].min(), df[FLOW].max()
t = np.linspace(0, 1, 40)
paths = []
for i, row in df.iterrows():
    x0, y0, x1, y1 = row[ORIGIN_LON], row[ORIGIN_LAT], row[DEST_LON], row[DEST_LAT]
    dx, dy = x1 - x0, y1 - y0
    seg_len = np.hypot(dx, dy)
    ctrl_x = (x0 + x1) / 2 - dy / seg_len * seg_len * CURVE_BEND
    ctrl_y = (y0 + y1) / 2 + dx / seg_len * seg_len * CURVE_BEND
    share = (row[FLOW] - flow_min) / (flow_max - flow_min) if flow_max > flow_min else 0.5
    paths.append(
        pd.DataFrame(
            {
                "flow_id": i,
                "x": (1 - t) ** 2 * x0 + 2 * (1 - t) * t * ctrl_x + t**2 * x1,
                "y": (1 - t) ** 2 * y0 + 2 * (1 - t) * t * ctrl_y + t**2 * y1,
                REGION: row[REGION],
                "width": WIDTH_MIN + share * (WIDTH_MAX - WIDTH_MIN),
            }
        )
    )
df_arcs = pd.concat(paths, ignore_index=True)

# Endpoints: every city that appears as an origin or a destination
points = pd.concat(
    [
        df[[ORIGIN, ORIGIN_LON, ORIGIN_LAT]].set_axis(["name", "lon", "lat"], axis=1),
        df[[DEST, DEST_LON, DEST_LAT]].set_axis(["name", "lon", "lat"], axis=1),
    ]
).drop_duplicates("name")

# Labels sit right of the dot; a label close to a higher one steps down until it is clear
placed = []
label_y = {}
for _, city in points.sort_values("lat", ascending=False).iterrows():
    y = city["lat"]
    while any(abs(city["lon"] - px) < LABEL_NEAR_LON and abs(y - py) < LABEL_GAP for px, py in placed):
        y -= LABEL_GAP
    placed.append((city["lon"], y))
    label_y[city["name"]] = y
points = points.assign(label_x=points["lon"] + 3.5, label_y=points["name"].map(label_y))

df_land = pd.concat(
    [pd.DataFrame({"continent": name, "lon": lon, "lat": lat}) for name, (lon, lat) in CONTINENTS.items()]
)

region_order = df[REGION].unique().tolist()

plot = (
    ggplot()
    + geom_polygon(
        aes(x="lon", y="lat", group="continent"), data=df_land, fill=LAND_FILL, color=LAND_COLOR, size=0.3, alpha=0.7
    )
    + geom_path(
        aes(x="x", y="y", group="flow_id", color=REGION, size="width"), data=df_arcs, alpha=0.6, lineend="round"
    )
    + geom_point(aes(x="lon", y="lat"), data=points, color=INK, fill=PAGE_BG, shape="o", size=2.2, stroke=0.9)
    + geom_text(aes(x="label_x", y="label_y", label="name"), data=points, color=INK, size=8, ha="left")
    + scale_size_identity()
    + scale_color_manual(values=IMPRINT_PALETTE, limits=region_order, name="Origin region\n(width = migrants)")
    + guides(color=guide_legend(override_aes={"size": 2.0, "alpha": 1.0}))
    + coord_fixed(ratio=1.3, xlim=(-180, 180), ylim=(-60, 80))
    + labs(title="flowmap-origin-destination · python · plotnine · anyplot.ai", x="Longitude (°)", y="Latitude (°)")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=OCEAN_BG),
        panel_grid_major=element_line(color=INK, size=0.2, alpha=0.08),
        panel_grid_minor=element_blank(),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=12, color=INK, weight="bold"),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=8, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color="none"),
        legend_key=element_rect(fill=ELEVATED_BG, color="none"),
        legend_position="right",
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
