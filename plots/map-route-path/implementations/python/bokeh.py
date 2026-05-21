""" anyplot.ai
map-route-path: Route Path Map
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-21
"""

import base64
import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Title
from bokeh.palettes import Viridis256
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Simulated hiking trail GPS track (Rocky Mountain National Park)
np.random.seed(42)

start_lon = -105.683
start_lat = 40.343

n_points = 200
t = np.linspace(0, 1, n_points)

# Linear trail trending northeast with natural meanders (no self-intersections)
lon_progress = 0.038 * t
lat_progress = 0.027 * t
lon_meander = 0.005 * np.sin(10 * np.pi * t) + 0.002 * np.sin(4 * np.pi * t)
lat_meander = 0.004 * np.sin(7 * np.pi * t) + 0.0015 * np.cos(5 * np.pi * t)

lats = start_lat + lat_progress + lat_meander
lons = start_lon + lon_progress + lon_meander

# Convert lat/lon to Web Mercator for tile compatibility
k = 20037508.34 / 180
x_coords = lons * k
y_coords = np.log(np.tan((90 + lats) * np.pi / 360)) / (np.pi / 180) * k

# Viridis gradient along waypoints to show trail progression
waypoint_colors = [Viridis256[int(255 * i / (n_points - 1))] for i in range(n_points)]

source = ColumnDataSource(data={"x": x_coords, "y": y_coords, "color": waypoint_colors})

# Figure
W, H = 3200, 1800
p = figure(
    width=W,
    height=H,
    x_axis_type="mercator",
    y_axis_type="mercator",
    x_axis_label="Longitude",
    y_axis_label="Latitude",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Title
title_obj = Title(
    text="Rocky Mountain Trail · map-route-path · python · bokeh · anyplot.ai", text_font_size="50pt", text_color=INK
)
p.add_layout(title_obj, "above")

# Theme-appropriate basemap tile
tile_provider = "CartoDB Positron" if THEME == "light" else "CartoDB Dark Matter"
p.add_tile(tile_provider)

# Route line — Okabe-Ito position 1 (#009E73)
p.line(x="x", y="y", source=source, line_width=5, line_color="#009E73", line_alpha=0.9)

# Waypoints with viridis gradient showing progression
p.scatter(x="x", y="y", source=source, size=12, fill_color="color", line_color=PAGE_BG, line_width=1.5, alpha=0.85)

# Start marker — Okabe-Ito #009E73 (large circle)
start_src = ColumnDataSource(data={"x": [x_coords[0]], "y": [y_coords[0]]})
p.scatter(
    x="x",
    y="y",
    source=start_src,
    size=32,
    fill_color="#009E73",
    line_color=PAGE_BG,
    line_width=3,
    legend_label="Start",
)

# End marker — Okabe-Ito #D55E00 (large square)
end_src = ColumnDataSource(data={"x": [x_coords[-1]], "y": [y_coords[-1]]})
p.scatter(
    x="x",
    y="y",
    source=end_src,
    size=32,
    fill_color="#D55E00",
    line_color=PAGE_BG,
    line_width=3,
    marker="square",
    legend_label="End",
)

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

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

# Minimal grid over basemap
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.06
p.ygrid.grid_line_alpha = 0.06

# Legend
p.legend.location = "top_right"
p.legend.label_text_font_size = "34pt"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome (Selenium 4 / Selenium Manager)
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
time.sleep(3)
# Capture full page (beyond visible viewport) to handle the ~139px viewport gap
result = driver.execute_cdp_cmd("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True})
with open(f"plot-{THEME}.png", "wb") as fh:
    fh.write(base64.b64decode(result["data"]))
driver.quit()
