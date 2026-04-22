""" pyplots.ai
flowmap-origin-destination: Origin-Destination Flow Map
Library: pygal 3.1.0 | Python 3.13.11
Quality: 78/100 | Created: 2026-01-16
"""

# When run from implementations directory, local pygal.py shadows the package
import sys


if sys.path and sys.path[0].endswith("implementations"):
    sys.path.pop(0)

import numpy as np
import pygal
from pygal.style import Style


# Data: Trade flows between major European ports
np.random.seed(42)

# Major European port cities
ports = {
    "Rotterdam": (51.92, 4.48),
    "Hamburg": (53.55, 9.99),
    "Antwerp": (51.22, 4.40),
    "London": (51.51, -0.13),
    "Le Havre": (49.49, 0.11),
    "Barcelona": (41.39, 2.17),
    "Marseille": (43.30, 5.37),
    "Genoa": (44.41, 8.93),
    "Valencia": (39.47, -0.38),
    "Lisbon": (38.72, -9.14),
    "Piraeus": (37.94, 23.65),
    "Copenhagen": (55.68, 12.57),
    "Gdansk": (54.35, 18.65),
    "Dublin": (53.35, -6.26),
}

# Create flows between major trading pairs
flow_pairs = [
    ("Rotterdam", "Hamburg", 850),
    ("Rotterdam", "Antwerp", 720),
    ("Rotterdam", "London", 680),
    ("Hamburg", "Copenhagen", 450),
    ("Hamburg", "Gdansk", 380),
    ("Antwerp", "Le Havre", 520),
    ("Le Havre", "Barcelona", 340),
    ("Barcelona", "Valencia", 420),
    ("Barcelona", "Marseille", 480),
    ("Marseille", "Genoa", 390),
    ("Genoa", "Barcelona", 360),
    ("Valencia", "Lisbon", 280),
    ("Lisbon", "Le Havre", 310),
    ("Piraeus", "Genoa", 290),
    ("Piraeus", "Marseille", 250),
    ("London", "Dublin", 410),
    ("Rotterdam", "Copenhagen", 370),
    ("Hamburg", "London", 320),
    ("Antwerp", "Barcelona", 260),
    ("Copenhagen", "Gdansk", 220),
]

flow_data = []
for origin, dest, flow in flow_pairs:
    o_lat, o_lon = ports[origin]
    d_lat, d_lon = ports[dest]
    flow_data.append(
        {
            "origin_lat": o_lat,
            "origin_lon": o_lon,
            "dest_lat": d_lat,
            "dest_lon": d_lon,
            "flow": flow,
            "origin_name": origin,
            "dest_name": dest,
        }
    )

# Map boundaries for Europe
lat_min, lat_max = 35.0, 58.0
lon_min, lon_max = -12.0, 28.0

# Simplified European coastlines
coastlines = [
    # Iberian Peninsula
    [
        (-9.5, 37.0),
        (-9.0, 38.7),
        (-8.5, 42.0),
        (-2.0, 43.5),
        (3.0, 42.5),
        (0.0, 40.5),
        (-0.5, 38.0),
        (-5.0, 36.0),
        (-9.5, 37.0),
    ],
    # France/Mediterranean
    [(3.0, 42.5), (6.0, 43.0), (9.5, 44.0), (10.5, 44.5), (13.5, 45.5), (12.5, 44.0), (16.0, 41.0)],
    # Italy
    [(9.5, 44.0), (11.0, 42.0), (15.0, 40.0), (18.0, 40.0), (16.0, 41.0)],
    # Balkans/Greece
    [(20.0, 40.0), (23.0, 38.0), (26.0, 40.0), (24.0, 41.5), (20.0, 40.0)],
    # North Sea/Baltic
    [(-6.0, 50.0), (2.0, 51.0), (5.0, 53.0), (8.0, 54.0), (10.0, 55.0), (12.0, 56.0), (18.0, 55.0), (20.0, 54.5)],
    # UK outline
    [
        (-6.0, 50.0),
        (-5.0, 50.0),
        (-3.0, 51.0),
        (1.5, 51.5),
        (0.0, 53.0),
        (-3.0, 54.0),
        (-5.0, 55.0),
        (-6.0, 56.0),
        (-5.0, 58.0),
    ],
    # Ireland
    [(-10.0, 51.5), (-6.0, 51.5), (-6.0, 54.0), (-8.0, 55.5), (-10.0, 53.5), (-10.0, 51.5)],
]

# Calculate flow ranges for scaling
flows = [f["flow"] for f in flow_data]
min_flow = min(flows)
max_flow = max(flows)
# More pronounced line width differentiation for better visual distinction
min_stroke = 3
mid_stroke = 10
max_stroke = 18

# Custom style - colorblind-safe palette (viridis-inspired)
# Colors: coastlines (gray), low (teal), medium (gold), high (purple), cities (coral)
custom_style = Style(
    background="white",
    plot_background="#F0F8F8",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#888888", "#1F9E89", "#FCA636", "#6A3D9A", "#FF7F50"),
    title_font_size=64,
    legend_font_size=40,
    label_font_size=42,
    major_label_font_size=36,
    value_font_size=36,
    tooltip_font_size=36,
    font_family="sans-serif",
    opacity=0.75,
    opacity_hover=1.0,
)

# Create XY chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="flowmap-origin-destination · pygal · pyplots.ai",
    x_title="Longitude",
    y_title="Latitude",
    show_legend=True,
    legend_at_bottom=False,
    legend_box_size=36,
    truncate_legend=-1,
    margin=100,
    margin_top=180,
    margin_bottom=140,
    margin_right=650,
    margin_left=200,
    range=(lat_min, lat_max),
    xrange=(lon_min, lon_max),
    show_dots=True,
    stroke=True,
    dots_size=14,
    tooltip_border_radius=10,
    show_x_guides=True,
    show_y_guides=True,
)

# Combine all coastlines into a single series with breaks
coastline_points = []
for coastline in coastlines:
    for lon, lat in coastline:
        coastline_points.append({"value": (lon, lat), "label": "European Coastline"})
    coastline_points.append({"value": (None, None)})  # Break between coastline segments

chart.add("Coastlines", coastline_points, stroke=True, show_dots=False, stroke_style={"width": 3})

# Sort flows by magnitude (smaller first so larger are on top visually)
sorted_flows = sorted(flow_data, key=lambda f: f["flow"])

# Group flows into categories for cleaner legend
high_flows = []  # >= 600
medium_flows = []  # 400-599
low_flows = []  # < 400

for flow in sorted_flows:
    if flow["flow"] >= 600:
        high_flows.append(flow)
    elif flow["flow"] >= 400:
        medium_flows.append(flow)
    else:
        low_flows.append(flow)

n_segments = 15

# Add low volume flows
low_curves = []
for flow in low_flows:
    o_lat, o_lon = flow["origin_lat"], flow["origin_lon"]
    d_lat, d_lon = flow["dest_lat"], flow["dest_lon"]
    magnitude = flow["flow"]
    origin_name = flow["origin_name"]
    dest_name = flow["dest_name"]

    mid_lon = (o_lon + d_lon) / 2
    mid_lat = (o_lat + d_lat) / 2
    dx = d_lon - o_lon
    dy = d_lat - o_lat
    length = np.sqrt(dx * dx + dy * dy)

    if length > 0:
        perp_x = -dy / length
        perp_y = dx / length
        offset_amount = min(length * 0.2, 2.5)
        ctrl_lon = mid_lon + perp_x * offset_amount
        ctrl_lat = mid_lat + perp_y * offset_amount
    else:
        ctrl_lon, ctrl_lat = mid_lon, mid_lat

    for i in range(n_segments + 1):
        t = i / n_segments
        lon = (1 - t) ** 2 * o_lon + 2 * (1 - t) * t * ctrl_lon + t**2 * d_lon
        lat = (1 - t) ** 2 * o_lat + 2 * (1 - t) * t * ctrl_lat + t**2 * d_lat
        low_curves.append({"value": (lon, lat), "label": f"{origin_name} → {dest_name}: {magnitude} units"})
    low_curves.append({"value": (None, None)})

chart.add(
    "Low (220-399)", low_curves, stroke=True, show_dots=False, stroke_style={"width": min_stroke, "linecap": "round"}
)

# Add medium volume flows
medium_curves = []
for flow in medium_flows:
    o_lat, o_lon = flow["origin_lat"], flow["origin_lon"]
    d_lat, d_lon = flow["dest_lat"], flow["dest_lon"]
    magnitude = flow["flow"]
    origin_name = flow["origin_name"]
    dest_name = flow["dest_name"]

    mid_lon = (o_lon + d_lon) / 2
    mid_lat = (o_lat + d_lat) / 2
    dx = d_lon - o_lon
    dy = d_lat - o_lat
    length = np.sqrt(dx * dx + dy * dy)

    if length > 0:
        perp_x = -dy / length
        perp_y = dx / length
        offset_amount = min(length * 0.2, 2.5)
        ctrl_lon = mid_lon + perp_x * offset_amount
        ctrl_lat = mid_lat + perp_y * offset_amount
    else:
        ctrl_lon, ctrl_lat = mid_lon, mid_lat

    for i in range(n_segments + 1):
        t = i / n_segments
        lon = (1 - t) ** 2 * o_lon + 2 * (1 - t) * t * ctrl_lon + t**2 * d_lon
        lat = (1 - t) ** 2 * o_lat + 2 * (1 - t) * t * ctrl_lat + t**2 * d_lat
        medium_curves.append({"value": (lon, lat), "label": f"{origin_name} → {dest_name}: {magnitude} units"})
    medium_curves.append({"value": (None, None)})

chart.add(
    "Medium (400-599)",
    medium_curves,
    stroke=True,
    show_dots=False,
    stroke_style={"width": mid_stroke, "linecap": "round"},
)

# Add high volume flows
high_curves = []
for flow in high_flows:
    o_lat, o_lon = flow["origin_lat"], flow["origin_lon"]
    d_lat, d_lon = flow["dest_lat"], flow["dest_lon"]
    magnitude = flow["flow"]
    origin_name = flow["origin_name"]
    dest_name = flow["dest_name"]

    mid_lon = (o_lon + d_lon) / 2
    mid_lat = (o_lat + d_lat) / 2
    dx = d_lon - o_lon
    dy = d_lat - o_lat
    length = np.sqrt(dx * dx + dy * dy)

    if length > 0:
        perp_x = -dy / length
        perp_y = dx / length
        offset_amount = min(length * 0.2, 2.5)
        ctrl_lon = mid_lon + perp_x * offset_amount
        ctrl_lat = mid_lat + perp_y * offset_amount
    else:
        ctrl_lon, ctrl_lat = mid_lon, mid_lat

    for i in range(n_segments + 1):
        t = i / n_segments
        lon = (1 - t) ** 2 * o_lon + 2 * (1 - t) * t * ctrl_lon + t**2 * d_lon
        lat = (1 - t) ** 2 * o_lat + 2 * (1 - t) * t * ctrl_lat + t**2 * d_lat
        high_curves.append({"value": (lon, lat), "label": f"{origin_name} → {dest_name}: {magnitude} units"})
    high_curves.append({"value": (None, None)})

chart.add(
    "High (600-850)", high_curves, stroke=True, show_dots=False, stroke_style={"width": max_stroke, "linecap": "round"}
)

# Add port city locations as the final layer (on top)
city_points = []
drawn_locations = set()

for flow in flow_data:
    o_key = (round(flow["origin_lat"], 2), round(flow["origin_lon"], 2))
    if o_key not in drawn_locations:
        city_points.append({"value": (flow["origin_lon"], flow["origin_lat"]), "label": flow["origin_name"]})
        drawn_locations.add(o_key)

    d_key = (round(flow["dest_lat"], 2), round(flow["dest_lon"], 2))
    if d_key not in drawn_locations:
        city_points.append({"value": (flow["dest_lon"], flow["dest_lat"]), "label": flow["dest_name"]})
        drawn_locations.add(d_key)

chart.add("Port Cities", city_points, dots_size=18, stroke=False)

# Save outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
