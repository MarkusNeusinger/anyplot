"""anyplot.ai
map-connection-lines: Connection Lines Map (Origin-Destination)
Library: pygal 3.1.3 | Python 3.14.10
Quality: 75/100 | Updated: 2026-11-26
"""

import math
import os
import sys
from itertools import pairwise


# Remove cwd temporarily to resolve the pygal.py → pygal library name conflict
_cwd = sys.path[0] if sys.path else None
if _cwd:
    sys.path.remove(_cwd)

import pandas as pd  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


if _cwd:
    sys.path.insert(0, _cwd)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
OCEAN_BG = "#E8F3F9" if THEME == "light" else "#0C1822"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID_COLOR = "#1A1A1722" if THEME == "light" else "#F0EFE822"

# Imprint palette (positions in canonical order)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential ramp for marks (lines on the page), (position, hex) stops low → high
SEQ_MARKS = (
    [(0.0, "#009E73"), (0.338, "#4467A3"), (1.0, "#002850")]
    if THEME == "light"
    else [(0.0, "#007755"), (0.32, "#009E73"), (1.0, "#CDD9FF")]
)


def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


# Constants
TIER_EDGES = (2000, 3000)  # volume tiers (thousand passengers / year): below, between, above
TIER_WIDTHS = (3, 6, 11)  # stroke width in px per tier, thicker = busier
TIER_OPACITY = (0.85, 0.75, 0.7)
TIER_RAMP_POS = (0.0, 0.5, 1.0) if THEME == "light" else (0.32, 0.62, 1.0)  # positions along SEQ_MARKS
N_SEGMENTS = 24  # points per curved route
BULGE = 0.15  # arc bow as a share of the route length
MAX_BULGE = 20.0  # in degrees

# Coarse world coastlines as (lon, lat) polylines: quiet base map beneath the routes
COASTLINES = [
    [(-125, 50), (-124, 45), (-122, 38), (-117, 33), (-110, 32), (-105, 28)],
    [(-105, 28), (-106, 23), (-105, 20), (-96, 16), (-92, 14), (-86, 12), (-80, 8), (-78, 10)],
    [(-67, 45), (-70, 42), (-74, 40), (-76, 37), (-80, 32), (-81, 28), (-82, 25)],
    [(-82, 25), (-85, 30), (-90, 30), (-95, 28), (-97, 26), (-97, 20), (-90, 21), (-87, 21), (-88, 16), (-83, 10)],
    [(-125, 50), (-130, 55), (-141, 60), (-150, 61), (-165, 55), (-168, 65)],
    [(-168, 65), (-160, 70), (-140, 70), (-125, 70), (-110, 68), (-95, 70)],
    [(-95, 70), (-90, 64), (-94, 58), (-82, 55), (-79, 52), (-78, 60), (-70, 62), (-65, 60), (-60, 55), (-56, 52)],
    [(-56, 52), (-60, 47), (-67, 45)],
    [(-45, 60), (-40, 65), (-35, 70), (-25, 72), (-20, 65), (-30, 60), (-45, 60)],
    [(-24, 65), (-18, 66), (-14, 65), (-19, 63), (-24, 65)],
    [(-35, -6), (-38, -13), (-42, -23), (-48, -28), (-53, -33), (-58, -38), (-66, -55)],
    [(-78, 10), (-80, 0), (-81, -5), (-77, -15), (-72, -30), (-75, -45), (-66, -55)],
    [(-35, -6), (-50, 0), (-60, 8), (-72, 12), (-78, 10)],
    [(-10, 36), (-9, 42), (-5, 44), (0, 43), (3, 43), (5, 47), (3, 51)],
    [(-5, 50), (1, 51), (2, 53), (-2, 57), (-5, 58), (-6, 55), (-3, 53), (-5, 50)],
    [(3, 51), (5, 53), (8, 55), (10, 58), (18, 60), (25, 66), (28, 70)],
    [(28, 70), (40, 67), (44, 68), (60, 69), (70, 73), (80, 73), (100, 77), (113, 74), (130, 71), (150, 71)],
    [(150, 71), (160, 69), (170, 70), (180, 68)],
    [(-180, 68), (-170, 66), (-168, 65)],
    [(-10, 36), (0, 37), (10, 43), (18, 40), (23, 37), (26, 35), (27, 40), (36, 41), (41, 41)],
    [(-17, 21), (-13, 27), (-10, 36)],
    [(-17, 14), (-17, 21)],
    [(-17, 14), (-15, 12), (-13, 10), (-5, 5), (0, 6), (5, 4), (10, 5)],
    [(30, 31), (34, 30), (42, 14), (48, 8), (45, 0), (40, -5), (35, -22), (27, -34)],
    [(27, -34), (20, -34), (17, -30), (12, -17), (10, 5)],
    [(44, -25), (47, -25), (50, -15), (49, -12), (44, -17), (44, -25)],
    [(30, 31), (35, 32), (42, 30), (50, 27), (55, 25), (60, 25)],
    [(60, 25), (66, 24), (72, 22), (72, 8), (80, 8), (88, 22), (90, 22)],
    [(90, 22), (100, 14), (104, 2), (102, -5), (106, -7), (110, -8)],
    [(100, 14), (100, 8), (103, 1)],
    [(106, 22), (106, 17), (109, 12), (105, 9), (100, 13)],
    [(95, 5), (100, 0), (104, -5)],
    [(109, 2), (117, 7), (119, 1), (116, -4), (110, -3), (109, 2)],
    [(120, 18), (122, 14), (125, 8), (122, 7)],
    [(131, -1), (141, -3), (150, -10), (142, -9), (135, -4), (131, -1)],
    [(120, 32), (122, 37), (124, 40), (130, 43), (135, 44), (141, 45)],
    [(124, 40), (126, 37), (126, 34), (129, 35), (129, 38)],
    [(100, 22), (106, 22), (110, 20), (117, 24), (120, 32)],
    [(141, 45), (140, 52), (137, 54), (143, 59), (155, 59), (163, 62), (180, 65)],
    [(156, 51), (160, 54), (163, 58)],
    [(130, 32), (132, 34), (135, 35), (140, 36), (141, 41), (145, 44)],
    [
        (113, -22),
        (130, -14),
        (145, -15),
        (150, -23),
        (153, -28),
        (150, -38),
        (142, -38),
        (130, -32),
        (117, -35),
        (113, -22),
    ],
    [(173, -41), (175, -37), (178, -38), (177, -44), (170, -46), (168, -45), (173, -41)],
]

# Columns: set these to your table's column names
ORIGIN = "Origin"  # role: label
ORIGIN_LAT = "Origin latitude (°)"  # role: origin_lat
ORIGIN_LON = "Origin longitude (°)"  # role: origin_lon
DEST = "Destination"  # role: label
DEST_LAT = "Destination latitude (°)"  # role: dest_lat
DEST_LON = "Destination longitude (°)"  # role: dest_lon
PASSENGERS = "Passengers (thousand / year)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("routes.csv")
airports = {
    "JFK": (40.64, -73.78, "New York"),
    "LAX": (33.94, -118.41, "Los Angeles"),
    "LHR": (51.47, -0.46, "London"),
    "CDG": (49.01, 2.55, "Paris"),
    "DXB": (25.25, 55.36, "Dubai"),
    "HND": (35.55, 139.78, "Tokyo"),
    "SIN": (1.36, 103.99, "Singapore"),
    "SYD": (-33.95, 151.18, "Sydney"),
    "HKG": (22.31, 113.91, "Hong Kong"),
    "FRA": (50.03, 8.57, "Frankfurt"),
    "ORD": (41.98, -87.90, "Chicago"),
    "PEK": (40.08, 116.58, "Beijing"),
    "GRU": (-23.43, -46.47, "Sao Paulo"),
    "JNB": (-26.13, 28.23, "Johannesburg"),
}
routes = [
    ("JFK", "LHR", 4200),
    ("JFK", "CDG", 2100),
    ("LAX", "HND", 3500),
    ("LAX", "SYD", 1800),
    ("LHR", "DXB", 3800),
    ("LHR", "HKG", 2900),
    ("LHR", "JFK", 4200),
    ("CDG", "JFK", 2100),
    ("DXB", "SIN", 3200),
    ("DXB", "LHR", 3800),
    ("HND", "SIN", 2400),
    ("HND", "LAX", 3500),
    ("SIN", "SYD", 2800),
    ("SIN", "HKG", 3100),
    ("HKG", "LHR", 2900),
    ("HKG", "SIN", 3100),
    ("FRA", "JFK", 2600),
    ("FRA", "DXB", 2200),
    ("ORD", "LHR", 2800),
    ("ORD", "FRA", 1900),
    ("PEK", "LAX", 2300),
    ("PEK", "FRA", 1700),
    ("GRU", "JFK", 1500),
    ("GRU", "LHR", 1200),
    ("JNB", "DXB", 1400),
    ("JNB", "LHR", 1100),
    ("SYD", "LAX", 1800),
    ("SYD", "SIN", 2800),
]
df = pd.DataFrame(
    {
        ORIGIN: [airports[o][2] for o, _, _ in routes],
        ORIGIN_LAT: [airports[o][0] for o, _, _ in routes],
        ORIGIN_LON: [airports[o][1] for o, _, _ in routes],
        DEST: [airports[d][2] for _, d, _ in routes],
        DEST_LAT: [airports[d][0] for _, d, _ in routes],
        DEST_LON: [airports[d][1] for _, d, _ in routes],
        PASSENGERS: [v for _, _, v in routes],
    }
)

# Plot
tier_colors = [ramp_color(SEQ_MARKS, t) for t in TIER_RAMP_POS]

custom_style = Style(
    background=PAGE_BG,
    plot_background=OCEAN_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=GRID_COLOR,
    major_guide_stroke_color=GRID_COLOR,
    guide_stroke_dasharray="2,6",
    colors=(*tier_colors, INK, INK_MUTED),
    opacity=0.65,
    opacity_hover=0.95,
    title_font_size=66,
    label_font_size=48,
    major_label_font_size=48,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

# pygal's `.reactive` rule sets stroke-width on the path itself, which beats the per-series
# width inherited from the group, so the tier widths go in as `!important` rules
tier_css = "\n".join(f".series.serie-{i} .line{{stroke-width:{w}px !important}}" for i, w in enumerate(TIER_WIDTHS))

chart = pygal.XY(
    css=["file://style.css", "file://graph.css", "inline:" + tier_css],
    width=3200,
    height=1800,
    style=custom_style,
    title="map-connection-lines · python · pygal · anyplot.ai",
    x_title="Longitude (°)",
    y_title="Latitude (°)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    legend_box_size=28,
    stroke=True,
    dots_size=3,
    show_x_guides=True,
    show_y_guides=True,
    explicit_size=True,
    print_values=False,
    xrange=(-180, 180),
    range=(df[[ORIGIN_LAT, DEST_LAT]].min().min() - 25, df[[ORIGIN_LAT, DEST_LAT]].max().max() + 30),
    margin=70,
    margin_top=120,
    margin_bottom=130,
)

# Volume tiers, drawn as quadratic arcs; a route that crosses the antimeridian is split there
tier_of = pd.cut(df[PASSENGERS], [-math.inf, TIER_EDGES[0] - 1, TIER_EDGES[1], math.inf], labels=False)
tier_names = [
    f"Routes < {TIER_EDGES[0] // 1000}M",
    f"Routes {TIER_EDGES[0] // 1000}-{TIER_EDGES[1] // 1000}M",
    f"Routes > {TIER_EDGES[1] // 1000}M",
]
for tier, name in enumerate(tier_names):
    points = []
    for row in df[tier_of == tier].itertuples(index=False):
        o_city, o_lat, o_lon, d_city, d_lat, d_lon, volume = row
        label = f"{o_city} → {d_city}: {volume}K passengers"
        # take the shorter way around the globe, so Pacific routes cross ±180°
        if d_lon - o_lon > 180:
            d_lon -= 360
        elif d_lon - o_lon < -180:
            d_lon += 360
        dx, dy = d_lon - o_lon, d_lat - o_lat
        length = math.hypot(dx, dy)
        sign = 1 if dx >= 0 else -1  # bow toward the north for eastbound and westbound routes alike
        offset = min(length * BULGE, MAX_BULGE)
        ctrl_lon = (o_lon + d_lon) / 2 + sign * (-dy / length) * offset
        ctrl_lat = (o_lat + d_lat) / 2 + sign * (dx / length) * offset
        curve = []
        for i in range(N_SEGMENTS + 1):
            t = i / N_SEGMENTS
            curve.append(
                (
                    (1 - t) ** 2 * o_lon + 2 * (1 - t) * t * ctrl_lon + t**2 * d_lon,
                    (1 - t) ** 2 * o_lat + 2 * (1 - t) * t * ctrl_lat + t**2 * d_lat,
                )
            )
        for (lon0, lat0), (lon1, lat1) in pairwise(curve):
            wrap0, wrap1 = math.floor((lon0 + 180) / 360), math.floor((lon1 + 180) / 360)
            if not points or points[-1] is None:
                points.append({"value": (lon0 - 360 * wrap0, lat0), "label": label})
            if wrap0 != wrap1:
                edge = 180 + 360 * min(wrap0, wrap1)
                lat_edge = lat0 + (lat1 - lat0) * (edge - lon0) / (lon1 - lon0)
                side = 180 if wrap1 > wrap0 else -180
                points.append({"value": (side, lat_edge), "label": label})
                points.append((0, None))
                points.append({"value": (-side, lat_edge), "label": label})
            points.append({"value": (lon1 - 360 * wrap1, lat1), "label": label})
        points.append((0, None))
    chart.add(
        name,
        points,
        stroke=True,
        show_dots=False,
        allow_interruptions=True,
        stroke_style={"width": TIER_WIDTHS[tier], "linecap": "round", "opacity": TIER_OPACITY[tier]},
    )

# Airport markers: every distinct origin or destination at its coordinates
ends = pd.concat(
    [
        df[[ORIGIN, ORIGIN_LAT, ORIGIN_LON]].set_axis(["city", "lat", "lon"], axis=1),
        df[[DEST, DEST_LAT, DEST_LON]].set_axis(["city", "lat", "lon"], axis=1),
    ]
).drop_duplicates("city")
chart.add(
    "Airports", [{"value": (r.lon, r.lat), "label": r.city} for r in ends.itertuples()], stroke=False, dots_size=16
)

# Coastlines last, low opacity so routes show through
coastline_points = []
for coastline in COASTLINES:
    coastline_points.extend({"value": (lon, lat), "label": "Coastline"} for lon, lat in coastline)
    coastline_points.append((0, None))
chart.add(
    "Coastlines",
    coastline_points,
    stroke=True,
    show_dots=False,
    allow_interruptions=True,
    stroke_style={"width": 2, "opacity": 0.25},
)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
