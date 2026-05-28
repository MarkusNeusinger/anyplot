"""anyplot.ai
map-connection-lines: Connection Lines Map (Origin-Destination)
Library: pygal 3.1.0 | Python 3.13.13
Quality: 81/100 | Updated: 2026-05-28
"""

import os
import sys


# Remove cwd temporarily to resolve the pygal.py → pygal library name conflict
_cwd = sys.path[0] if sys.path else None
if _cwd:
    sys.path.remove(_cwd)

import numpy as np  # noqa: E402
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

# Data - Major international flight routes with passenger volumes (thousands/year)
np.random.seed(42)

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

route_data = []
for origin, dest, volume in routes:
    o_lat, o_lon, o_city = airports[origin]
    d_lat, d_lon, d_city = airports[dest]
    route_data.append(
        {
            "origin_lat": o_lat,
            "origin_lon": o_lon,
            "dest_lat": d_lat,
            "dest_lon": d_lon,
            "volume": volume,
            "origin_city": o_city,
            "dest_city": d_city,
        }
    )

coastlines = [
    [(-125, 50), (-124, 45), (-122, 38), (-117, 33), (-110, 32), (-105, 28)],
    [(-67, 45), (-70, 42), (-74, 40), (-76, 37), (-80, 32), (-81, 28), (-82, 25)],
    [(-82, 25), (-85, 30), (-90, 30), (-95, 28), (-97, 26), (-105, 28)],
    [(-125, 50), (-130, 55), (-141, 60), (-150, 61), (-165, 55), (-168, 65)],
    [(-45, 60), (-40, 65), (-35, 70), (-25, 72), (-20, 65), (-30, 60), (-45, 60)],
    [(-35, -6), (-38, -13), (-42, -23), (-48, -28), (-53, -33), (-58, -38), (-66, -55)],
    [(-78, 10), (-80, 0), (-81, -5), (-77, -15), (-72, -30), (-75, -45), (-66, -55)],
    [(-10, 36), (-9, 42), (-5, 44), (0, 43), (3, 43), (5, 47), (3, 51)],
    [(3, 51), (5, 53), (8, 55), (10, 58), (18, 60), (25, 66), (28, 70)],
    [(-10, 36), (0, 37), (10, 43), (18, 40), (23, 37), (26, 35), (30, 31)],
    [(-17, 14), (-15, 12), (-13, 10), (-5, 5), (0, 6), (5, 4), (10, 5)],
    [(30, 31), (34, 30), (42, 14), (48, 8), (45, 0), (40, -5), (35, -22), (27, -34)],
    [(27, -34), (20, -34), (17, -30), (12, -17), (10, 5)],
    [(30, 31), (35, 32), (42, 30), (50, 27), (55, 25), (60, 25)],
    [(60, 25), (66, 24), (72, 22), (72, 8), (80, 8), (88, 22), (90, 22)],
    [(90, 22), (100, 14), (104, 2), (102, -5), (106, -7), (110, -8)],
    [(120, 32), (122, 37), (124, 40), (130, 43), (135, 44), (141, 45)],
    [(100, 22), (106, 22), (110, 20), (117, 24), (120, 32)],
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

# Plot - colors ordered: routes first (pos 0-2 = brand green/lavender/blue),
# then airports (pos 3), then coastlines last (pos 4 = INK_MUTED)
custom_style = Style(
    background=PAGE_BG,
    plot_background=OCEAN_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=GRID_COLOR,
    guide_stroke_dasharray="2,6",
    colors=(
        "#009E73",  # Routes < 2M (anyplot palette pos 0 — brand green, first series)
        "#C475FD",  # Routes 2-3M (anyplot palette pos 1)
        "#4467A3",  # Routes > 3M (anyplot palette pos 2)
        INK,  # Airports (theme-adaptive endpoint markers)
        INK_MUTED,  # Coastlines (geographic context, drawn last)
    ),
    opacity=0.65,
    opacity_hover=0.95,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

chart = pygal.XY(
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
    range=(-60, 80),
    margin=70,
    margin_top=120,
    margin_bottom=130,
)

n_segments = 20


def build_bezier_curves(route_list):
    curves = []
    for route in route_list:
        o_lat, o_lon = route["origin_lat"], route["origin_lon"]
        d_lat, d_lon = route["dest_lat"], route["dest_lon"]
        label = f"{route['origin_city']} → {route['dest_city']}: {route['volume']}K passengers"
        mid_lon = (o_lon + d_lon) / 2
        mid_lat = (o_lat + d_lat) / 2
        dx, dy = d_lon - o_lon, d_lat - o_lat
        length = np.sqrt(dx * dx + dy * dy)
        if length > 0:
            perp_x, perp_y = -dy / length, dx / length
            # Pacific-crossing routes: flip perpendicular to arc northward over the pole
            if abs(d_lon - o_lon) > 150:
                perp_x, perp_y = -perp_x, -perp_y
            offset_amount = min(length * 0.15, 20.0)
            ctrl_lon = mid_lon + perp_x * offset_amount
            ctrl_lat = mid_lat + perp_y * offset_amount
        else:
            ctrl_lon, ctrl_lat = mid_lon, mid_lat
        for i in range(n_segments + 1):
            t = i / n_segments
            lon = (1 - t) ** 2 * o_lon + 2 * (1 - t) * t * ctrl_lon + t**2 * d_lon
            lat = (1 - t) ** 2 * o_lat + 2 * (1 - t) * t * ctrl_lat + t**2 * d_lat
            curves.append({"value": (lon, lat), "label": label})
        curves.append({"value": (None, None)})
    return curves


low_routes = [r for r in route_data if r["volume"] < 2000]
medium_routes = [r for r in route_data if 2000 <= r["volume"] <= 3000]
high_routes = [r for r in route_data if r["volume"] > 3000]

# Routes added first — occupy palette positions 0-2 (brand green, lavender, blue)
chart.add(
    "Routes < 2M",
    build_bezier_curves(low_routes),
    stroke=True,
    show_dots=False,
    stroke_style={"width": 3, "linecap": "round", "opacity": 0.55},
)
chart.add(
    "Routes 2-3M",
    build_bezier_curves(medium_routes),
    stroke=True,
    show_dots=False,
    stroke_style={"width": 5, "linecap": "round", "opacity": 0.60},
)
chart.add(
    "Routes > 3M",
    build_bezier_curves(high_routes),
    stroke=True,
    show_dots=False,
    stroke_style={"width": 8, "linecap": "round", "opacity": 0.65},
)

# Airport markers — palette position 3 (INK, theme-adaptive)
airport_points = []
for code, (lat, lon, city) in airports.items():
    airport_points.append({"value": (lon, lat), "label": f"{city} ({code})"})

chart.add("Airports", airport_points, stroke=False, dots_size=16)

# Coastlines last — palette position 4 (INK_MUTED), low opacity so routes show through
coastline_points = []
for coastline in coastlines:
    for lon, lat in coastline:
        coastline_points.append({"value": (lon, lat), "label": "Coastline"})
    coastline_points.append({"value": (None, None)})

chart.add("Coastlines", coastline_points, stroke=True, show_dots=False, stroke_style={"width": 2, "opacity": 0.25})

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
