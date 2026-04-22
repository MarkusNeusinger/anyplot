""" pyplots.ai
bubble-map-geographic: Bubble Map with Sized Geographic Markers
Library: pygal 3.1.0 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-10
"""

# Fix module name conflict (this file is named pygal.py)
import sys


_cwd = sys.path[0] if sys.path and sys.path[0] else None
if _cwd:
    sys.path.remove(_cwd)

import numpy as np  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


if _cwd:
    sys.path.insert(0, _cwd)


# Data - Major world cities with population data (millions)
np.random.seed(42)

cities = {
    "Tokyo": (35.68, 139.69, 37.4),
    "Delhi": (28.61, 77.21, 32.9),
    "Shanghai": (31.23, 121.47, 28.5),
    "Sao Paulo": (-23.55, -46.63, 22.4),
    "Mexico City": (19.43, -99.13, 21.8),
    "Cairo": (30.04, 31.24, 21.3),
    "Mumbai": (19.08, 72.88, 20.7),
    "Beijing": (39.90, 116.41, 20.5),
    "New York": (40.71, -74.01, 18.8),
    "Los Angeles": (34.05, -118.24, 12.5),
    "Paris": (48.86, 2.35, 11.0),
    "London": (51.51, -0.13, 9.5),
    "Moscow": (55.76, 37.62, 12.5),
    "Istanbul": (41.01, 28.98, 15.4),
    "Lagos": (6.52, 3.38, 14.9),
    "Buenos Aires": (-34.60, -58.38, 15.4),
    "Sydney": (-33.87, 151.21, 5.4),
    "Seoul": (37.57, 126.98, 9.8),
    "Bangkok": (13.76, 100.50, 10.7),
    "Jakarta": (-6.21, 106.85, 10.6),
}

# Extract data
names = list(cities.keys())
lats = [cities[c][0] for c in names]
lons = [cities[c][1] for c in names]
populations = [cities[c][2] for c in names]

# Simplified world coastlines as XY series (longitude, latitude format for pygal XY)
coastlines = [
    # North America
    [
        (-125, 50),
        (-141, 60),
        (-165, 55),
        (-168, 52),
        (-148, 60),
        (-130, 55),
        (-120, 49),
        (-95, 49),
        (-80, 45),
        (-67, 45),
        (-75, 35),
        (-81, 25),
        (-90, 30),
        (-97, 26),
        (-110, 32),
        (-125, 50),
    ],
    # Mexico/Central America
    [(-117, 33), (-110, 25), (-97, 20), (-87, 16), (-80, 8), (-90, 22), (-110, 32), (-117, 33)],
    # South America
    [(-78, 10), (-60, 8), (-35, -6), (-42, -23), (-66, -55), (-72, -30), (-78, 10)],
    # Europe/Africa
    [(-10, 36), (10, 37), (30, 31), (42, 14), (35, -22), (17, -30), (0, 6), (-17, 14), (-10, 36)],
    # Northern Europe
    [(-6, 50), (5, 58), (28, 70), (24, 55), (3, 51), (-6, 50)],
    # Asia
    [(28, 70), (100, 77), (170, 60), (120, 32), (100, 14), (72, 25), (40, 46), (28, 70)],
    # India/SE Asia
    [(78, 33), (72, 8), (88, 22), (104, 2), (78, 33)],
    # Japan
    [(130, 32), (145, 44), (130, 32)],
    # Australia
    [(113, -22), (150, -23), (140, -38), (113, -22)],
]

# Bin cities by population for bubble sizing
small_cities = []  # < 12M
medium_cities = []  # 12-20M
large_cities = []  # 20-30M
mega_cities = []  # > 30M

for i, name in enumerate(names):
    lat, lon, pop = lats[i], lons[i], populations[i]
    point = {"value": (lon, lat), "label": f"{name}: {pop}M"}

    if pop < 12:
        small_cities.append(point)
    elif pop < 20:
        medium_cities.append(point)
    elif pop < 30:
        large_cities.append(point)
    else:
        mega_cities.append(point)

# Custom style for 4800x2700 canvas
# Colors: 9 gray for coastlines, then 4 for population categories
custom_style = Style(
    background="white",
    plot_background="#C8DDF0",  # Ocean blue background
    foreground="#333333",
    foreground_strong="#111111",
    foreground_subtle="#666666",
    guide_stroke_color="#88888866",  # Semi-transparent gray grid lines
    guide_stroke_dasharray="5,5",  # Dashed grid lines for visibility
    colors=(
        # Gray for all coastlines (9 series)
        "#999999",
        "#999999",
        "#999999",
        "#999999",
        "#999999",
        "#999999",
        "#999999",
        "#999999",
        "#999999",
        # City bubble colors - distinct colors for population sizes
        "#306998",  # Python Blue - small
        "#4a8cc2",  # Light blue - medium
        "#FFD43B",  # Python Yellow - large
        "#E24A33",  # Red-orange - mega
    ),
    opacity=0.7,
    opacity_hover=0.9,
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=40,
    legend_font_size=40,
    value_font_size=36,
    tooltip_font_size=36,
)

# Create XY chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="bubble-map-geographic · pygal · pyplots.ai",
    x_title="Longitude (°)",
    y_title="Latitude (°)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=30,
    stroke=True,
    dots_size=3,
    show_x_guides=True,
    show_y_guides=True,
    explicit_size=True,
    print_values=False,
    xrange=(-180, 180),
    range=(-60, 80),
)

# Add coastlines as background (None title = no legend entry in pygal)
for coords in coastlines:
    chart.add(None, coords, stroke=True, dots_size=0, show_dots=False, fill=False)

# Add city bubbles by population category (increased sizes for visibility)
chart.add("Pop < 12M", small_cities, stroke=False, dots_size=28)
chart.add("Pop 12-20M", medium_cities, stroke=False, dots_size=42)
chart.add("Pop 20-30M", large_cities, stroke=False, dots_size=58)
chart.add("Pop > 30M", mega_cities, stroke=False, dots_size=78)

# Save outputs (PNG first as primary, then HTML for interactivity)
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
