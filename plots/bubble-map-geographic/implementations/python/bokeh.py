""" anyplot.ai
bubble-map-geographic: Bubble Map with Sized Geographic Markers
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 87/100 | Updated: 2026-11-22
"""

import sys


# Remove script directory from sys.path to avoid shadowing the installed bokeh package
# (script is named bokeh.py, which would otherwise shadow the bokeh package on import)
if sys.path and sys.path[0] not in ("", "-c"):
    sys.path.pop(0)

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, LabelSet, Legend, LegendItem, WMTSTileSource
from bokeh.plotting import figure
from bokeh.resources import CDN
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (canonical order)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Column constants
CITY = "City"  # role: label
LATITUDE = "Latitude (°)"  # role: latitude
LONGITUDE = "Longitude (°)"  # role: longitude
POPULATION = "Population (millions)"  # role: value
REGION = "Region"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("cities.csv")
df = pd.DataFrame(
    {
        CITY: [
            "Tokyo",
            "Delhi",
            "Shanghai",
            "São Paulo",
            "Mexico City",
            "Cairo",
            "Mumbai",
            "Beijing",
            "Dhaka",
            "Osaka",
            "New York",
            "Karachi",
            "Buenos Aires",
            "Istanbul",
            "Lagos",
            "London",
            "Paris",
            "Bangkok",
            "Lima",
            "Sydney",
            "Toronto",
            "Singapore",
            "Berlin",
            "Madrid",
            "Johannesburg",
        ],
        LATITUDE: [
            35.68,
            28.61,
            31.23,
            -23.55,
            19.43,
            30.04,
            19.08,
            39.90,
            23.81,
            34.69,
            40.71,
            24.86,
            -34.60,
            41.01,
            6.52,
            51.51,
            48.86,
            13.76,
            -12.05,
            -33.87,
            43.65,
            1.35,
            52.52,
            40.42,
            -26.20,
        ],
        LONGITUDE: [
            139.69,
            77.21,
            121.47,
            -46.63,
            -99.13,
            31.24,
            72.88,
            116.41,
            90.41,
            135.50,
            -74.01,
            67.01,
            -58.38,
            28.98,
            3.38,
            -0.13,
            2.35,
            100.50,
            -77.03,
            151.21,
            -79.38,
            103.82,
            13.40,
            -3.70,
            28.04,
        ],
        POPULATION: [
            37.4,
            32.9,
            28.5,
            22.4,
            21.8,
            21.3,
            20.7,
            20.5,
            22.5,
            19.1,
            18.9,
            16.5,
            15.5,
            15.6,
            15.4,
            9.5,
            11.1,
            10.7,
            10.9,
            5.3,
            6.2,
            5.9,
            3.6,
            6.7,
            5.8,
        ],
        REGION: [
            "Asia",
            "Asia",
            "Asia",
            "Americas",
            "Americas",
            "Africa",
            "Asia",
            "Asia",
            "Asia",
            "Asia",
            "Americas",
            "Asia",
            "Americas",
            "Europe",
            "Africa",
            "Europe",
            "Europe",
            "Asia",
            "Americas",
            "Oceania",
            "Americas",
            "Asia",
            "Europe",
            "Europe",
            "Africa",
        ],
    }
)

# Plot: reads only df and the constants above
# Convert lat/lon to Web Mercator projection (EPSG:3857)
EARTH_RADIUS = 6378137
df["x"] = df[LONGITUDE] * (EARTH_RADIUS * np.pi / 180.0)
df["y"] = np.log(np.tan((90 + df[LATITUDE]) * np.pi / 360.0)) * EARTH_RADIUS

# Bubble area proportional to population: the diameter grows with its square root
MAX_SIZE = 62
pop_max = df[POPULATION].max()
df["size"] = MAX_SIZE * np.sqrt(df[POPULATION] / pop_max)

title = "World Cities by Population · bubble-map-geographic · python · bokeh · anyplot.ai"
title_pt = round(50 * 67 / len(title))

tile_style = "World_Light_Gray_Base" if THEME == "light" else "World_Dark_Gray_Base"
tile_url = f"https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/{tile_style}/MapServer/tile/{{z}}/{{y}}/{{x}}"

p = figure(
    width=3200,
    height=1800,
    x_axis_type="mercator",
    y_axis_type="mercator",
    x_axis_label=LONGITUDE,
    y_axis_label=LATITUDE,
    title=title,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
    tools="pan,wheel_zoom,box_zoom,reset,hover,save",
    tooltips=[
        (CITY, f"@{{{CITY}}}"),
        (POPULATION, f"@{{{POPULATION}}}{{0.0}}"),
        (REGION, f"@{{{REGION}}}"),
        ("Coordinates", f"(@{{{LATITUDE}}}{{0.00}}°, @{{{LONGITUDE}}}{{0.00}}°)"),
    ],
)

p.add_tile(WMTSTileSource(url=tile_url))

REGION_ORDER = ["Asia", "Americas", "Europe", "Africa", "Oceania"]  # palette position follows this order

# Bubbles per region, one renderer each for the legend; larger bubbles first so smaller ones stay on top
legend_items = []
for i, region in enumerate(REGION_ORDER):
    rows = df[df[REGION] == region].sort_values(POPULATION, ascending=False)
    renderer = p.scatter(
        x="x",
        y="y",
        source=ColumnDataSource(rows),
        size="size",
        fill_color=IMPRINT_PALETTE[i],
        fill_alpha=0.65,
        line_color=PAGE_BG,
        line_width=1.5,
    )
    legend_items.append(LegendItem(label=str(region), renderers=[renderer]))

# Region legend
legend = Legend(
    items=legend_items,
    title=REGION,
    title_text_font_size="28pt",
    title_text_color=INK,
    label_text_font_size="26pt",
    label_text_color=INK_SOFT,
    glyph_height=36,
    glyph_width=36,
    spacing=12,
    padding=18,
    background_fill_alpha=0.90,
    background_fill_color=ELEVATED_BG,
    border_line_color=INK_SOFT,
    border_line_width=1,
)
p.add_layout(legend, "right")

# Size reference legend: reference bubbles drawn like the data marks, placed over the Pacific
ref_pops = [5, 15, 25, 35]
ref_x = 18500000
ref_y0 = 5600000
ref_dy = 1700000
ref_source = ColumnDataSource(
    data={
        "x": [ref_x] * len(ref_pops),
        "y": [ref_y0 - i * ref_dy for i in range(len(ref_pops))],
        "size": [MAX_SIZE * np.sqrt(pop / pop_max) for pop in ref_pops],
        "label": [f"{pop}M" for pop in ref_pops],
    }
)
p.scatter(
    x="x",
    y="y",
    source=ref_source,
    size="size",
    fill_color=IMPRINT_PALETTE[0],
    fill_alpha=0.65,
    line_color=PAGE_BG,
    line_width=1.5,
)
p.add_layout(
    LabelSet(
        x="x",
        y="y",
        text="label",
        source=ref_source,
        x_offset=48,
        y_offset=-14,
        text_font_size="26pt",
        text_color=INK_SOFT,
        text_align="left",
    )
)
p.text(
    x=[ref_x - 150000],
    y=[ref_y0 + 1300000],
    text=["Population"],
    text_font_size="28pt",
    text_font_style="bold",
    text_color=INK,
)

# Style
p.title.text_font_size = f"{title_pt}pt"
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

# The tile basemap already carries the geographic structure
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None

p.x_range.start = -15000000
p.x_range.end = 21000000
p.y_range.start = -6000000
p.y_range.end = 8500000

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Save
output_file(f"plot-{THEME}.html")
save(p, title=title, resources=CDN)

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
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
