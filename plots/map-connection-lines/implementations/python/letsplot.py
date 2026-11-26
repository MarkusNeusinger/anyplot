"""anyplot.ai
map-connection-lines: Connection Lines Map (Origin-Destination)
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-26
"""

import math
import os
from itertools import pairwise

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_polygon,
    geom_text,
    geom_text_repel,
    ggplot,
    ggsave,
    ggsize,
    guide_legend,
    labs,
    scale_color_gradientn,
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
LAND_FILL = "#E8E4DF" if THEME == "light" else "#2D2D29"
LAND_BORDER = "#C5C0BA" if THEME == "light" else "#404040"

# Imprint sequential ramp for marks (lines on the page), as (position, hex) stops
SEQ_MARKS = (
    [(0.0, "#009E73"), (0.338, "#4467A3"), (1.0, "#002850")]
    if THEME == "light"
    else [(0.0, "#007755"), (0.32, "#009E73"), (1.0, "#CDD9FF")]
)


def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    if not math.isfinite(t):
        return "none"
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


# Data: Major flight routes between world cities
np.random.seed(42)

airports = {
    "JFK": (-73.78, 40.64, "New York"),
    "LAX": (-118.41, 33.94, "Los Angeles"),
    "LHR": (-0.45, 51.47, "London"),
    "CDG": (2.55, 49.01, "Paris"),
    "DXB": (55.37, 25.25, "Dubai"),
    "HND": (139.78, 35.55, "Tokyo"),
    "SIN": (103.99, 1.36, "Singapore"),
    "SYD": (151.18, -33.94, "Sydney"),
    "GRU": (-46.47, -23.44, "São Paulo"),
    "JNB": (28.24, -26.14, "Johannesburg"),
}

routes = [
    ("JFK", "LHR", 4.2),
    ("JFK", "CDG", 2.8),
    ("JFK", "LAX", 3.5),
    ("LAX", "HND", 2.1),
    ("LAX", "SYD", 1.5),
    ("LHR", "DXB", 3.8),
    ("LHR", "SIN", 2.4),
    ("LHR", "JNB", 1.8),
    ("CDG", "DXB", 2.2),
    ("DXB", "SIN", 3.1),
    ("DXB", "HND", 1.9),
    ("SIN", "SYD", 2.6),
    ("SIN", "HND", 2.3),
    ("GRU", "LHR", 1.4),
    ("GRU", "JFK", 1.6),
    ("JNB", "DXB", 1.2),
]

route_data = []
for origin, dest, passengers in routes:
    o_lon, o_lat, _ = airports[origin]
    d_lon, d_lat, _ = airports[dest]
    route_data.append(
        {"origin_lon": o_lon, "origin_lat": o_lat, "dest_lon": d_lon, "dest_lat": d_lat, "passengers": passengers}
    )
df_routes = pd.DataFrame(route_data)

airport_data = [{"name": name, "lon": lon, "lat": lat} for _, (lon, lat, name) in airports.items()]
df_airports = pd.DataFrame(airport_data)

# Annotation: highlight busiest route JFK-LHR (4.2M passengers)
jfk_lon, jfk_lat, _ = airports["JFK"]
lhr_lon, lhr_lat, _ = airports["LHR"]
df_callout = pd.DataFrame(
    [{"x": (jfk_lon + lhr_lon) / 2, "y": (jfk_lat + lhr_lat) / 2 + 13, "label": "Busiest route\nJFK–LHR · 4.2M pax"}]
)

# Simplified world coastlines: one list of (lon, lat) vertices per landmass
LANDMASSES = [
    # North America
    [
        (-168, 66),
        (-162, 70),
        (-156, 71),
        (-141, 70),
        (-128, 70),
        (-115, 68),
        (-95, 69),
        (-85, 69),
        (-82, 66),
        (-88, 64),
        (-93, 60),
        (-94, 58),
        (-85, 55),
        (-82, 52),
        (-79, 52),
        (-78, 58),
        (-77, 62),
        (-72, 62),
        (-65, 60),
        (-62, 57),
        (-56, 52),
        (-60, 50),
        (-66, 50),
        (-64, 47),
        (-66, 45),
        (-70, 43),
        (-70, 41.5),
        (-74, 40.5),
        (-76, 37),
        (-76, 35),
        (-81, 31),
        (-80, 26),
        (-81, 25.5),
        (-83, 29),
        (-85, 30),
        (-89, 30),
        (-91, 29),
        (-94, 29.5),
        (-97, 27),
        (-97.5, 22),
        (-96, 19),
        (-94, 18),
        (-91, 19),
        (-90, 21),
        (-87, 21),
        (-88, 16),
        (-84, 15.5),
        (-83, 11),
        (-80, 9),
        (-77.5, 8.5),
        (-79, 8),
        (-82, 8),
        (-86, 11),
        (-88, 13),
        (-92, 14.5),
        (-96, 16),
        (-101, 17.5),
        (-105.5, 20.5),
        (-105.5, 23),
        (-109, 25.5),
        (-112.5, 29),
        (-114.7, 31.5),
        (-114, 29),
        (-112, 26),
        (-110, 23),
        (-112, 24.5),
        (-115, 28),
        (-117, 32.5),
        (-120, 34.5),
        (-122.5, 37.5),
        (-124, 40.5),
        (-124, 46),
        (-125, 49),
        (-130, 54),
        (-134, 58),
        (-140, 60),
        (-148, 60.5),
        (-152, 59),
        (-158, 57),
        (-164, 55),
        (-158, 58.5),
        (-162, 60),
        (-165, 62),
        (-161, 64.5),
        (-168, 65.5),
    ],
    # Greenland (cut at 76 N)
    [(-68, 76), (-45, 76), (-20, 76), (-20, 70), (-30, 68), (-43, 60), (-50, 64), (-55, 70), (-68, 76)],
    # South America
    [
        (-77, 8),
        (-72, 12),
        (-65, 10.5),
        (-60, 8.5),
        (-52, 5),
        (-50, 0),
        (-44, -2.5),
        (-35, -5),
        (-37, -12),
        (-39, -17),
        (-41, -22),
        (-45, -23.5),
        (-48.5, -26),
        (-49, -29),
        (-53, -34),
        (-58, -34.5),
        (-57, -38),
        (-62, -39),
        (-65, -41),
        (-64, -45),
        (-67, -47),
        (-66, -51),
        (-69, -52.5),
        (-68.5, -55),
        (-72, -54),
        (-75, -50),
        (-74, -44),
        (-73, -37),
        (-71.5, -30),
        (-70, -18),
        (-76, -14),
        (-81, -5),
        (-80, -1),
        (-78, 2),
        (-77.5, 6),
    ],
    # Africa
    [
        (-17, 21),
        (-13, 27.5),
        (-9.5, 30),
        (-6, 35.8),
        (0, 35.5),
        (10, 37),
        (11, 33),
        (15, 32),
        (20, 31),
        (25, 32),
        (32, 31.2),
        (32.5, 30),
        (35, 24),
        (37.5, 18),
        (39, 15.5),
        (43.5, 11.5),
        (51.2, 11.8),
        (48, 5),
        (41, -1.5),
        (39, -5),
        (40.5, -11),
        (40.5, -15),
        (35, -20),
        (35.5, -24),
        (32.5, -26),
        (32.5, -28.5),
        (28, -33),
        (20, -34.8),
        (18.4, -34),
        (17, -29),
        (14.5, -22.5),
        (12, -17),
        (13.5, -11),
        (12, -5),
        (9, -1),
        (9.5, 3.5),
        (6, 4.3),
        (3, 6.3),
        (-2, 5),
        (-8, 4.5),
        (-13, 8),
        (-16, 12),
        (-17.5, 14.7),
        (-16.5, 19),
    ],
    # Eurasia
    [
        (-9, 43),
        (-9, 37),
        (-5.5, 36),
        (-2, 36.8),
        (0, 38.5),
        (3, 42),
        (6, 43),
        (8.5, 44.3),
        (12.5, 41.5),
        (15.8, 38),
        (17, 40),
        (18.5, 40.3),
        (16, 41.8),
        (12.3, 44.5),
        (13.7, 45.6),
        (19, 42),
        (19.5, 40),
        (23, 36.5),
        (24, 38),
        (23, 40),
        (26, 40.8),
        (29, 41),
        (28, 43),
        (29.5, 45),
        (33.5, 44.5),
        (35, 45),
        (38, 47),
        (36, 45),
        (39, 43.5),
        (41.5, 41.5),
        (36, 41.5),
        (31, 41),
        (27, 41),
        (26.5, 39),
        (27, 37),
        (30, 36.3),
        (36, 36.6),
        (35.8, 34),
        (34.6, 31),
        (34.3, 29.5),
        (35, 28),
        (39, 22),
        (42, 16),
        (43.3, 12.7),
        (45, 12.8),
        (52, 16),
        (55, 17.5),
        (58.5, 20.5),
        (59.8, 22.5),
        (56.4, 26.2),
        (55, 25.5),
        (51.5, 24.2),
        (51.3, 26),
        (50, 26.5),
        (50, 29),
        (48, 30),
        (50.5, 30),
        (52, 27.5),
        (55, 26.8),
        (57, 25.8),
        (61.5, 25.2),
        (66.5, 25.4),
        (68, 23.5),
        (70, 21),
        (72.8, 19),
        (73.5, 16),
        (75, 12),
        (77, 8),
        (78, 8.8),
        (80, 12.5),
        (80.3, 15.5),
        (82, 17),
        (85, 19.5),
        (87, 21.5),
        (89, 22),
        (91, 22.5),
        (92.5, 20),
        (94, 17),
        (94.5, 16),
        (97.5, 16.5),
        (98.5, 13),
        (98.5, 10),
        (99.5, 7),
        (101, 3),
        (103.5, 1.4),
        (104, 3),
        (103, 6),
        (100.5, 13.5),
        (103, 10.5),
        (105, 8.7),
        (106.5, 10.5),
        (109, 12),
        (109.3, 15),
        (106, 19),
        (108, 21.5),
        (110.5, 20.3),
        (113, 22),
        (117, 23.5),
        (120, 26),
        (121.5, 29),
        (122, 31),
        (120.5, 34),
        (119, 37),
        (122, 37),
        (121, 39),
        (122, 40.5),
        (124.5, 40),
        (126, 37.5),
        (126.5, 34.5),
        (129, 35.2),
        (129.5, 37),
        (128, 39),
        (131, 42.5),
        (135, 44),
        (140, 48),
        (141, 52),
        (137, 54),
        (141, 53),
        (143, 59),
        (150, 59.5),
        (155, 59),
        (156.5, 57),
        (156, 51),
        (158, 53),
        (162, 56),
        (163, 59.5),
        (170, 60),
        (179, 62.5),
        (180, 65),
        (180, 69),
        (170, 70),
        (160, 69.5),
        (150, 71),
        (140, 72.5),
        (131, 71),
        (128, 72),
        (113, 74),
        (106, 77),
        (100, 76),
        (95, 76),
        (87, 75),
        (80, 73),
        (70, 73),
        (68, 70),
        (60, 69.5),
        (44, 68.5),
        (40, 66),
        (34, 66.5),
        (30, 70),
        (25, 71),
        (18, 69.5),
        (14, 67),
        (10.5, 64),
        (5, 62),
        (5, 59),
        (8, 58),
        (11, 59),
        (11.5, 58),
        (13, 55.5),
        (16, 56),
        (17, 58.5),
        (17.5, 61),
        (21, 64.5),
        (25, 65.5),
        (22, 60.5),
        (25, 60),
        (29.5, 60.5),
        (23, 59.2),
        (21, 57),
        (21, 55),
        (18, 54.8),
        (14, 54),
        (10.5, 54.3),
        (10, 57.5),
        (8.2, 56),
        (8.5, 54),
        (5, 53),
        (4, 51.5),
        (2, 51),
        (1.5, 50.3),
        (-1.5, 49.7),
        (-4.5, 48.5),
        (-1.5, 46),
        (-1.5, 43.5),
    ],
    # Great Britain, Ireland, Iceland
    [
        (-5.5, 50),
        (1.5, 51),
        (1.7, 52.8),
        (0, 53.5),
        (-2, 55.8),
        (-2, 57.5),
        (-4, 57.8),
        (-3, 58.6),
        (-5, 58.5),
        (-6, 56.5),
        (-5, 55),
        (-3, 54.8),
        (-3, 53.3),
        (-4.5, 53),
        (-5, 51.8),
        (-3, 51.4),
    ],
    [(-10, 52), (-6, 52.2), (-6, 54.5), (-8, 55.2), (-10, 54)],
    [(-24, 65.5), (-22, 66.4), (-14.5, 66.3), (-13.6, 65), (-18, 63.4), (-22.5, 63.8)],
    # Japan, Taiwan, Philippines, Sri Lanka
    [
        (130, 33),
        (131, 34.5),
        (133, 35.5),
        (136, 36.5),
        (137, 37.3),
        (139, 38),
        (140, 40),
        (141.5, 41.5),
        (142, 40),
        (141, 38),
        (140.8, 35.7),
        (138.5, 35),
        (136.5, 34.3),
        (135, 33.5),
        (132.5, 33.2),
        (131, 31.2),
    ],
    [(140, 42), (141.5, 45.3), (145.5, 43.3), (143, 42)],
    [(121, 25), (122, 24.5), (120.8, 22), (120, 23.3)],
    [(120.5, 18.5), (122.2, 18.4), (121.5, 14), (124, 12.7), (123, 13.8), (120.6, 14.5), (120, 16)],
    [(122, 7), (125.5, 9.5), (126.5, 7), (125.5, 5.8)],
    [(80, 9.8), (81.8, 7.5), (81, 6), (80, 6.2), (79.8, 8)],
    # Indonesia and New Guinea
    [(95.3, 5.6), (98.7, 3.5), (103.5, -1), (106, -3), (105.8, -5.8), (102, -4), (98.5, 0.5)],
    [(109, 1), (111, 1.5), (114, 4.5), (117.5, 7), (119, 5), (118, 1), (116.5, -3), (114, -4), (110.5, -3), (109, -1)],
    [(105.5, -6.5), (108, -6.5), (114.5, -7.8), (114, -8.7), (106, -7.5)],
    [
        (131, -1),
        (134.5, -3.5),
        (138, -1.7),
        (144, -3.8),
        (147, -6),
        (150, -10.5),
        (146, -8.5),
        (143, -9),
        (141, -9.2),
        (138, -8.2),
        (138, -5),
        (133.5, -4),
    ],
    # Australia, Tasmania, New Zealand, Madagascar, Cuba, Hispaniola
    [
        (113.5, -22),
        (114.5, -26),
        (115, -34),
        (118, -35),
        (123, -34),
        (129, -31.5),
        (134, -32.8),
        (138, -35),
        (140, -38),
        (144, -38.5),
        (147, -39),
        (150, -37.5),
        (153, -31),
        (153.5, -26),
        (151, -23),
        (146, -19),
        (145.5, -15),
        (143.5, -14),
        (142.5, -10.8),
        (141.5, -13),
        (141, -17),
        (139.5, -17.5),
        (136.5, -15),
        (135, -12),
        (132, -11.5),
        (130, -12.5),
        (129.5, -15),
        (125, -14.5),
        (122, -17.5),
        (119, -20),
        (116, -21),
    ],
    [(145, -41), (148.2, -41), (147.5, -43.5), (146, -43.5)],
    [(173, -35), (175, -37), (178, -37.7), (177, -39.5), (175, -41.5), (174.5, -39.5), (173.7, -35.5)],
    [(172.7, -40.5), (174, -41.5), (171, -44.5), (169, -46.5), (166.5, -46), (168, -44)],
    [(49.3, -12), (50.5, -15.5), (47.5, -25), (45, -25.5), (43.5, -22), (44.5, -16)],
    [(-84.9, 21.9), (-82, 23.1), (-77.5, 21.8), (-74.2, 20.2), (-77.5, 19.9), (-80, 21.8)],
    [(-74.4, 18.4), (-72, 19.9), (-68.4, 18.6), (-71, 17.8)],
]

df_world = pd.DataFrame([{"x": lon, "y": lat, "group": i} for i, poly in enumerate(LANDMASSES) for lon, lat in poly])

# Great-circle arcs: spherical interpolation per route, split where a path crosses the antimeridian
ARC_POINTS = 80


def great_circle(lon1, lat1, lon2, lat2, n=ARC_POINTS):
    """(lon, lat) points of the shortest path on the sphere, lon unwrapped to a continuous run."""
    p1 = np.array(
        [
            np.cos(np.radians(lat1)) * np.cos(np.radians(lon1)),
            np.cos(np.radians(lat1)) * np.sin(np.radians(lon1)),
            np.sin(np.radians(lat1)),
        ]
    )
    p2 = np.array(
        [
            np.cos(np.radians(lat2)) * np.cos(np.radians(lon2)),
            np.cos(np.radians(lat2)) * np.sin(np.radians(lon2)),
            np.sin(np.radians(lat2)),
        ]
    )
    omega = np.arccos(np.clip(p1 @ p2, -1, 1))
    t = np.linspace(0, 1, n)[:, None]
    pts = (np.sin((1 - t) * omega) * p1 + np.sin(t * omega) * p2) / np.sin(omega)
    lons = np.degrees(np.unwrap(np.arctan2(pts[:, 1], pts[:, 0])))
    lats = np.degrees(np.arcsin(pts[:, 2]))
    return lons, lats


arc_rows = []
for i, r in df_routes.iterrows():
    lons, lats = great_circle(r["origin_lon"], r["origin_lat"], r["dest_lon"], r["dest_lat"])
    seg = 0
    for k in range(len(lons)):
        if k:
            # leaving the [-180, 180] frame: close this piece at the edge, restart on the other side
            for edge in (-180, 180):
                if (lons[k - 1] - edge) * (lons[k] - edge) < 0:
                    frac = (edge - lons[k - 1]) / (lons[k] - lons[k - 1])
                    lat_edge = lats[k - 1] + frac * (lats[k] - lats[k - 1])
                    arc_rows.append(
                        {"lon": edge, "lat": lat_edge, "group": f"{i}-{seg}", "passengers": r["passengers"]}
                    )
                    seg += 1
                    arc_rows.append(
                        {"lon": -edge, "lat": lat_edge, "group": f"{i}-{seg}", "passengers": r["passengers"]}
                    )
        lon = (lons[k] + 180) % 360 - 180
        arc_rows.append({"lon": lon, "lat": lats[k], "group": f"{i}-{seg}", "passengers": r["passengers"]})
df_arcs = pd.DataFrame(arc_rows)

# View limits from the base map, with a small margin
x_min, x_max = df_world["x"].min(), df_world["x"].max()
y_min, y_max = df_world["y"].min() - 3, df_world["y"].max() + 3

# Title font size scaled to length
title = "Global Flight Routes · map-connection-lines · python · letsplot · anyplot.ai"
n = len(title)
ratio = 67 / n if n > 67 else 1.0
title_fontsize = max(11, round(16 * ratio))

# Plot
plot = (
    ggplot()
    + geom_polygon(data=df_world, mapping=aes(x="x", y="y", group="group"), fill=LAND_FILL, color=LAND_BORDER, size=0.3)
    + geom_path(
        data=df_arcs, mapping=aes(x="lon", y="lat", group="group", size="passengers", color="passengers"), alpha=0.6
    )
    + geom_point(
        data=df_airports, mapping=aes(x="lon", y="lat"), size=6, color=PAGE_BG, fill="#009E73", shape=21, stroke=2
    )
    + geom_text_repel(
        data=df_airports,
        mapping=aes(x="lon", y="lat", label="name"),
        size=3.5,
        color=INK,
        seed=42,
        point_padding=5,
        box_padding=3,
        max_overlaps=20,
    )
    + geom_text(
        data=df_callout, mapping=aes(x="x", y="y", label="label"), size=3.5, color=INK, hjust=0.5, fontface="bold"
    )
    + scale_size(range=[0.5, 6], name="Passengers (millions)", guide=guide_legend())
    + scale_color_gradientn(
        colors=[ramp_color(SEQ_MARKS, k / 255) for k in range(256)], name="Passengers (millions)", guide=guide_legend()
    )
    + labs(title=title)
    + theme_void()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=title_fontsize, hjust=0.5, color=INK),
        legend_title=element_text(size=12, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_position="right",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    )
    + ggsize(800, 450)
    + xlim(x_min, x_max)
    + ylim(y_min, y_max)
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
