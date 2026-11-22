"""anyplot.ai
scatter-map-geographic: Scatter Map with Geographic Points
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-18
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColorBar, ColumnDataSource, LinearColorMapper, WMTSTileSource
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: position 1 is the brand green
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]


def lerp_hex(c0, c1, t):
    r0, g0, b0 = (int(c0[i : i + 2], 16) for i in (1, 3, 5))
    r1, g1, b1 = (int(c1[i : i + 2], 16) for i in (1, 3, 5))
    r, g, b = (round(a + (b - a) * t) for a, b in ((r0, r1), (g0, g1), (b0, b1)))
    return f"#{r:02X}{g:02X}{b:02X}"


# Imprint sequential ramp (single polarity): green to blue
IMPRINT_SEQ256 = [lerp_hex("#009E73", "#4467A3", t / 255.0) for t in range(256)]

# Columns: set these to your table's column names
CITY = "City"  # role: label
LATITUDE = "Latitude (°)"  # role: latitude
LONGITUDE = "Longitude (°)"  # role: longitude
ELEVATION = "Elevation (m)"  # role: value
POPULATION = "Population (millions)"  # role: size

# Data: replace this block with your own table, for example df = pd.read_csv("places.csv")
df = pd.DataFrame(
    {
        CITY: [
            "New York",
            "Los Angeles",
            "Chicago",
            "Houston",
            "Phoenix",
            "Philadelphia",
            "San Antonio",
            "San Diego",
            "Dallas",
            "San Jose",
            "London",
            "Paris",
            "Berlin",
            "Madrid",
            "Rome",
            "Tokyo",
            "Beijing",
            "Shanghai",
            "Mumbai",
            "Sydney",
            "São Paulo",
            "Mexico City",
            "Cairo",
            "Lagos",
            "Johannesburg",
            "Toronto",
            "Vancouver",
            "Montreal",
            "Buenos Aires",
            "Lima",
        ],
        LATITUDE: [
            40.71,
            34.05,
            41.88,
            29.76,
            33.45,
            39.95,
            29.42,
            32.72,
            32.78,
            37.34,
            51.51,
            48.86,
            52.52,
            40.42,
            41.90,
            35.68,
            39.90,
            31.23,
            19.08,
            -33.87,
            -23.55,
            19.43,
            30.04,
            6.52,
            -26.20,
            43.65,
            49.28,
            45.50,
            -34.60,
            -12.05,
        ],
        LONGITUDE: [
            -74.01,
            -118.24,
            -87.63,
            -95.37,
            -112.07,
            -75.17,
            -98.49,
            -117.16,
            -96.80,
            -121.89,
            -0.13,
            2.35,
            13.40,
            -3.70,
            12.50,
            139.69,
            116.41,
            121.47,
            72.88,
            151.21,
            -46.63,
            -99.13,
            31.24,
            3.38,
            28.04,
            -79.38,
            -123.12,
            -73.57,
            -58.38,
            -77.03,
        ],
        POPULATION: [
            8.3,
            3.9,
            2.7,
            2.3,
            1.6,
            1.6,
            1.5,
            1.4,
            1.3,
            1.0,
            8.9,
            2.2,
            3.6,
            3.2,
            2.9,
            13.9,
            21.5,
            24.9,
            20.7,
            5.3,
            12.3,
            8.9,
            10.2,
            15.4,
            5.8,
            2.9,
            0.7,
            1.8,
            3.1,
            10.5,
        ],
        ELEVATION: [
            10,
            71,
            182,
            15,
            340,
            12,
            198,
            19,
            131,
            25,
            11,
            35,
            34,
            657,
            21,
            40,
            55,
            4,
            14,
            58,
            760,
            2240,
            75,
            41,
            1753,
            76,
            0,
            47,
            25,
            154,
        ],
    }
)

# Plot: reads only df and the constants above
EARTH_RADIUS = 6378137  # Web Mercator sphere radius in meters
MARKER_MIN, MARKER_MAX = 20, 62  # marker diameter in px at the extremes of the size variable

df["x"] = np.radians(df[LONGITUDE]) * EARTH_RADIUS
df["y"] = np.log(np.tan(np.pi / 4 + np.radians(df[LATITUDE]) / 2)) * EARTH_RADIUS


def marker_size(pop):
    return MARKER_MIN + (pop - df[POPULATION].min()) / (df[POPULATION].max() - df[POPULATION].min()) * (
        MARKER_MAX - MARKER_MIN
    )


df["marker"] = marker_size(df[POPULATION])
source = ColumnDataSource(df)

# View: data extent with padding, aspect kept by Web Mercator
pad_x = (df["x"].max() - df["x"].min()) * 0.06
span_y_total = df["y"].max() - df["y"].min()
pad_y = span_y_total * 0.08

p = figure(
    width=3200,
    height=1800,
    x_axis_type="mercator",
    y_axis_type="mercator",
    x_range=(df["x"].min() - pad_x, df["x"].max() + pad_x),
    y_range=(df["y"].min() - span_y_total * 0.27, df["y"].max() + pad_y),
    match_aspect=True,
    title="scatter-map-geographic · python · bokeh · anyplot.ai",
    x_axis_label="Longitude (°)",
    y_axis_label="Latitude (°)",
    tools="pan,wheel_zoom,box_zoom,reset,hover,save",
    toolbar_location=None,
    tooltips=[
        ("City", f"@{{{CITY}}}"),
        (POPULATION, f"@{{{POPULATION}}}{{0.0}}"),
        (ELEVATION, f"@{{{ELEVATION}}}"),
        ("Coordinates", f"(@{{{LATITUDE}}}, @{{{LONGITUDE}}})"),
    ],
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Quiet gray basemap matched to the theme, so the points stay the loudest layer
basemap = "World_Light_Gray_Base" if THEME == "light" else "World_Dark_Gray_Base"
p.add_tile(
    WMTSTileSource(
        url=f"https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/{basemap}/MapServer/tile/{{Z}}/{{Y}}/{{X}}"
    )
)

color_mapper = LinearColorMapper(palette=IMPRINT_SEQ256, low=df[ELEVATION].min(), high=df[ELEVATION].max())

p.scatter(
    x="x",
    y="y",
    source=source,
    size="marker",
    fill_color={"field": ELEVATION, "transform": color_mapper},
    fill_alpha=0.78,
    line_color=INK,
    line_width=2,
    line_alpha=0.85,
)

p.add_layout(
    ColorBar(
        color_mapper=color_mapper,
        title=ELEVATION,
        title_text_font_size="30pt",
        title_text_color=INK,
        major_label_text_font_size="26pt",
        major_label_text_color=INK_SOFT,
        label_standoff=15,
        background_fill_color=PAGE_BG,
        bar_line_color=INK_SOFT,
        major_tick_line_color=INK_SOFT,
        width=50,
        height=700,
        margin=20,
    ),
    "right",
)

# Size legend: reference markers drawn at the data markers' real pixel sizes, in the empty south-Pacific band
span_y = df["y"].max() - df["y"].min()
key_left = df["x"].min() - pad_x * 0.6
key_top = df["y"].min() - span_y * 0.02
key_bottom = df["y"].min() - span_y * 0.245
key_width = (df["x"].max() - df["x"].min()) * 0.3
p.rect(
    x=key_left + key_width / 2,
    y=(key_top + key_bottom) / 2,
    width=key_width,
    height=key_top - key_bottom,
    fill_color=ELEVATED_BG,
    fill_alpha=0.92,
    line_color=INK_SOFT,
    line_width=2,
)
p.text(
    x=[key_left + key_width * 0.04],
    y=[key_top - span_y * 0.015],
    text=[POPULATION],
    text_font_size="26pt",
    text_color=INK,
    text_baseline="top",
)
for k, ref in enumerate((df[POPULATION].min(), df[POPULATION].median(), df[POPULATION].max())):
    mx = key_left + key_width * (0.1 + 0.3 * k)
    my = key_bottom + (key_top - key_bottom) * 0.32
    p.scatter(
        x=[mx], y=[my], size=float(marker_size(ref)), fill_color=INK_SOFT, fill_alpha=0.35, line_color=INK, line_width=2
    )
    p.text(
        x=[mx + key_width * 0.07],
        y=[my],
        text=[f"{ref:.1f}"],
        text_font_size="26pt",
        text_color=INK_SOFT,
        text_baseline="middle",
    )

# Chrome
p.title.text_font_size = "50pt"
p.title.text_color = INK
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
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.12
p.ygrid.grid_line_alpha = 0.12
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT
p.outline_line_width = 2

# Save interactive HTML, then screenshot it with headless Chrome
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
time.sleep(4)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
