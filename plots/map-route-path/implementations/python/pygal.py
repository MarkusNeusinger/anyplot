"""anyplot.ai
map-route-path: Route Path Map
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-21
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_SEGMENTS = 5  # the route is split into this many equal time segments

# Columns: set these to your table's column names
LON = "Longitude (degrees)"  # role: lon
LAT = "Latitude (degrees)"  # role: lat
MINUTES = "Elapsed time (min)"  # role: timestamp

# Data: replace this block with your own table, for example df = pd.read_csv("track.csv")
# Simulated hiking trail GPS track (Central Park loop, NYC), 100 waypoints over 45 minutes
np.random.seed(42)
n_points = 100
t = np.linspace(0, 2 * np.pi, n_points)
base_lon = -73.97 + 0.015 * np.sin(t)
base_lat = 40.77 + 0.025 * np.cos(t) * (1 + 0.3 * np.sin(2 * t))
df = pd.DataFrame(
    {
        LON: base_lon + np.random.normal(0, 0.0005, n_points),
        LAT: base_lat + np.random.normal(0, 0.0003, n_points),
        MINUTES: np.linspace(0, 45, n_points),
    }
)

# Plot: reads only df and the constants above
lon = df[LON].to_numpy()
lat = df[LAT].to_numpy()
minutes = df[MINUTES].to_numpy()
n_rows = len(df)
stamps = [f"{int(m):02d}min" for m in minutes]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=tuple(IMPRINT_PALETTE),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=6,
)

# XY chart maps longitude/latitude as Cartesian coordinates; tick labels are
# rounded to three decimals, which is about 100 m and enough for a map reader
chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="map-route-path · python · pygal · anyplot.ai",
    x_title=LON,
    y_title=LAT,
    show_dots=False,
    stroke_style={"width": 6, "linecap": "round", "linejoin": "round"},
    show_x_guides=True,
    show_y_guides=True,
    legend_at_bottom=True,
    legend_box_size=32,
    truncate_legend=-1,
    truncate_label=-1,
    x_label_rotation=45,
    x_value_formatter=lambda v: f"{v:.3f}",
    value_formatter=lambda v: f"Lon {v[0]:.4f}°, Lat {v[1]:.4f}°" if isinstance(v, (tuple, list)) else str(v),
)
chart.x_labels = np.linspace(np.nanmin(lon), np.nanmax(lon), 7).tolist()

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

# Route segments: one palette color per time segment; the stroke width follows a bell
# curve to suggest pace, with the peak effort in the middle of the hike
bounds = np.linspace(0, n_rows - 1, N_SEGMENTS + 1).round().astype(int)
for i in range(N_SEGMENTS):
    start_idx, end_idx = bounds[i], bounds[i + 1]
    segment_data = [
        {"value": (float(lon[j]), float(lat[j])), "label": f"Waypoint {j + 1} at {stamps[j]}"}
        for j in range(start_idx, end_idx + 1)
    ]
    width = round(5 + 3 * np.sin(np.pi * i / (N_SEGMENTS - 1)))
    chart.add(
        f"{minutes[start_idx]:.0f}–{minutes[end_idx]:.0f} min",
        segment_data,
        stroke_style={"width": width, "linecap": "round", "linejoin": "round"},
    )

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
