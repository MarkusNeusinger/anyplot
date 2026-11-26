""" anyplot.ai
map-tile-background: Map with Tile Background
Library: pygal 3.1.3 | Python 3.14.10
Quality: 76/100 | Updated: 2026-11-26
"""

import importlib
import math
import os
import sys

import pandas as pd


# Remove cwd from path to avoid importing this file instead of the pygal library
_cwd = sys.path[0] if sys.path and sys.path[0] else None
if _cwd:
    sys.path.remove(_cwd)
_pygal = importlib.import_module("pygal")
_style_mod = importlib.import_module("pygal.style")
if _cwd:
    sys.path.insert(0, _cwd)

Style = _style_mod.Style

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
# Semantic exception: temperature carries a strong cold -> blue, mild -> green, hot -> red expectation
BAND_COLORS = [IMPRINT_PALETTE[2], IMPRINT_PALETTE[0], IMPRINT_PALETTE[4]]  # cool, mild, warm
BAND_LIMITS = [12, 22]  # annual mean in deg C that separates cool | mild | warm
BAND_NAMES = ["Annual mean < 12 °C", "Annual mean 12–22 °C", "Annual mean > 22 °C"]
DOT_SIZES = [16, 20, 24]  # redundant size encoding per band, aids color-vision accessibility

# Columns: set these to your table's column names
LAT = "Latitude (°)"  # role: lat
LON = "Longitude (°)"  # role: lon
TEMP = "Annual mean temperature (°C)"  # role: value
STATION = "Station"  # role: label

# Data: replace this block with your own table, for example df = pd.read_csv("stations.csv")
# US weather monitoring network, mean annual surface temperatures
df = pd.DataFrame(
    {
        STATION: [
            "Seattle",
            "Portland",
            "San Francisco",
            "Los Angeles",
            "Phoenix",
            "Denver",
            "Dallas",
            "Houston",
            "Minneapolis",
            "Chicago",
            "Detroit",
            "Atlanta",
            "Miami",
            "Washington DC",
            "New York",
            "Boston",
            "Nashville",
            "New Orleans",
            "Kansas City",
            "Salt Lake City",
            "Las Vegas",
            "Albuquerque",
            "Memphis",
            "Charlotte",
            "Tampa",
        ],
        LAT: [47.6, 45.5, 37.8, 34.1, 33.4, 39.7, 32.8, 29.8, 44.9, 41.9, 42.3, 33.7, 25.8]
        + [38.9, 40.7, 42.4, 36.2, 30.0, 39.1, 40.8, 36.2, 35.1, 35.1, 35.2, 28.0],
        LON: [-122.3, -122.7, -122.4, -118.2, -112.1, -104.9, -96.8, -95.4, -93.2, -87.6, -83.0, -84.4, -80.2]
        + [-77.0, -74.0, -71.1, -86.8, -90.1, -94.6, -111.9, -115.2, -106.7, -90.0, -80.8, -82.5],
        TEMP: [11.0, 12.0, 13.5, 19.0, 28.5, 10.5, 19.5, 24.5, 7.5, 9.5, 8.5, 17.5, 27.0]
        + [13.5, 12.5, 10.0, 15.5, 23.0, 12.5, 11.5, 20.0, 14.5, 18.0, 16.0, 25.0],
    }
)

# Plot: reads only df and the constants above
# View fitted to the data bounds: ticks every 10° longitude and 5° latitude, padded frame
lat_min, lat_max = 5 * math.floor(df[LAT].min() / 5), 5 * math.ceil(df[LAT].max() / 5)
lon_min, lon_max = 10 * math.floor(df[LON].min() / 10), 10 * math.ceil(df[LON].max() / 10)
x_pad = 0.06 * (lon_max - lon_min)

title = "map-tile-background · python · pygal · anyplot.ai"
n = len(title)
ratio = 67 / n if n > 67 else 1.0
title_font_size = max(44, round(66 * ratio))

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=tuple(BAND_COLORS),
    title_font_size=title_font_size,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
    opacity=0.9,
    opacity_hover=1.0,
)

chart = _pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    x_title=LON,
    y_title=LAT,
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=36,
    show_x_guides=True,
    show_y_guides=True,
    dots_size=18,
    stroke=False,
    margin=60,
    margin_top=110,
    margin_bottom=240,
    margin_left=200,
    margin_right=80,
    range=(lat_min - 1, lat_max + 1),
    xrange=(lon_min - x_pad, lon_max + x_pad),
    print_values=False,
    truncate_legend=-1,
    truncate_label=-1,
    explicit_size=True,
)

# Group stations into temperature bands (cool | mild | warm)
band = pd.cut(df[TEMP], [-math.inf, *BAND_LIMITS, math.inf], right=False, labels=False)
for i, name in enumerate(BAND_NAMES):
    rows = df[band == i]
    points = [
        {"value": (lon, lat), "label": f"{station}: {temp} °C"}
        for station, lat, lon, temp in zip(rows[STATION], rows[LAT], rows[LON], rows[TEMP], strict=True)
    ]
    chart.add(name, points, dots_size=DOT_SIZES[i])

# Labels with explicit values, so each tick sits at its coordinate
chart.x_labels = [{"label": f"{lon}°", "value": lon} for lon in range(lon_min, lon_max + 1, 10)]
chart.y_labels = [{"label": f"{lat}°", "value": lat} for lat in range(lat_min, lat_max + 1, 5)]

# Save PNG and interactive HTML
chart.render_to_png(f"plot-{THEME}.png")

with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
