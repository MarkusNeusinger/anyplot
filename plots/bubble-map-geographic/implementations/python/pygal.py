"""anyplot.ai
bubble-map-geographic: Bubble Map with Sized Geographic Markers
Library: pygal | Python 3.13
Quality: pending | Created: 2026-05-18
"""

import os
import sys


_cwd = sys.path[0] if sys.path and sys.path[0] else None
if _cwd:
    sys.path.remove(_cwd)

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


if _cwd:
    sys.path.insert(0, _cwd)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
OCEAN_BG = "#C8DDF0" if THEME == "light" else "#0D2535"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
COAST_COLOR = "#A0A096" if THEME == "light" else "#5A5A52"
BRAND = "#009E73"

# Data — major world cities with population (millions)
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
    "Istanbul": (41.01, 28.98, 15.4),
    "Buenos Aires": (-34.60, -58.38, 15.4),
    "Lagos": (6.52, 3.38, 14.9),
    "Los Angeles": (34.05, -118.24, 12.5),
    "Moscow": (55.76, 37.62, 12.5),
    "Bangkok": (13.76, 100.50, 10.7),
    "Jakarta": (-6.21, 106.85, 10.6),
    "Paris": (48.86, 2.35, 11.0),
    "Seoul": (37.57, 126.98, 9.8),
    "London": (51.51, -0.13, 9.5),
    "Sydney": (-33.87, 151.21, 5.4),
}

# Simplified world coastlines (longitude, latitude)
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
    # Mexico / Central America
    [(-117, 33), (-110, 25), (-97, 20), (-87, 16), (-80, 8), (-90, 22), (-110, 32), (-117, 33)],
    # South America
    [(-78, 10), (-60, 8), (-35, -6), (-42, -23), (-66, -55), (-72, -30), (-78, 10)],
    # Europe / Africa
    [(-10, 36), (10, 37), (30, 31), (42, 14), (35, -22), (17, -30), (0, 6), (-17, 14), (-10, 36)],
    # Northern Europe
    [(-6, 50), (5, 58), (28, 70), (24, 55), (3, 51), (-6, 50)],
    # Asia
    [(28, 70), (100, 77), (170, 60), (120, 32), (100, 14), (72, 25), (40, 46), (28, 70)],
    # India / SE Asia
    [(78, 33), (72, 8), (88, 22), (104, 2), (78, 33)],
    # Japan
    [(130, 32), (145, 44), (130, 32)],
    # Australia
    [(113, -22), (150, -23), (140, -38), (113, -22)],
]

# Continuous bubble sizing: area ∝ population → dots_size ∝ sqrt(population)
pops = {name: data[2] for name, data in cities.items()}
k_scale = 78.0 / max(pops.values()) ** 0.5
city_sizes = {name: round(k_scale * pop**0.5) for name, pop in pops.items()}

# Size legend reference markers placed in south Pacific (open ocean)
LEGEND_POPS = [5, 15, 25, 37]
legend_sizes = [round(k_scale * lpop**0.5) for lpop in LEGEND_POPS]
LEGEND_LON = -158
LEGEND_LATS = [-31, -38, -45, -52]

n_coasts = len(coastlines)
n_cities = len(cities)
n_legend = len(LEGEND_POPS)

# Color tuple: coast gray × n_coasts, brand green × (cities + legend entries)
colors_tuple = (COAST_COLOR,) * n_coasts + (BRAND,) * (n_cities + n_legend)

custom_style = Style(
    background=PAGE_BG,
    plot_background=OCEAN_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=colors_tuple,
    opacity=0.72,
    opacity_hover=0.9,
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=40,
    legend_font_size=40,
    value_font_size=36,
    tooltip_font_size=36,
    stroke_width=2,
)

# Plot
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="bubble-map-geographic · python · pygal · anyplot.ai",
    x_title="Longitude (°)",
    y_title="Latitude (°)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=40,
    stroke=False,
    dots_size=3,
    show_x_guides=False,
    show_y_guides=False,
    explicit_size=True,
    print_values=False,
    xrange=(-180, 180),
    range=(-60, 80),
)

# Coastlines (title=None → no legend entry)
for coords in coastlines:
    chart.add(None, coords, stroke=True, dots_size=0, show_dots=False, fill=False)

# Cities: one series per city, dots_size proportional to sqrt(population)
for name, (lat, lon, _pop) in cities.items():
    chart.add(None, [{"value": (lon, lat), "label": f"{name}: {_pop}M"}], stroke=False, dots_size=city_sizes[name])

# Size legend: reference markers in south Pacific showing size scale
for lpop, lsize, llat in zip(LEGEND_POPS, legend_sizes, LEGEND_LATS, strict=False):
    chart.add(
        f"{lpop}M pop", [{"value": (LEGEND_LON, llat), "label": f"Reference: {lpop}M"}], stroke=False, dots_size=lsize
    )

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
