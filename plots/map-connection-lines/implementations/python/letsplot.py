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
    coord_fixed,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_polygon,
    geom_text,
    geom_text_repel,
    gggrid,
    ggplot,
    ggsave,
    ggsize,
    guide_legend,
    labs,
    scale_color_gradientn,
    scale_size,
    theme,
    theme_void,
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
    [(0.0, "#009E73"), (0.687, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#6F7E20"), (0.21, "#009E73"), (1.0, "#CDD9FF")]
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


# Column constants
ORIGIN = "origin"  # role: route start (airport code)
DEST = "dest"  # role: route end (airport code)
PASSENGERS = "passengers"  # role: annual passengers in millions, drives line width and color
LEGEND_TITLE = "Passengers (millions)"

# Data: major flight routes between world cities, longitude / latitude in degrees
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
df = pd.DataFrame(
    [
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
    ],
    columns=[ORIGIN, DEST, PASSENGERS],
)

# Coastline outlines (lon, lat) of the landmasses, simplified; lakes are drawn in the page color
landmasses = {
    "north_america": [
        (-168, 66),
        (-162, 70),
        (-156, 71.3),
        (-141, 69.6),
        (-128, 70),
        (-115, 68),
        (-95, 68),
        (-82, 68),
        (-88, 64),
        (-94, 59),
        (-92, 57),
        (-85, 55),
        (-82, 52),
        (-79, 52),
        (-78, 58),
        (-77, 62),
        (-70, 61),
        (-65, 60),
        (-62, 57),
        (-56, 52),
        (-60, 50),
        (-66, 50),
        (-60, 47),
        (-66, 44),
        (-70, 43),
        (-70, 41.5),
        (-74, 40.5),
        (-76, 37),
        (-76, 35),
        (-81, 31),
        (-80, 27),
        (-80, 25.2),
        (-82, 26),
        (-83, 29),
        (-85, 30),
        (-89, 30),
        (-90, 29),
        (-94, 29.5),
        (-97, 27),
        (-97.5, 22),
        (-95, 18.5),
        (-91, 18.7),
        (-90.5, 21),
        (-87, 21.5),
        (-88, 16),
        (-84, 15.8),
        (-83.5, 11),
        (-81.5, 9),
        (-79, 9.5),
        (-77.5, 8.5),
        (-80, 7.5),
        (-83, 8.2),
        (-85.7, 10),
        (-87.5, 13),
        (-92, 14.5),
        (-96, 15.7),
        (-105, 19.5),
        (-105.5, 22.5),
        (-109, 26),
        (-112.5, 31),
        (-114.8, 31.8),
        (-112, 27),
        (-110, 23.5),
        (-112, 24.8),
        (-114.5, 28),
        (-117, 32.5),
        (-120.5, 34.5),
        (-122.5, 37.5),
        (-124.2, 40.5),
        (-124, 46),
        (-124.8, 48.4),
        (-128, 51),
        (-133, 55),
        (-138, 59),
        (-146, 61),
        (-152, 59),
        (-158, 56.5),
        (-164, 54.7),
        (-158, 58.5),
        (-162, 60),
        (-166, 62),
        (-161, 64.5),
        (-168, 65.7),
    ],
    "greenland": [
        (-73, 78),
        (-60, 82),
        (-30, 83.5),
        (-20, 80),
        (-18, 75),
        (-22, 70),
        (-32, 68),
        (-42, 60),
        (-48, 61),
        (-52, 65),
        (-54, 70),
        (-58, 75),
        (-68, 76.5),
    ],
    "baffin": [(-80, 73), (-68, 70), (-62, 66), (-65, 63), (-72, 64), (-78, 65), (-88, 70)],
    "cuba": [(-85, 22), (-82, 23.1), (-77, 21.3), (-74.2, 20.2), (-77.7, 19.9), (-80, 21.8)],
    "hispaniola": [(-74.4, 18.4), (-72.5, 19.9), (-69.5, 19.2), (-68.4, 18.5), (-71, 17.7)],
    "south_america": [
        (-77.5, 8),
        (-72, 12),
        (-67, 10.7),
        (-62, 10.5),
        (-60, 8.5),
        (-52, 5),
        (-50, 0),
        (-44, -2.5),
        (-35, -5.5),
        (-35, -9),
        (-39, -14),
        (-39, -18),
        (-41, -22),
        (-45, -23.5),
        (-48, -26),
        (-48.5, -28.5),
        (-53, -34),
        (-57, -35),
        (-57, -38),
        (-62, -39),
        (-65, -41),
        (-64, -43),
        (-67, -46),
        (-66, -48),
        (-69, -51),
        (-68.5, -53),
        (-71, -54),
        (-74, -52),
        (-75, -47),
        (-73.5, -42),
        (-73.7, -37),
        (-71.5, -30),
        (-70.5, -18),
        (-76, -14),
        (-79, -8),
        (-81, -5),
        (-80, -2),
        (-80, 1),
        (-78, 2.5),
        (-77, 7),
    ],
    "eurasia": [
        (-9, 37),
        (-9, 43),
        (-2, 43.5),
        (-1.5, 46),
        (-4.5, 48.5),
        (-1.5, 49.5),
        (2, 51),
        (4, 52),
        (8, 54),
        (8.5, 57),
        (10.5, 57.5),
        (10.5, 54.8),
        (14, 54),
        (19, 54.5),
        (21, 57),
        (24, 57.5),
        (24, 59.5),
        (30, 60),
        (23, 60),
        (21.5, 61),
        (21.5, 64),
        (25, 65.5),
        (22, 65.8),
        (17.5, 62.5),
        (18.5, 60),
        (16, 56.5),
        (13, 55.5),
        (12, 58),
        (11, 59),
        (8, 58),
        (5, 59),
        (5, 62),
        (10, 64),
        (14, 67.5),
        (19, 70),
        (26, 71),
        (31, 70),
        (41, 67),
        (33, 66.5),
        (40, 65),
        (44, 66),
        (43, 68),
        (54, 68.5),
        (60, 69),
        (68, 69),
        (73, 68),
        (69, 73),
        (80, 73),
        (88, 75.5),
        (100, 77),
        (113, 74),
        (129, 72),
        (140, 72.5),
        (160, 70),
        (170, 70),
        (180, 69),
        (180, 65),
        (177, 63),
        (170, 60),
        (163, 59.5),
        (163, 56),
        (156, 51),
        (156, 57),
        (160, 61),
        (155, 59.5),
        (143, 59),
        (137, 54),
        (141, 53),
        (140, 48),
        (135, 43),
        (130, 42.5),
        (129, 40),
        (127, 39.5),
        (129, 35.5),
        (126.5, 34.5),
        (126, 37.5),
        (125, 39.5),
        (121.5, 39),
        (122, 40.5),
        (118, 39),
        (119, 37),
        (122.5, 37),
        (120, 35),
        (121.8, 31.5),
        (122, 29.5),
        (120, 26),
        (117, 23.3),
        (113, 22),
        (110.5, 21),
        (108, 21.5),
        (106, 19),
        (109, 15),
        (109, 12),
        (106, 9),
        (105, 8.7),
        (105, 10.5),
        (100.5, 13.5),
        (99.5, 10),
        (101, 6.5),
        (103.5, 4),
        (104, 1.4),
        (101, 2.8),
        (98.5, 8),
        (98.3, 13),
        (97.5, 16.5),
        (94.5, 16),
        (94, 19),
        (92, 21),
        (90, 22),
        (87, 21.5),
        (85, 19.5),
        (81.5, 16.5),
        (80.2, 13),
        (79.8, 10),
        (78, 8.3),
        (76.5, 9),
        (75, 12.5),
        (73.5, 16.5),
        (72.8, 20.5),
        (70.5, 21),
        (69, 22.5),
        (67, 24.5),
        (62, 25),
        (57, 25.8),
        (56.5, 27),
        (52, 27.5),
        (50, 30),
        (48.5, 29.8),
        (50, 26.5),
        (51.5, 24.5),
        (54, 24.2),
        (56, 26),
        (56.5, 24.5),
        (58.5, 23.5),
        (59.8, 22.5),
        (57.5, 19),
        (55, 17),
        (52, 16),
        (48, 14),
        (45, 12.8),
        (43.3, 12.7),
        (42.8, 15),
        (41, 19),
        (39, 22),
        (37, 26),
        (35, 28),
        (34.8, 29.5),
        (34.2, 31.3),
        (35, 33.5),
        (36, 36),
        (32, 36.2),
        (30, 36.4),
        (27.5, 36.8),
        (27, 38.5),
        (26.3, 40),
        (26, 40.7),
        (24, 40.3),
        (23.5, 38),
        (22, 36.8),
        (21.2, 38.5),
        (19.5, 41),
        (19.3, 42),
        (16, 43.5),
        (13.5, 45.3),
        (12.3, 45.3),
        (12.5, 44),
        (16, 41.8),
        (18.5, 40.2),
        (16, 38),
        (15.7, 40),
        (12, 42),
        (10, 44),
        (8.5, 44.3),
        (6, 43),
        (3, 43.3),
        (3, 42),
        (0, 39.5),
        (-0.5, 38),
        (-2, 36.8),
        (-5.3, 36),
        (-6.5, 37),
    ],
    "africa": [
        (-5.9, 35.8),
        (-2, 35.2),
        (3, 36.8),
        (10, 37.2),
        (11, 35),
        (10, 33.5),
        (15, 32.3),
        (20, 32),
        (20, 30.8),
        (25, 31.7),
        (32, 31.2),
        (32.5, 29.9),
        (33.5, 27.5),
        (35.5, 24),
        (37.3, 19),
        (38.5, 16),
        (41, 14.5),
        (43, 12.5),
        (44, 10.5),
        (51, 12),
        (51, 10.5),
        (48, 5),
        (44, 1.5),
        (41.5, -2),
        (39.2, -5),
        (39, -8),
        (40.5, -11),
        (40.5, -15),
        (36, -18.5),
        (35, -21),
        (35.5, -24),
        (32.8, -26),
        (32.8, -28.5),
        (30, -31),
        (27.5, -33.3),
        (25.5, -34),
        (22, -34),
        (19, -34.5),
        (18.3, -32),
        (15.5, -27.5),
        (14.5, -22.5),
        (11.8, -17),
        (13.5, -12),
        (12, -6),
        (9.5, -1),
        (9.5, 3.8),
        (8, 4.5),
        (6, 4.3),
        (4, 6.3),
        (1, 6),
        (-2, 4.8),
        (-4.5, 5.2),
        (-7.5, 4.4),
        (-11, 6.8),
        (-13.2, 8.5),
        (-15, 11),
        (-17.2, 14.7),
        (-16.5, 19.5),
        (-16, 22),
        (-13, 27.5),
        (-10, 29.5),
        (-9.5, 31),
        (-8.5, 33.2),
        (-6.8, 34),
    ],
    "madagascar": [(49.3, -12), (50.5, -15.5), (47.5, -24.5), (45, -25.5), (43.5, -22), (44.3, -16.5), (47, -15)],
    "great_britain": [
        (-5.5, 50),
        (1.5, 51),
        (1.7, 52.8),
        (-0.5, 54.5),
        (-2, 56),
        (-2, 57.6),
        (-3.5, 58.6),
        (-5, 58.5),
        (-6, 57),
        (-5.5, 55.5),
        (-3, 54.8),
        (-3, 53.4),
        (-4.5, 53),
        (-5, 51.8),
        (-3, 51.4),
    ],
    "ireland": [(-10, 51.8), (-6, 52), (-6, 54), (-5.7, 54.7), (-8, 55.2), (-10, 54), (-9.5, 52.5)],
    "iceland": [(-24, 65.5), (-22, 64), (-18, 63.4), (-14, 64.5), (-14.5, 65.8), (-18, 66.2), (-22, 66.4)],
    "honshu": [
        (135, 33.5),
        (137, 34.5),
        (139, 35),
        (140.8, 35.7),
        (141, 38.5),
        (141.5, 41.2),
        (140, 40.5),
        (139.8, 38.5),
        (137, 37),
        (136, 35.7),
        (133, 35.5),
        (131, 34.2),
        (132.5, 34),
        (135, 34.5),
    ],
    "kyushu": [(130, 33.5), (131.8, 33.3), (131, 31.2), (130.2, 31.3)],
    "hokkaido": [(140, 42), (141.5, 42.6), (145.3, 43.3), (144, 44.2), (141.8, 45.3), (141.5, 43.5), (140.3, 43.3)],
    "sri_lanka": [(80, 9.8), (81.8, 7.5), (81, 6), (80, 6), (79.8, 8)],
    "sumatra": [(95.3, 2.5), (97, 5.2), (100.5, 2.2), (103.7, -1), (106, -3), (105.8, -5.9), (102, -4), (98.5, 0.5)],
    "java": [(105.5, -6.8), (108, -6.3), (111, -6.5), (114.5, -7.8), (114.4, -8.7), (110, -8.2), (106, -7.5)],
    "borneo": [
        (109, 1.5),
        (111, 1.8),
        (113, 3.3),
        (116, 6.9),
        (118, 5.8),
        (119, 5),
        (117.5, 1),
        (116, -3.5),
        (114.5, -4),
        (111, -3.2),
        (110, -1.5),
    ],
    "new_guinea": [
        (131, -1.2),
        (135, -3.3),
        (138, -1.8),
        (143, -3.3),
        (147, -6),
        (147.8, -7.8),
        (150.5, -10.5),
        (146, -8.2),
        (143, -9),
        (141, -9.2),
        (138, -8),
        (137.8, -5),
        (134, -4),
        (132.5, -2.8),
    ],
    "luzon": [(120.5, 18.5), (122.2, 18.4), (122, 16), (124, 13), (121.5, 13.5), (120, 14.5), (120.3, 16.5)],
    "mindanao": [(122, 7), (124, 8.7), (126.5, 7.5), (126, 6), (124.5, 6.3), (122.5, 6.9)],
    "australia": [
        (113.5, -22),
        (114, -26),
        (115, -34),
        (118, -35),
        (123, -34),
        (129, -31.5),
        (134, -32.5),
        (136, -34),
        (138, -35),
        (140, -38),
        (144, -38.3),
        (147, -38.5),
        (150, -37),
        (151, -33.5),
        (153, -30),
        (153, -26),
        (150, -22.5),
        (146, -19),
        (145, -15),
        (143.5, -14),
        (142.5, -10.8),
        (141.5, -13),
        (141.5, -17),
        (139, -17.3),
        (136, -15),
        (137, -12),
        (132, -11.2),
        (130, -12.5),
        (127, -14),
        (125, -14.5),
        (122, -17.5),
        (120, -19.5),
        (116, -20.7),
    ],
    "new_zealand_north": [(173, -35), (176, -37.5), (178, -38), (175, -41.5), (174.5, -39.5), (174, -37)],
    "new_zealand_south": [
        (172.7, -40.5),
        (174.3, -41.5),
        (171, -44.5),
        (170.5, -46),
        (166.5, -46),
        (168, -44),
        (171, -42),
    ],
}
lakes = {
    "black_sea": [
        (28.2, 41.2),
        (28, 43),
        (29.5, 45.2),
        (31.5, 46.6),
        (33.5, 46),
        (33.5, 44.5),
        (36.5, 45.2),
        (38, 47),
        (39.5, 47),
        (37.5, 44.5),
        (40, 43.4),
        (41.5, 42),
        (41, 41),
        (36, 41.7),
        (32, 42),
        (29, 41.2),
    ],
    "caspian_sea": [
        (47, 45),
        (49, 46.5),
        (53, 46.8),
        (53, 44),
        (51, 43),
        (51.5, 41),
        (53.5, 40),
        (53.5, 37),
        (50.5, 37),
        (49, 38.5),
        (49, 40.5),
        (50.5, 40.5),
        (47.5, 42.5),
        (47, 44),
    ],
}


def project(lon, lat):
    """Natural Earth projection (Savric et al. 2015): lon/lat in degrees to plane x/y."""
    lam, phi = np.radians(lon), np.radians(lat)
    p2 = phi**2
    p4 = p2**2
    x = lam * (0.8707 - 0.131979 * p2 + p4 * (-0.013791 + p4 * (0.003971 * p2 - 0.001529 * p4)))
    y = phi * (1.007226 + p2 * (0.015085 + p4 * (-0.044475 + 0.028874 * p2 - 0.005916 * p4)))
    return x, y


def great_circle(lon0, lat0, lon1, lat1, n=120):
    """n points along the great-circle arc, longitudes unwrapped so the arc is continuous."""
    a = np.array(
        [
            [
                np.cos(np.radians(lat)) * np.cos(np.radians(lon)),
                np.cos(np.radians(lat)) * np.sin(np.radians(lon)),
                np.sin(np.radians(lat)),
            ]
            for lon, lat in ((lon0, lat0), (lon1, lat1))
        ]
    )
    omega = np.arccos(np.clip(a[0] @ a[1], -1, 1))
    t = np.linspace(0, 1, n)[:, None]
    xyz = (np.sin((1 - t) * omega) * a[0] + np.sin(t * omega) * a[1]) / np.sin(omega)
    lon = np.degrees(np.unwrap(np.arctan2(xyz[:, 1], xyz[:, 0])))
    return lon, np.degrees(np.arcsin(xyz[:, 2]))


# Routes as great-circle arcs, cut where they cross the antimeridian so Pacific routes run across the Pacific
arc_rows = []
for route_id, (origin, dest, passengers) in enumerate(df.itertuples(index=False)):
    lon, lat = great_circle(*airports[origin][:2], *airports[dest][:2])
    part = np.floor((lon + 180) / 360).astype(int)
    for k in range(len(lon) - 1):
        if part[k + 1] != part[k]:
            edge = 180 + 360 * min(part[k], part[k + 1])
            lat_edge = lat[k] + (lat[k + 1] - lat[k]) * (edge - lon[k]) / (lon[k + 1] - lon[k])
            lon = np.insert(lon, k + 1, [edge, edge])
            lat = np.insert(lat, k + 1, [lat_edge, lat_edge])
            part = np.insert(part, k + 1, [part[k], part[k + 1]])
            break
    wrapped = lon - 360 * part
    for sub in np.unique(part):
        keep = part == sub
        x, y = project(wrapped[keep], lat[keep])
        arc_rows.append(pd.DataFrame({"x": x, "y": y, "arc": f"{route_id}-{sub}", PASSENGERS: passengers}))
df_arcs = pd.concat(arc_rows, ignore_index=True)


def outline_frame(shapes):
    """Projected polygon vertices; edges are densified so straight sides curve with the projection."""
    rows = []
    for name, ring in shapes.items():
        pts = np.array(ring + [ring[0]], dtype=float)
        dense = np.vstack([np.linspace(a, b, 6)[:-1] for a, b in pairwise(pts)])
        x, y = project(dense[:, 0], dense[:, 1])
        rows.append(pd.DataFrame({"x": x, "y": y, "shape": name}))
    return pd.concat(rows, ignore_index=True)


df_land = outline_frame(landmasses)
df_lakes = outline_frame(lakes)

airport_x, airport_y = project(*np.array([a[:2] for a in airports.values()]).T)
df_airports = pd.DataFrame({"x": airport_x, "y": airport_y, "name": [a[2] for a in airports.values()]})

# Callout for the busiest route, set in open ocean south of its arc
busiest = df.loc[df[PASSENGERS].idxmax()]
callout_x, callout_y = project(-42, 29)
df_callout = pd.DataFrame(
    {
        "x": [float(callout_x)],
        "y": [float(callout_y)],
        "label": [f"Busiest route\n{busiest[ORIGIN]}–{busiest[DEST]} · {busiest[PASSENGERS]}M pax"],
    }
)

# Map extent from the land outlines, with a small margin
margin = 0.03
x_span = df_land["x"].max() - df_land["x"].min()
y_span = df_land["y"].max() - df_land["y"].min()
x_limits = [df_land["x"].min() - margin * x_span, df_land["x"].max() + margin * x_span]
y_limits = [df_land["y"].min() - margin * y_span, df_land["y"].max() + margin * y_span]

# Title font size scaled to length
title = "Global Flight Routes · map-connection-lines · python · letsplot · anyplot.ai"
n = len(title)
ratio = 67 / n if n > 67 else 1.0
title_fontsize = max(11, round(16 * ratio))

# Plot
plot = (
    ggplot()
    + geom_polygon(data=df_land, mapping=aes(x="x", y="y", group="shape"), fill=LAND_FILL, color=LAND_BORDER, size=0.3)
    + geom_polygon(data=df_lakes, mapping=aes(x="x", y="y", group="shape"), fill=PAGE_BG, color=LAND_BORDER, size=0.3)
    + geom_path(data=df_arcs, mapping=aes(x="x", y="y", group="arc", size=PASSENGERS, color=PASSENGERS), alpha=0.6)
    + geom_point(data=df_airports, mapping=aes(x="x", y="y"), size=6, color=PAGE_BG, fill="#009E73", shape=21, stroke=2)
    + geom_text_repel(
        data=df_airports,
        mapping=aes(x="x", y="y", label="name"),
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
    + scale_size(range=[0.5, 6], name=LEGEND_TITLE, guide=guide_legend())
    + scale_color_gradientn(
        colors=[ramp_color(SEQ_MARKS, k / 255) for k in range(256)], name=LEGEND_TITLE, guide=guide_legend()
    )
    + coord_fixed(xlim=x_limits, ylim=y_limits)
    + labs(title=title)
    + theme_void()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=title_fontsize, hjust=0.5, color=INK),
        legend_title=element_text(size=12, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_position="bottom",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    )
)
plot = gggrid([plot]) + ggsize(800, 450) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
