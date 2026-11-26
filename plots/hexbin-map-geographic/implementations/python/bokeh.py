"""anyplot.ai
hexbin-map-geographic: Hexagonal Binning Map
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-27
"""

import os
import sys


# Remove the script's own directory from sys.path to prevent self-import collision
# (this file is named bokeh.py, which would otherwise shadow the installed bokeh package)
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if p != "" and os.path.abspath(p) != _script_dir]

import time
from itertools import pairwise
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColorBar, ColumnDataSource, HoverTool, LinearColorMapper, WMTSTileSource
from bokeh.plotting import figure
from bokeh.transform import transform
from bokeh.util.hex import hexbin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"


# Imprint sequential ramp stops (fields: colored cells fill the plot)
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.368, "#009E73"), (0.582, "#4467A3"), (1.0, "#002850")]
    if THEME == "light"
    else [(0.0, "#00573D"), (0.467, "#009E73"), (1.0, "#CDD9FF")]
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
HEX_SIZE = 650  # hexagon size in Web Mercator meters: detail against aggregation
COUNT_LABEL = "Pickup Count"  # the statistic drawn per cell

# Columns: set these to your table's column names
LON = "Longitude"  # role: lon
LAT = "Latitude"  # role: lat

# Data: replace this block with your own table, for example df = pd.read_csv("pickups.csv")
# Simulated NYC taxi pickup GPS coordinates around five hot spots
np.random.seed(42)
n_points = 8000

cluster_centers = [
    (-73.984, 40.754),  # Times Square / Midtown
    (-73.965, 40.782),  # Upper West Side
    (-74.005, 40.724),  # SoHo / TriBeCa
    (-73.991, 40.735),  # Greenwich Village
    (-73.951, 40.773),  # Carnegie Hill / Museum Mile
]

lon_list = []
lat_list = []
for cx, cy in cluster_centers:
    n = n_points // len(cluster_centers) + np.random.randint(-300, 300)
    lon_list.extend(np.random.normal(cx, 0.018, n))
    lat_list.extend(np.random.normal(cy, 0.014, n))

df = pd.DataFrame({LON: lon_list, LAT: lat_list})

# Plot
# Web Mercator projection (EPSG:3857)
K = 6378137.0
merc_x = df[LON].to_numpy() * (K * np.pi / 180.0)
merc_y = np.log(np.tan((90.0 + df[LAT].to_numpy()) * np.pi / 360.0)) * K

# Hexagonal binning
bins = hexbin(merc_x, merc_y, HEX_SIZE)
source = ColumnDataSource(data={"q": np.array(bins.q), "r": np.array(bins.r), "counts": np.array(bins.counts)})

# Imprint sequential ramp (fields stops: colored cells fill the plot), sampled at 256 even steps
imprint_seq = [ramp_color(SEQ_FIELDS, k / 255) for k in range(256)]
mapper = LinearColorMapper(palette=imprint_seq, low=float(bins.counts.min()), high=float(bins.counts.max()))

# Map viewport with padding of a few hexagons
pad = 6 * HEX_SIZE
x_range = (float(merc_x.min()) - pad, float(merc_x.max()) + pad)
y_range = (float(merc_y.min()) - pad, float(merc_y.max()) + pad)

# Title
title = "hexbin-map-geographic · python · bokeh · anyplot.ai"

# Tile layer for geographic context
tile_provider = WMTSTileSource(
    url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/"
    + ("World_Dark_Gray_Base" if THEME == "dark" else "World_Light_Gray_Base")
    + "/MapServer/tile/{Z}/{Y}/{X}",
    attribution="Tiles © Esri — Esri, HERE, Garmin, FAO, NOAA, USGS",
)

# Figure — 3200×1800 landscape, toolbar disabled for exact PNG dimensions
p = figure(
    width=3200,
    height=1800,
    title=title,
    x_axis_label=LON,
    y_axis_label=LAT,
    x_axis_type="mercator",
    y_axis_type="mercator",
    x_range=x_range,
    y_range=y_range,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=200,
    min_border_top=110,
    min_border_right=80,
)

# Geographic base layer
p.add_tile(tile_provider)

# Hex tiles
p.hex_tile(
    q="q", r="r", size=HEX_SIZE, fill_color=transform("counts", mapper), line_color=None, alpha=0.78, source=source
)

# Hover tooltip
hover = HoverTool(tooltips=[("Taxi Pickups", "@counts"), ("Hex Cell", "(@q, @r)")], mode="mouse")
p.add_tools(hover)

# Color bar
color_bar = ColorBar(
    color_mapper=mapper,
    location=(0, 0),
    title=COUNT_LABEL,
    title_text_font_size="34pt",
    title_text_font_style="bold",
    title_text_color=INK,
    major_label_text_font_size="28pt",
    major_label_text_color=INK_SOFT,
    width=60,
    padding=30,
    background_fill_color=PAGE_BG,
    margin=40,
)
p.add_layout(color_bar, "right")

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.title.text_font_size = "50pt"
p.title.text_color = INK
p.title.text_font_style = "bold"

p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.12
p.ygrid.grid_line_alpha = 0.12

# Save interactive HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome — Selenium Manager resolves the driver automatically
W, H = 3200, 1800
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H}",
    "--hide-scrollbars",
    "--force-device-scale-factor=1",
):
    opts.add_argument(arg)

driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, H)
# Override viewport to exact pixel dimensions (bypasses browser-chrome height overhead)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_script(
    "document.documentElement.style.background = arguments[0]; document.body.style.background = arguments[0];", PAGE_BG
)
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
