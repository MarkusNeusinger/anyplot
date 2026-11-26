"""anyplot.ai
map-tile-background: Map with Tile Background
Library: bokeh 3.10.2 | Python 3.14.10
Quality: pending | Updated: 2026-11-26
"""

import os
import sys


# bokeh.py shadows the installed bokeh package — remove script dir from sys.path
_here = os.path.abspath(os.path.dirname(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _here]

import time
from itertools import pairwise
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColorBar, ColumnDataSource, HoverTool, Label, LinearColorMapper, Range1d, WMTSTileSource
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential ramp for colored marks on the page, as (position, hex) stops
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


# Columns: set these to your table's column names
LABEL = "City"  # role: label
LON = "Longitude (°)"  # role: lon
LAT = "Latitude (°)"  # role: lat
VALUE = "Visitors (M/year)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("places.csv")
df = pd.DataFrame(
    {
        LABEL: [
            "Paris",
            "London",
            "Rome",
            "Barcelona",
            "Amsterdam",
            "Berlin",
            "Prague",
            "Vienna",
            "Madrid",
            "Lisbon",
            "Brussels",
            "Dublin",
            "Copenhagen",
            "Stockholm",
            "Warsaw",
        ],
        LON: [
            2.3522,
            -0.1276,
            12.4964,
            2.1734,
            4.9041,
            13.4050,
            14.4378,
            16.3738,
            -3.7038,
            -9.1393,
            4.3517,
            -6.2603,
            12.5683,
            18.0686,
            21.0122,
        ],
        LAT: [
            48.8566,
            51.5074,
            41.9028,
            41.3851,
            52.3676,
            52.5200,
            50.0755,
            48.2082,
            40.4168,
            38.7223,
            50.8503,
            53.3498,
            55.6761,
            59.3293,
            52.2297,
        ],
        VALUE: [19.1, 21.0, 10.1, 12.0, 8.0, 6.1, 8.0, 7.7, 7.5, 4.5, 4.0, 5.5, 3.5, 4.0, 3.0],
    }
)

# Plot
# Web Mercator projection (required for tile maps)
k = 6378137
df["x"] = df[LON] * (k * np.pi / 180.0)
df["y"] = np.log(np.tan((90 + df[LAT]) * np.pi / 360.0)) * k
df["size"] = df[VALUE] * 2.0 + 20

source = ColumnDataSource(df)

ANYPLOT_SEQ256 = [ramp_color(SEQ_MARKS, i / 255) for i in range(256)]
color_mapper = LinearColorMapper(palette=ANYPLOT_SEQ256, low=df[VALUE].min(), high=df[VALUE].max())

# Esri gray canvas tiles: a light and a dark basemap that follow the page theme
ESRI_CANVAS = "World_Light_Gray_Base" if THEME == "light" else "World_Dark_Gray_Base"
tile_provider = WMTSTileSource(
    url=f"https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/{ESRI_CANVAS}/MapServer/tile/{{Z}}/{{Y}}/{{X}}",
    attribution="",
    max_zoom=16,
)

# View fitted to the data bounds with a margin
pad_x = (df["x"].max() - df["x"].min()) * 0.12
pad_y = (df["y"].max() - df["y"].min()) * 0.12
x_range = Range1d(df["x"].min() - pad_x, df["x"].max() + pad_x)
y_range = Range1d(df["y"].min() - pad_y, df["y"].max() + pad_y)

title = "map-tile-background · python · bokeh · anyplot.ai"
n = len(title)
title_pt = max(34, round(50 * 67 / n)) if n > 67 else 50

p = figure(
    width=2400,
    height=2400,
    x_range=x_range,
    y_range=y_range,
    x_axis_type="mercator",
    y_axis_type="mercator",
    title=title,
    tools="pan,wheel_zoom,box_zoom,reset",
    active_scroll="wheel_zoom",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=250,
)

p.add_tile(tile_provider)

p.scatter(
    "x",
    "y",
    source=source,
    size="size",
    fill_color={"field": VALUE, "transform": color_mapper},
    fill_alpha=0.85,
    line_color="white",
    line_width=2,
)

color_bar = ColorBar(
    color_mapper=color_mapper,
    title=VALUE,
    title_text_font_size="34pt",
    title_text_color=INK,
    major_label_text_font_size="34pt",
    major_label_text_color=INK_SOFT,
    background_fill_color=ELEVATED_BG,
    width=80,
)
p.add_layout(color_bar, "right")

# Readable provider credit in the bottom-right corner of the map
credit = Label(
    x=x_range.end,
    y=y_range.start,
    text_align="right",
    text="Tiles © Esri — Esri, DeLorme, NAVTEQ",
    text_font_size="22pt",
    text_color=INK,
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.85,
    text_baseline="bottom",
)
p.add_layout(credit, "center")

hover = HoverTool(
    tooltips=[
        (LABEL, f"@{{{LABEL}}}"),
        (VALUE, f"@{{{VALUE}}}{{0.0}}"),
        ("Location", f"@{{{LAT}}}{{0.00}}, @{{{LON}}}{{0.00}}"),
    ]
)
p.add_tools(hover)

p.title.text_font_size = f"{title_pt}pt"
p.title.align = "center"
p.title.text_color = INK

p.xaxis.axis_label = LON
p.yaxis.axis_label = LAT
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

output_file(f"plot-{THEME}.html")
save(p)

W, H = 2400, 2400
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
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
