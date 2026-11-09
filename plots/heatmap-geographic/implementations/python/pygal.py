""" anyplot.ai
heatmap-geographic: Geographic Heatmap for Spatial Density
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-19
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style
from scipy.stats import gaussian_kde


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# imprint_seq, the sequential Imprint colormap: brand green (low) to blue (high)
SEQ_LOW, SEQ_HIGH = "#009E73", "#4467A3"

# Constants: the basemap, California's outline as (longitude, latitude), offline and simplified;
# clockwise from the Oregon border at the coast, down the coast, then the Mexican, Arizona and Nevada borders
CALIFORNIA = [
    (-124.21, 42.00), (-124.20, 41.75), (-124.08, 41.20), (-124.17, 40.80), (-124.41, 40.44),
    (-124.05, 40.00), (-123.82, 39.60), (-123.74, 38.95), (-123.40, 38.55), (-123.02, 38.00),
    (-122.51, 37.78), (-122.50, 37.50), (-122.36, 37.15), (-122.02, 36.96), (-121.89, 36.60),
    (-121.92, 36.31), (-121.50, 35.90), (-121.28, 35.66), (-120.87, 35.37), (-120.64, 34.90),
    (-120.47, 34.45), (-119.70, 34.41), (-119.23, 34.15), (-118.80, 34.03), (-118.50, 34.02),
    (-118.40, 33.74), (-118.10, 33.74), (-117.78, 33.54), (-117.38, 33.20), (-117.27, 32.85),
    (-117.12, 32.53), (-114.72, 32.72), (-114.47, 33.00), (-114.72, 33.40), (-114.52, 33.95),
    (-114.13, 34.30), (-114.63, 35.00), (-120.00, 39.00), (-120.00, 42.00),
]  # fmt: skip
LEVELS = np.linspace(0.08, 0.9, 14)  # density levels as shares of the peak, outermost first

# Columns: set these to your table's column names
LATITUDE = "Latitude (°N)"  # role: latitude
LONGITUDE = "Longitude (°E)"  # role: longitude
PM25 = "PM2.5 (µg/m³)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("stations.csv")
# Air-quality monitoring stations around Sacramento, the San Joaquin Valley and Los Angeles, plus
# scattered rural sites; draws outside the state outline are rejected, so every station is on land
np.random.seed(42)
lon = np.concatenate([
    np.random.normal(-121.4, 0.45, 220), np.random.normal(-119.8, 0.5, 220),
    np.random.normal(-118.0, 0.55, 220), np.random.uniform(-124.2, -114.2, 240),
])  # fmt: skip
lat = np.concatenate([
    np.random.normal(38.6, 0.35, 220), np.random.normal(36.6, 0.45, 220),
    np.random.normal(34.1, 0.25, 220), np.random.uniform(32.6, 41.9, 240),
])  # fmt: skip
pm25 = np.concatenate([
    np.random.lognormal(2.4, 0.35, 220), np.random.lognormal(2.8, 0.35, 220),
    np.random.lognormal(2.7, 0.35, 220), np.random.lognormal(1.9, 0.4, 240),
])  # fmt: skip
on_land = np.zeros(len(lon), dtype=bool)
for (x1, y1), (x2, y2) in zip(CALIFORNIA, CALIFORNIA[1:] + CALIFORNIA[:1], strict=True):  # ray casting
    on_land ^= ((y1 > lat) != (y2 > lat)) & (lon < x1 + (lat - y1) * (x2 - x1) / (y2 - y1 + 1e-12))
df = pd.DataFrame({LATITUDE: lat[on_land], LONGITUDE: lon[on_land], PM25: pm25[on_land].round(1)})

# Plot: a PM2.5-weighted kernel density on a grid over the map frame
stations = df[[LONGITUDE, LATITUDE, PM25]].dropna().astype(float)
lat_lo, lat_hi = min(y for _, y in CALIFORNIA) - 0.5, max(y for _, y in CALIFORNIA) + 0.5
shrink = np.cos(np.radians((lat_lo + lat_hi) / 2))  # a degree of longitude is this much shorter than one of latitude
# equal distances at equal lengths: the plot area on this square canvas is about as wide as it is tall
lon_span = (lat_hi - lat_lo) * 0.98 / shrink
lon_mid = (min(x for x, _ in CALIFORNIA) + max(x for x, _ in CALIFORNIA)) / 2 - 0.6  # room for the colour bar
lon_lo, lon_hi = lon_mid - lon_span / 2, lon_mid + lon_span / 2
gx = np.linspace(lon_lo, lon_hi, 170)
gy = np.linspace(lat_lo, lat_hi, 170)
kde = gaussian_kde(
    np.vstack([stations[LONGITUDE] * shrink, stations[LATITUDE]]), weights=stations[PM25], bw_method=0.19
)
grid_x, grid_y = np.meshgrid(gx * shrink, gy)
# density[row, col] is the estimate at (gx[col], gy[row])
density = kde(np.vstack([grid_x.ravel(), grid_y.ravel()])).reshape(grid_x.shape)
peak = density.max()

# Marching squares: each level's crossings sit on grid edges; chaining them gives closed rings
rings_by_level = []
for share in LEVELS:
    level = share * peak
    above = density >= level
    points, neighbors = {}, {}
    for r in range(len(gy) - 1):
        for c in range(len(gx) - 1):
            corners = [above[r, c], above[r, c + 1], above[r + 1, c + 1], above[r + 1, c]]  # BL, BR, TR, TL
            if all(corners) or not any(corners):
                continue
            # cell edges in order bottom, right, top, left: (key, end-a value, end-b value, end-a xy, end-b xy)
            edges = [
                (("h", r, c), density[r, c], density[r, c + 1], (gx[c], gy[r]), (gx[c + 1], gy[r])),
                (("v", r, c + 1), density[r, c + 1], density[r + 1, c + 1], (gx[c + 1], gy[r]), (gx[c + 1], gy[r + 1])),
                (("h", r + 1, c), density[r + 1, c], density[r + 1, c + 1], (gx[c], gy[r + 1]), (gx[c + 1], gy[r + 1])),
                (("v", r, c), density[r, c], density[r + 1, c], (gx[c], gy[r]), (gx[c], gy[r + 1])),
            ]
            crossed = []
            for key, za, zb, (xa, ya), (xb, yb) in edges:
                if (za >= level) != (zb >= level):
                    t = (level - za) / (zb - za)
                    points[key] = (xa + t * (xb - xa), ya + t * (yb - ya))
                    crossed.append(key)
            if len(crossed) == 2:
                pairs = [(crossed[0], crossed[1])]
            else:  # saddle: the cell centre decides which corners stay connected
                centre_above = density[r : r + 2, c : c + 2].mean() >= level
                if corners[1] != centre_above:
                    pairs = [(crossed[0], crossed[1]), (crossed[2], crossed[3])]
                else:
                    pairs = [(crossed[3], crossed[0]), (crossed[1], crossed[2])]
            for a, b in pairs:
                neighbors.setdefault(a, []).append(b)
                neighbors.setdefault(b, []).append(a)
    rings, seen = [], set()
    for start in neighbors:
        if start in seen:
            continue
        ring, previous, current = [], None, start
        while current is not None:
            seen.add(current)
            ring.append(points[current])
            following = [key for key in neighbors[current] if key != previous and key not in seen]
            previous, current = current, (following[0] if following else None)
        if start in neighbors[previous]:
            ring.append(points[start])
        rings.append(ring)
    rings_by_level.append(rings)

# Colour bar in the open Pacific: band k is covered by k translucent layers, exactly like the map
bar_x0, bar_x1 = lon_lo + 0.35, lon_lo + 0.75
bar_y0, bar_y1 = lat_lo + 0.9, lat_lo + 4.4
bar_step = (bar_y1 - bar_y0) / len(LEVELS)
level_colors = []
for t in np.linspace(0, 1, len(LEVELS)):
    rgb = [round(int(SEQ_LOW[k : k + 2], 16) * (1 - t) + int(SEQ_HIGH[k : k + 2], 16) * t) for k in (1, 3, 5)]
    level_colors.append(f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}")

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    # series order: the heat levels, the state outline, the stations, the colour-bar captions
    colors=(*level_colors, INK, INK_SOFT, INK),
    value_colors=(INK,) * (len(LEVELS) + 3),
    guide_stroke_color=RULE,
    major_guide_stroke_color=RULE,
    guide_stroke_dasharray="none",
    major_guide_stroke_dasharray="none",
    title_font_size=60,
    label_font_size=42,
    major_label_font_size=42,
    legend_font_size=42,
    value_font_size=0,
    value_label_font_size=38,
    opacity=0.17,
    opacity_hover=0.25,
    stroke_opacity=1,
    stroke_opacity_hover=1,
    stroke_width=4,
)
level_outlines = ", ".join(f".serie-{i} .line" for i in range(len(LEVELS)))  # the heat fills draw no outline

chart = pygal.XY(
    width=2400,
    height=2400,
    style=custom_style,
    title="heatmap-geographic · python · pygal · anyplot.ai",
    x_title="Longitude",
    y_title="Latitude",
    xrange=(lon_lo, lon_hi),
    range=(lat_lo, lat_hi),
    zero=lat_lo,
    x_labels=list(range(int(np.ceil(lon_lo / 2) * 2), int(lon_hi) + 1, 2)),
    y_labels=list(range(int(np.ceil(lat_lo / 2) * 2), int(lat_hi) + 1, 2)),
    x_value_formatter=lambda degrees: f"{abs(degrees):g}°W" if degrees < 0 else f"{degrees:g}°E",
    value_formatter=lambda degrees: f"{degrees:g}°N" if degrees >= 0 else f"{abs(degrees):g}°S",
    show_x_guides=True,
    show_y_guides=True,
    show_dots=False,
    allow_interruptions=True,
    print_labels=True,
    show_legend=False,
    spacing=24,
    margin=40,
    css=[
        "file://style.css",
        "file://graph.css",
        f"inline:{level_outlines} {{ stroke-opacity: 0 !important; }}",
        f"inline:.serie-{len(LEVELS) + 1} .dot {{ fill-opacity: 0.55 !important; }}",
    ],
)

# The heat layer: one translucent fill per level, deepening towards each hot spot; the fill path
# starts and ends on pygal's zero line, so the series are anchored at the frame's bottom-left corner
corner = (lon_lo, lat_lo)
for k, rings in enumerate(rings_by_level):
    bar = [(bar_x0, bar_y0 + k * bar_step), (bar_x1, bar_y0 + k * bar_step), (bar_x1, bar_y1), (bar_x0, bar_y1)]
    values = [corner, (None, None), *bar, bar[0], (None, None)]
    for ring in rings:
        values += [*ring, (None, None)]
    values.append(corner)
    chart.add(None, values, fill=True)
chart.add("California coastline and borders", [*CALIFORNIA, CALIFORNIA[0]])
chart.add(
    "Monitoring station",
    list(zip(stations[LONGITUDE], stations[LATITUDE], strict=True)),
    stroke=False,
    show_dots=True,
    dots_size=4,
)
captions = [
    {"value": (bar_x0, bar_y1 + 0.8), "label": "PM2.5-weighted"},
    {"value": (bar_x0, bar_y1 + 0.5), "label": "density of the"},
    {"value": (bar_x0, bar_y1 + 0.2), "label": "stations (dots)"},
    {"value": (bar_x1 + 0.12, bar_y1 - 0.12), "label": "high"},
    {"value": (bar_x1 + 0.12, bar_y0), "label": "low"},
]
chart.add(None, captions, stroke=False, show_dots=True, dots_size=0)

# Save
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
