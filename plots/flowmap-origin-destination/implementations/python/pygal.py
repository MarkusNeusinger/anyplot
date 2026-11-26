"""anyplot.ai
flowmap-origin-destination: Origin-Destination Flow Map
Library: pygal 3.1.0 | Python 3.13.13
"""

import os
import sys


# Remove this script's directory from sys.path to prevent self-import
# (this file is named pygal.py, which shadows the installed pygal package)
_here = os.path.dirname(os.path.abspath(__file__))
while _here in sys.path:
    sys.path.remove(_here)
del _here

import cairosvg
import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Constants
LOW_MAX = 400  # flows below this many thousand people are the low tier
HIGH_MIN = 600  # flows from this many thousand people are the high tier
ARC_SEGMENTS = 20  # straight pieces per Bezier arc

# Columns: set these to your table's column names
ORIGIN_LAT = "origin_lat"  # role: origin_lat
ORIGIN_LON = "origin_lon"  # role: origin_lon
DEST_LAT = "dest_lat"  # role: dest_lat
DEST_LON = "dest_lon"  # role: dest_lon
FLOW = "Migrants (thousand people)"  # role: flow
ORIGIN_NAME = "origin_name"  # role: origin_name
DEST_NAME = "dest_name"  # role: dest_name

# Data: replace this block with your own table, for example df = pd.read_csv("flows.csv")
capitals = {
    "Germany": (52.52, 13.40),
    "France": (48.86, 2.35),
    "United Kingdom": (51.51, -0.13),
    "Spain": (40.42, -3.70),
    "Italy": (41.90, 12.50),
    "Poland": (52.23, 21.01),
    "Romania": (44.43, 26.10),
    "Netherlands": (52.37, 4.90),
    "Portugal": (38.72, -9.14),
    "Greece": (37.98, 23.73),
    "Ireland": (53.35, -6.26),
}

flow_pairs = [
    ("Romania", "Italy", 850),
    ("Poland", "Germany", 810),
    ("Romania", "Germany", 740),
    ("Romania", "Spain", 640),
    ("Portugal", "France", 610),
    ("Poland", "United Kingdom", 520),
    ("Poland", "Ireland", 270),
    ("Poland", "Netherlands", 330),
    ("Italy", "Germany", 460),
    ("Italy", "United Kingdom", 430),
    ("Spain", "France", 410),
    ("Spain", "Germany", 300),
    ("Portugal", "United Kingdom", 350),
    ("Greece", "Germany", 380),
    ("Greece", "United Kingdom", 240),
    ("Ireland", "United Kingdom", 420),
    ("Romania", "France", 290),
    ("Italy", "France", 360),
    ("Netherlands", "Germany", 220),
    ("Portugal", "Spain", 250),
]

df = pd.DataFrame(
    {
        ORIGIN_LAT: [capitals[o][0] for o, _, _ in flow_pairs],
        ORIGIN_LON: [capitals[o][1] for o, _, _ in flow_pairs],
        DEST_LAT: [capitals[d][0] for _, d, _ in flow_pairs],
        DEST_LON: [capitals[d][1] for _, d, _ in flow_pairs],
        FLOW: [f for _, _, f in flow_pairs],
        ORIGIN_NAME: [o for o, _, _ in flow_pairs],
        DEST_NAME: [d for _, d, _ in flow_pairs],
    }
)

# Plot
lat_min = min(df[ORIGIN_LAT].min(), df[DEST_LAT].min()) - 3
lat_max = max(df[ORIGIN_LAT].max(), df[DEST_LAT].max()) + 3
lon_min = min(df[ORIGIN_LON].min(), df[DEST_LON].min()) - 3
lon_max = max(df[ORIGIN_LON].max(), df[DEST_LON].max()) + 2

coastlines = [
    # Iberian Peninsula
    [
        (-9.5, 37.0),
        (-9.2, 37.5),
        (-9.0, 38.0),
        (-9.0, 38.7),
        (-8.8, 39.5),
        (-8.5, 40.5),
        (-8.5, 42.0),
        (-5.0, 43.5),
        (-2.0, 43.5),
        (0.5, 43.0),
        (3.0, 42.5),
        (1.5, 41.5),
        (0.5, 40.5),
        (0.0, 39.5),
        (-0.5, 38.0),
        (-1.5, 37.5),
        (-5.0, 36.0),
        (-6.0, 36.2),
        (-9.5, 37.0),
    ],
    # Southern France + Italian Riviera + Adriatic
    [
        (3.0, 42.5),
        (4.5, 43.2),
        (6.0, 43.0),
        (7.5, 43.5),
        (9.5, 44.0),
        (10.5, 44.5),
        (12.0, 44.8),
        (13.5, 45.5),
        (13.0, 45.0),
        (12.5, 44.0),
        (14.0, 42.5),
        (15.5, 41.5),
        (16.0, 41.0),
    ],
    # Italian peninsula boot
    [
        (9.5, 44.0),
        (10.0, 43.5),
        (11.0, 42.0),
        (12.5, 41.0),
        (14.0, 40.0),
        (15.5, 39.5),
        (16.5, 38.5),
        (18.0, 40.0),
        (17.5, 40.5),
        (16.0, 41.0),
    ],
    # Greece and Aegean coast
    [
        (20.0, 40.0),
        (21.0, 39.0),
        (22.0, 37.5),
        (23.0, 38.0),
        (24.0, 38.5),
        (25.5, 39.0),
        (26.0, 40.0),
        (25.5, 41.0),
        (24.0, 41.5),
        (22.0, 41.0),
        (20.0, 40.0),
    ],
    # Northern European coast (France to Poland)
    [
        (-6.0, 50.0),
        (0.0, 50.5),
        (2.0, 51.0),
        (4.0, 52.0),
        (5.0, 53.0),
        (6.5, 53.5),
        (8.0, 54.0),
        (9.0, 54.5),
        (10.0, 55.0),
        (11.0, 55.5),
        (12.0, 56.0),
        (14.0, 55.5),
        (16.0, 55.5),
        (18.0, 55.0),
        (20.0, 54.5),
    ],
    # Great Britain
    [
        (-6.0, 50.0),
        (-5.0, 50.0),
        (-3.5, 50.5),
        (-2.0, 51.0),
        (-0.5, 51.5),
        (1.5, 51.5),
        (1.0, 52.5),
        (0.0, 53.0),
        (-2.0, 54.0),
        (-3.0, 54.0),
        (-4.0, 54.5),
        (-5.0, 55.0),
        (-5.5, 56.0),
        (-6.0, 56.0),
        (-5.5, 57.0),
        (-5.0, 58.0),
    ],
    # Ireland
    [
        (-10.0, 51.5),
        (-8.5, 51.5),
        (-6.0, 51.5),
        (-5.8, 52.5),
        (-6.0, 53.5),
        (-7.0, 54.5),
        (-8.0, 55.5),
        (-9.5, 55.0),
        (-10.0, 53.5),
        (-10.0, 51.5),
    ],
]


def make_bezier_curves(flows):
    curves = []
    for row in flows.itertuples(index=False):
        o_lat, o_lon, d_lat, d_lon = row[0], row[1], row[2], row[3]
        magnitude = row[4]
        label = f"{row[5]} → {row[6]}: {magnitude:,} thousand people"
        dx, dy = d_lon - o_lon, d_lat - o_lat
        length = np.hypot(dx, dy)
        offset = min(length * 0.2, 2.5) / length
        ctrl_lon = (o_lon + d_lon) / 2 - dy * offset
        ctrl_lat = (o_lat + d_lat) / 2 + dx * offset
        for i in range(ARC_SEGMENTS + 1):
            t = i / ARC_SEGMENTS
            lon = (1 - t) ** 2 * o_lon + 2 * (1 - t) * t * ctrl_lon + t**2 * d_lon
            lat = (1 - t) ** 2 * o_lat + 2 * (1 - t) * t * ctrl_lat + t**2 * d_lat
            curves.append({"value": (lon, lat), "label": label})
        curves.append((None, None))
    return curves


# Style — INK_SOFT for coastlines (neutral), then Okabe-Ito for data series
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(INK_SOFT,) + IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    tooltip_font_size=36,
    font_family="sans-serif",
    stroke_width=2.5,
)

# Chart
chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="flowmap-origin-destination · python · pygal · anyplot.ai",
    x_title="Longitude (°)",
    y_title="Latitude (°)",
    show_legend=True,
    legend_at_bottom=False,
    legend_box_size=40,
    truncate_legend=-1,
    margin=80,
    margin_top=160,
    margin_bottom=120,
    margin_right=200,
    margin_left=180,
    range=(lat_min, lat_max),
    xrange=(lon_min, lon_max),
    show_dots=True,
    stroke=True,
    allow_interruptions=True,
    dots_size=16,
    tooltip_border_radius=10,
    show_x_guides=True,
    show_y_guides=True,
)

# Coastlines — drawn first (lowest z-order)
coastline_points = []
for segment in coastlines:
    for lon, lat in segment:
        coastline_points.append({"value": (lon, lat), "label": "Coastline"})
    coastline_points.append((None, None))

chart.add("Coastlines", coastline_points, stroke=True, show_dots=False, stroke_style={"width": 2})

# Tiers by magnitude: thin arcs first, so the thickest are drawn last (on top)
arc_cols = [ORIGIN_LAT, ORIGIN_LON, DEST_LAT, DEST_LON, FLOW, ORIGIN_NAME, DEST_NAME]
flows_sorted = df.sort_values(FLOW)[arc_cols]
tiers = [
    (f"Low (under {LOW_MAX:,} thousand)", flows_sorted[flows_sorted[FLOW] < LOW_MAX], 6),
    (
        f"Medium ({LOW_MAX:,}–{HIGH_MIN - 1:,} thousand)",
        flows_sorted[(flows_sorted[FLOW] >= LOW_MAX) & (flows_sorted[FLOW] < HIGH_MIN)],
        14,
    ),
    (f"High ({HIGH_MIN:,}+ thousand)", flows_sorted[flows_sorted[FLOW] >= HIGH_MIN], 28),
]
for name, tier, width in tiers:
    chart.add(
        name, make_bezier_curves(tier), stroke=True, show_dots=False, stroke_style={"width": width, "linecap": "round"}
    )

# Countries — drawn last (on top of all arcs), one dot per capital
places = pd.concat(
    [
        df[[ORIGIN_NAME, ORIGIN_LON, ORIGIN_LAT]].set_axis(["name", "lon", "lat"], axis=1),
        df[[DEST_NAME, DEST_LON, DEST_LAT]].set_axis(["name", "lon", "lat"], axis=1),
    ]
).drop_duplicates("name")
city_points = [{"value": (p.lon, p.lat), "label": p.name} for p in places.itertuples()]

chart.add("Countries (capital)", city_points, dots_size=18, stroke=False)

# Save — inject arc transparency via CSS (pygal stroke_style doesn't expose opacity)
svg_bytes = chart.render()
svg_str = svg_bytes.decode("utf-8")
# pygal's `.reactive` rule sets every path to 2.5 px, so the tier widths need !important
arc_opacity = "".join(
    f".serie-{i}{{opacity:0.6;}}.serie-{i} .reactive{{stroke-width:{width}px !important;}}"
    for i, (_, _, width) in enumerate(tiers, start=1)
)
svg_str = svg_str.replace("</style>", arc_opacity + "</style>", 1)
svg_out = svg_str.encode("utf-8")
cairosvg.svg2png(bytestring=svg_out, write_to=f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(svg_out)
