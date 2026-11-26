"""anyplot.ai
map-route-path: Route Path Map
Library: pygal 3.1.3 | Python 3.14.10
Quality: 76/100 | Updated: 2026-11-26
"""

import math
import os
from itertools import pairwise

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BASEMAP = "#B9B7AC" if THEME == "light" else "#55544D"  # quiet context strokes under the route

# Imprint palette positions used here: green for the start, purple for the finish
IMPRINT_GREEN = "#009E73"
IMPRINT_PURPLE = "#C475FD"

# Imprint sequential ramp for marks (colored lines on the page), stops per theme
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
N_SEGMENTS = 5  # the route is split into this many equal time segments
RAMP_FROM = 0.25  # the first segment starts off the START green so the marker stays distinct
COS_LAT = 0.757  # cos(40.77 deg): one degree of longitude is this much shorter than one of latitude
PLOT_ASPECT = 1.07  # plot-area width / height on the square canvas, used to fit the view
TICK_STEP = 0.004  # degrees between axis ticks

# Columns: set these to your table's column names
LON = "Longitude (degrees)"  # role: lon
LAT = "Latitude (degrees)"  # role: lat
MINUTES = "Elapsed time (min)"  # role: timestamp

# Data: replace this block with your own table, for example df = pd.read_csv("track.csv")
# Simulated hiking trail GPS track (Central Park loop, NYC): ~3.6 km in 45 minutes, 100 waypoints
np.random.seed(42)
n_points = 100
t = np.linspace(0, 2 * np.pi, n_points)
base_lon = -73.97 + 0.0038 * np.sin(t)
base_lat = 40.77 + 0.0063 * np.cos(t) * (1 + 0.3 * np.sin(2 * t))
df = pd.DataFrame(
    {
        LON: base_lon + np.random.normal(0, 0.00013, n_points),
        LAT: base_lat + np.random.normal(0, 0.00008, n_points),
        MINUTES: np.linspace(0, 45, n_points),
    }
)

# Plot: reads only df and the constants above
lon = df[LON].to_numpy()
lat = df[LAT].to_numpy()
minutes = df[MINUTES].to_numpy()
n_rows = len(df)
stamps = [f"{int(m):02d}min" for m in minutes]

# View fitted to the route, drawn at true ground proportions: x spans 1/COS_LAT more
# degrees than y per screen pixel, so one kilometre looks the same in both directions
lon_c, lat_c = (lon.min() + lon.max()) / 2, (lat.min() + lat.max()) / 2
y_half = (lat.max() - lat.min()) / 2 * 1.35
x_half = y_half * PLOT_ASPECT / COS_LAT
x_lo, x_hi = lon_c - x_half, lon_c + x_half
y_lo, y_hi = lat_c - y_half, lat_c + y_half

# Quiet basemap: park boundary with a pond, and the street grid around the park
park_hx, park_hy = (lon.max() - lon.min()) / 2 * 1.3, (lat.max() - lat.min()) / 2 * 1.12
park = [
    (lon_c - park_hx, lat_c - park_hy),
    (lon_c + park_hx, lat_c - park_hy),
    (lon_c + park_hx, lat_c + park_hy),
    (lon_c - park_hx, lat_c + park_hy),
    (lon_c - park_hx, lat_c - park_hy),
]
angles = np.linspace(0, 2 * np.pi, 49)
pond = [(lon_c + 0.2 * park_hx * math.cos(a), lat_c + 0.28 * park_hy * math.sin(a)) for a in angles]
# pygal joins gaps in a series, so the street grid is one polyline that retraces its own strokes
st_lo, st_hi = lat_c - park_hy * 1.1, lat_c + park_hy * 1.1  # cross streets
av_lo, av_hi = lon_c - park_hx * 1.15, lon_c + park_hx * 1.15  # avenues
streets = [
    (x_lo, st_lo),
    (av_lo, st_lo),
    (av_lo, y_lo),
    (av_lo, y_hi),
    (av_lo, st_hi),
    (x_lo, st_hi),
    (x_hi, st_hi),
    (av_hi, st_hi),
    (av_hi, y_hi),
    (av_hi, y_lo),
    (av_hi, st_lo),
    (x_hi, st_lo),
]

segment_colors = [ramp_color(SEQ_MARKS, RAMP_FROM + (1 - RAMP_FROM) * i / (N_SEGMENTS - 1)) for i in range(N_SEGMENTS)]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=BASEMAP,
    major_guide_stroke_color=BASEMAP,
    colors=tuple([BASEMAP] * 3 + segment_colors + [IMPRINT_GREEN, IMPRINT_PURPLE]),
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=6,
)

# XY chart maps longitude/latitude as Cartesian coordinates; tick labels use three
# decimals, which is about 100 m and enough for a map reader
chart = pygal.XY(
    width=2400,
    height=2400,
    style=custom_style,
    title="map-route-path · python · pygal · anyplot.ai",
    x_title=LON,
    y_title=LAT,
    show_dots=False,
    stroke_style={"width": 7, "linecap": "round", "linejoin": "round"},
    show_x_guides=False,
    show_y_guides=False,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    legend_box_size=32,
    truncate_legend=-1,
    truncate_label=-1,
    x_label_rotation=45,
    xrange=(x_lo, x_hi),
    range=(y_lo, y_hi),
    x_value_formatter=lambda v: f"{v:.3f}",
    value_formatter=lambda v: f"Lon {v[0]:.4f}°, Lat {v[1]:.4f}°" if isinstance(v, (tuple, list)) else str(v),
)
chart.x_labels = np.arange(math.ceil(x_lo / TICK_STEP) * TICK_STEP, x_hi, TICK_STEP).round(3).tolist()
chart.y_labels = np.arange(math.ceil(y_lo / TICK_STEP) * TICK_STEP, y_hi, TICK_STEP).round(3).tolist()

# Basemap first, so the route is drawn on top of it
chart.add("Park", park, stroke_style={"width": 4, "linecap": "round"})
chart.add("Pond", pond, stroke_style={"width": 4, "linecap": "round"})
chart.add("Streets", streets, stroke_style={"width": 3, "linecap": "round"})

# Route segments: one step of the Imprint ramp per time segment, in time order
bounds = np.linspace(0, n_rows - 1, N_SEGMENTS + 1).round().astype(int)
for i in range(N_SEGMENTS):
    start_idx, end_idx = bounds[i], bounds[i + 1]
    segment_data = [
        {"value": (float(lon[j]), float(lat[j])), "label": f"Waypoint {j + 1} at {stamps[j]}"}
        for j in range(start_idx, end_idx + 1)
    ]
    chart.add(f"{minutes[start_idx]:.0f}–{minutes[end_idx]:.0f} min", segment_data)

# START marker: brand green, the larger dot, so the FINISH dot drawn on top stays visible
# (a closed loop ends where it began)
chart.add(
    "START",
    [{"value": (float(lon[0]), float(lat[0])), "label": f"Trail head — {stamps[0]}"}],
    dots_size=30,
    stroke=False,
    show_dots=True,
)

# FINISH marker: a smaller dot in the second palette color
chart.add(
    "FINISH",
    [{"value": (float(lon[-1]), float(lat[-1])), "label": f"Trail end — {stamps[-1]}"}],
    dots_size=13,
    stroke=False,
    show_dots=True,
)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
