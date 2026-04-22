""" pyplots.ai
map-tile-background: Map with Tile Background
Library: pygal 3.1.0 | Python 3.13.11
Quality: 55/100 | Created: 2026-01-20
"""

import sys


# Fix module name conflict (this file is named pygal.py)
_cwd = sys.path[0] if sys.path and sys.path[0] else None
if _cwd:
    sys.path.remove(_cwd)

import numpy as np  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


if _cwd:
    sys.path.insert(0, _cwd)

# Data: European city landmarks with visitor counts (thousands per year)
np.random.seed(42)

landmarks = [
    {"label": "Eiffel Tower", "lat": 48.8584, "lon": 2.2945, "value": 7000},
    {"label": "Colosseum", "lat": 41.8902, "lon": 12.4922, "value": 6500},
    {"label": "Sagrada Familia", "lat": 41.4036, "lon": 2.1744, "value": 4500},
    {"label": "Big Ben", "lat": 51.5007, "lon": -0.1246, "value": 3500},
    {"label": "Brandenburg Gate", "lat": 52.5163, "lon": 13.3777, "value": 3000},
    {"label": "Acropolis", "lat": 37.9715, "lon": 23.7257, "value": 2900},
    {"label": "Anne Frank House", "lat": 52.3752, "lon": 4.8840, "value": 1300},
    {"label": "Prague Castle", "lat": 50.0911, "lon": 14.4008, "value": 2000},
    {"label": "Schonbrunn Palace", "lat": 48.1845, "lon": 16.3122, "value": 3800},
    {"label": "Rijksmuseum", "lat": 52.3600, "lon": 4.8852, "value": 2700},
    {"label": "Uffizi Gallery", "lat": 43.7677, "lon": 11.2553, "value": 2500},
    {"label": "Tower of London", "lat": 51.5081, "lon": -0.0759, "value": 2900},
    {"label": "Notre-Dame", "lat": 48.8530, "lon": 2.3499, "value": 5000},
    {"label": "Louvre Museum", "lat": 48.8606, "lon": 2.3376, "value": 9600},
    {"label": "Vatican Museums", "lat": 41.9065, "lon": 12.4536, "value": 6800},
]

# Map bounds for Europe (expanded to include all landmarks with ample padding)
# Acropolis is at 37.97°N, so we extend southward to 35°N for visibility
lat_min, lat_max = 35, 55
lon_min, lon_max = -3, 26

# Custom style for 4800x2700 canvas with OSM-inspired map appearance
# Note: Pygal cannot render actual tile-based backgrounds; this uses colors
# inspired by OpenStreetMap (ocean blue #aad3df, land beige #f2efe9) to
# simulate a map aesthetic. Tile attribution: Colors inspired by OpenStreetMap.
custom_style = Style(
    background="#aad3df",  # OSM ocean blue as background
    plot_background="#f2efe9",  # OSM land beige as plot area
    foreground="#333333",
    foreground_strong="#111111",
    foreground_subtle="#666666",
    # Distinct colors for better accessibility: orange, teal, purple
    colors=("#e67e22", "#16a085", "#8e44ad"),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=44,
    legend_font_size=40,
    value_font_size=32,
    tooltip_font_size=36,
    guide_stroke_color="#d4cfc4",  # Subtle beige/tan grid lines
    guide_stroke_dasharray="0",  # Solid grid lines
    opacity=0.85,
    opacity_hover=1.0,
)

# Create XY scatter chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="map-tile-background · pygal · pyplots.ai",
    x_title="Longitude (degrees East/West)",
    y_title="Latitude (degrees North)",
    show_legend=True,
    legend_at_bottom=True,  # Move legend to bottom to avoid overlap with data
    legend_box_size=32,
    show_x_guides=True,
    show_y_guides=True,
    dots_size=20,  # Large dots for visibility
    stroke=False,  # No connecting lines
    margin=50,
    margin_top=140,
    margin_bottom=220,
    margin_left=220,
    margin_right=80,
    range=(lat_min, lat_max),  # Y-axis range (latitude)
    xrange=(lon_min, lon_max),  # X-axis range (longitude)
    print_values=False,
    truncate_legend=-1,  # Don't truncate legend text
    explicit_size=True,
)

# Group landmarks by visitor count ranges for legend
# Low: < 3000K, Medium: 3000-6000K, High: > 6000K
low_visitors = []  # 1,300K - 2,999K
medium_visitors = []  # 3,000K - 5,999K
high_visitors = []  # 6,000K - 9,600K

for lm in landmarks:
    point = {"value": (lm["lon"], lm["lat"]), "label": f"{lm['label']}: {lm['value']:,}K visitors/year"}
    if lm["value"] < 3000:
        low_visitors.append(point)
    elif lm["value"] < 6000:
        medium_visitors.append(point)
    else:
        high_visitors.append(point)

# Add series with meaningful legend labels (different colors per range)
chart.add("1,300K–2,999K visitors/year", low_visitors, dots_size=16)
chart.add("3,000K–5,999K visitors/year", medium_visitors, dots_size=22)
chart.add("6,000K–9,600K visitors/year", high_visitors, dots_size=28)

# Set axis labels with degree notation
chart.x_labels = [f"{lon}°" for lon in range(lon_min, lon_max + 1, 5)]
chart.y_labels = [f"{lat}°" for lat in range(lat_min, lat_max + 1, 5)]

# Save output (PNG only)
chart.render_to_png("plot.png")
