"""anyplot.ai
flowmap-origin-destination: Origin-Destination Flow Map
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-20
"""

import math
import os
import sys
import time
from itertools import pairwise
from pathlib import Path


# This file is named bokeh.py — remove its directory from sys.path so that
# `import bokeh` resolves to the installed package, not this file itself.
sys.path = [p for p in sys.path if Path(p).resolve() != Path(__file__).resolve().parent]

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColorBar, ColumnDataSource, HoverTool, LinearColorMapper, WMTSTileSource
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: position 1 is the brand green used for the port markers
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential ramp for marks (colored lines on the page), as (position, hex) stops
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


# LinearColorMapper takes evenly spaced colors, so sample the stops at 256 even steps
ANYPLOT_SEQ256 = [ramp_color(SEQ_MARKS, k / 255) for k in range(256)]

# Constants
CURVE_BOW = 0.2  # arc height as a share of the origin-destination distance
LINE_WIDTH_RANGE = (3, 17)  # px, thinnest to thickest arc

# Columns: set these to your table's column names
ORIGIN = "Origin"  # role: origin_name
DEST = "Destination"  # role: dest_name
ORIGIN_LAT = "Origin latitude"  # role: origin_lat
ORIGIN_LON = "Origin longitude"  # role: origin_lon
DEST_LAT = "Destination latitude"  # role: dest_lat
DEST_LON = "Destination longitude"  # role: dest_lon
FLOW = "Volume (TEU)"  # role: flow

# Data: replace this block with your own table, for example df = pd.read_csv("flows.csv")
ports = {
    "Shanghai": (31.2304, 121.4737),
    "Singapore": (1.3521, 103.8198),
    "Rotterdam": (51.9225, 4.4792),
    "Los Angeles": (33.7490, -118.2437),
    "Dubai": (25.2048, 55.2708),
    "Hong Kong": (22.3193, 114.1694),
    "Hamburg": (53.5511, 9.9937),
    "New York": (40.7128, -74.0060),
    "Tokyo": (35.6762, 139.6503),
    "Sydney": (-33.8688, 151.2093),
}
flow_pairs = [
    ("Shanghai", "Los Angeles", 850),
    ("Shanghai", "Rotterdam", 720),
    ("Singapore", "Rotterdam", 580),
    ("Singapore", "Dubai", 490),
    ("Hong Kong", "Los Angeles", 620),
    ("Hong Kong", "Hamburg", 410),
    ("Rotterdam", "New York", 530),
    ("Dubai", "Singapore", 380),
    ("Tokyo", "Los Angeles", 560),
    ("Tokyo", "Shanghai", 470),
    ("Shanghai", "Singapore", 650),
    ("Los Angeles", "New York", 420),
    ("Sydney", "Singapore", 340),
    ("Sydney", "Shanghai", 290),
    ("Hamburg", "New York", 310),
    ("Rotterdam", "Dubai", 280),
    ("New York", "Rotterdam", 390),
    ("Dubai", "Hamburg", 260),
]
df = pd.DataFrame(
    {
        ORIGIN: [o for o, _, _ in flow_pairs],
        DEST: [d for _, d, _ in flow_pairs],
        ORIGIN_LAT: [ports[o][0] for o, _, _ in flow_pairs],
        ORIGIN_LON: [ports[o][1] for o, _, _ in flow_pairs],
        DEST_LAT: [ports[d][0] for _, d, _ in flow_pairs],
        DEST_LON: [ports[d][1] for _, d, _ in flow_pairs],
        FLOW: [f for _, _, f in flow_pairs],
    }
)


# Plot: reads only df and the constants above
def to_mercator(lon, lat):
    """Longitude/latitude in degrees to Web Mercator (EPSG:3857) meters."""
    k = 6378137
    return np.asarray(lon) * (k * np.pi / 180.0), np.log(np.tan((90 + np.asarray(lat)) * np.pi / 360.0)) * k


x0, y0 = to_mercator(df[ORIGIN_LON], df[ORIGIN_LAT])
x1, y1 = to_mercator(df[DEST_LON], df[DEST_LAT])

# Flow encoding: line width and color both follow the volume
flow_low, flow_high = df[FLOW].min(), df[FLOW].max()
share = (df[FLOW] - flow_low) / ((flow_high - flow_low) or 1)
line_width = LINE_WIDTH_RANGE[0] + share * (LINE_WIDTH_RANGE[1] - LINE_WIDTH_RANGE[0])
color_mapper = LinearColorMapper(palette=ANYPLOT_SEQ256, low=flow_low, high=flow_high)

# Quadratic Bezier arcs: the control point sits above the midpoint, ends stay on the ports
t = np.linspace(0, 1, 50)
arc_xs, arc_ys = [], []
for ax_, ay_, bx_, by_ in zip(x0, y0, x1, y1, strict=True):
    ctrl_y = (ay_ + by_) / 2 + math.hypot(bx_ - ax_, by_ - ay_) * CURVE_BOW
    arc_xs.append((1 - t) ** 2 * ax_ + 2 * (1 - t) * t * (ax_ + bx_) / 2 + t**2 * bx_)
    arc_ys.append((1 - t) ** 2 * ay_ + 2 * (1 - t) * t * ctrl_y + t**2 * by_)

arc_source = ColumnDataSource(
    {"xs": arc_xs, "ys": arc_ys, ORIGIN: df[ORIGIN], DEST: df[DEST], FLOW: df[FLOW], "line_width": line_width}
)

# One marker per distinct port, taken from the flow endpoints
ends = pd.concat(
    [
        df[[ORIGIN, ORIGIN_LAT, ORIGIN_LON]].set_axis(["name", "lat", "lon"], axis=1),
        df[[DEST, DEST_LAT, DEST_LON]].set_axis(["name", "lat", "lon"], axis=1),
    ]
).drop_duplicates("name")
port_x, port_y = to_mercator(ends["lon"], ends["lat"])
port_source = ColumnDataSource({"x": port_x, "y": port_y, "name": ends["name"], "lat": ends["lat"], "lon": ends["lon"]})

# Map extent from the data: ports plus the arc bows, padded
all_x = np.concatenate([np.concatenate(arc_xs), port_x])
all_y = np.concatenate([np.concatenate(arc_ys), port_y])
pad_x = (all_x.max() - all_x.min()) * 0.04
pad_y = (all_y.max() - all_y.min()) * 0.08

# Theme-adaptive basemap tiles
tile_style = "World_Light_Gray_Base" if THEME == "light" else "World_Dark_Gray_Base"
tile_url = f"https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/{tile_style}/MapServer/tile/{{Z}}/{{Y}}/{{X}}"

p = figure(
    width=3200,
    height=1800,
    title="flowmap-origin-destination · python · bokeh · anyplot.ai",
    x_axis_type="mercator",
    y_axis_type="mercator",
    x_range=(all_x.min() - pad_x, all_x.max() + pad_x),
    y_range=(all_y.min() - pad_y, all_y.max() + pad_y),
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)
p.add_tile(WMTSTileSource(url=tile_url))

# Flow arcs: one renderer, so every arc has its own hover tooltip
arcs = p.multi_line(
    xs="xs",
    ys="ys",
    source=arc_source,
    line_width="line_width",
    line_color={"field": FLOW, "transform": color_mapper},
    line_alpha=0.65,
    line_cap="round",
)

# Port markers in the brand green, outlined so they stand out on both basemaps
ports_r = p.scatter(
    x="x",
    y="y",
    source=port_source,
    size=26,
    color=IMPRINT_PALETTE[0],
    line_color=PAGE_BG,
    line_width=3,
    legend_label="Ports",
)

p.add_tools(
    HoverTool(
        renderers=[arcs], tooltips=[("Route", f"@{{{ORIGIN}}} → @{{{DEST}}}"), ("Volume", f"@{{{FLOW}}}{{,}} TEU")]
    ),
    HoverTool(renderers=[ports_r], tooltips=[("Port", "@name"), ("Lat", "@lat{0.00}°"), ("Lon", "@lon{0.00}°")]),
)

# Style
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.title.text_font_size = "50pt"
p.title.text_color = INK

p.xaxis.axis_label = "Longitude"
p.yaxis.axis_label = "Latitude"
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# The basemap already gives the geographic reference, so no grid lines
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None

p.legend.location = "top_left"
p.legend.label_text_font_size = "34pt"
p.legend.glyph_height = 40
p.legend.glyph_width = 40
p.legend.label_standoff = 16
p.legend.padding = 20
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT

# ColorBar: explains the arc color as shipping volume
color_bar = ColorBar(
    color_mapper=color_mapper,
    title=FLOW,
    title_text_font_size="34pt",
    title_text_color=INK,
    major_label_text_font_size="30pt",
    major_label_text_color=INK_SOFT,
    label_standoff=20,
    width=40,
    padding=20,
    background_fill_color=PAGE_BG,
    bar_line_color=INK_SOFT,
    border_line_color=INK_SOFT,
)
p.add_layout(color_bar, "right")

# Save HTML and screenshot it with headless Chrome (export_png needs a broken chromedriver)
output_file(f"plot-{THEME}.html")
save(p)

W, H = 3200, 1800
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.execute_script(
    "document.documentElement.style.background = arguments[0]; document.body.style.background = arguments[0];", PAGE_BG
)
time.sleep(3)  # let bokeh's JS render the canvas
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
