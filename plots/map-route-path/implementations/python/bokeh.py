"""anyplot.ai
map-route-path: Route Path Map
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-21
"""

import base64
import os
import sys
import time
from itertools import pairwise
from pathlib import Path


# bokeh.py shadows the installed bokeh package when Python adds this file's
# directory to sys.path[0]; remove it so imports resolve to the package.
_here = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != _here]
del _here

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColorBar, ColumnDataSource, LinearColorMapper, Title
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
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


# LinearColorMapper takes evenly spaced colors, so sample the stops at 256 even steps
ANYPLOT_SEQ256 = [ramp_color(SEQ_MARKS, k / 255) for k in range(256)]

# Columns: set these to your table's column names
LAT = "Latitude"  # role: lat
LON = "Longitude"  # role: lon
SEQUENCE = "Waypoint order"  # role: sequence

# Data: replace this block with your own GPS track, for example df = pd.read_csv("track.csv")
# Simulated hiking trail (Rocky Mountain National Park), 200 waypoints in travel order
n_points = 200
t = np.linspace(0, 1, n_points)
df = pd.DataFrame(
    {
        SEQUENCE: np.arange(n_points),
        LAT: 40.343 + 0.027 * t + 0.003 * np.sin(2 * np.pi * t),
        LON: -105.683 + 0.038 * t + 0.006 * np.sin(np.pi * t),
    }
)

# Plot: reads only df and the constants above
df = df.sort_values(SEQUENCE).reset_index(drop=True)

# Convert lat/lon to Web Mercator for tile compatibility
k = 20037508.34 / 180
df["x"] = df[LON] * k
df["y"] = np.log(np.tan((90 + df[LAT]) * np.pi / 360)) / (np.pi / 180) * k

# Progress along the route (0-100 %) drives the dot colors and the colorbar
df["progress"] = np.linspace(0, 100, len(df))
mapper = LinearColorMapper(palette=ANYPLOT_SEQ256, low=0, high=100)
source = ColumnDataSource(df)

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
    min_border_right=200,  # extra room for the colorbar + tick labels
)

# Title
title_obj = Title(
    text="Rocky Mountain Trail · map-route-path · python · bokeh · anyplot.ai", text_font_size="50pt", text_color=INK
)
p.add_layout(title_obj, "above")

# Theme-appropriate basemap tile
tile_provider = "CartoDB Positron" if THEME == "light" else "CartoDB Dark Matter"
p.add_tile(tile_provider)

# Route line — Imprint position 1, wider than the dots so it frames them
p.line(x="x", y="y", source=source, line_width=8, line_color=IMPRINT_PALETTE[0], line_alpha=0.95)

# Waypoints with the Imprint ramp showing trail progression
p.scatter(
    x="x",
    y="y",
    source=source,
    size=9,
    fill_color={"field": "progress", "transform": mapper},
    line_color=PAGE_BG,
    line_width=1,
)

# Start marker — Imprint position 1 (large circle)
start_src = ColumnDataSource(df.iloc[[0]])
p.scatter(
    x="x",
    y="y",
    source=start_src,
    size=32,
    fill_color=IMPRINT_PALETTE[0],
    line_color=PAGE_BG,
    line_width=3,
    legend_label="Start",
)

# End marker — Imprint position 2 (large square)
end_src = ColumnDataSource(df.iloc[[-1]])
p.scatter(
    x="x",
    y="y",
    source=end_src,
    size=32,
    fill_color=IMPRINT_PALETTE[1],
    line_color=PAGE_BG,
    line_width=3,
    marker="square",
    legend_label="End",
)

# Colorbar decoding the ramp: green = trail start, dark blue / pale blue = trail end
color_bar = ColorBar(
    color_mapper=mapper,
    label_standoff=16,
    major_label_text_font_size="34pt",
    major_label_text_color=INK_SOFT,
    title="Trail Progress (%)",
    title_text_font_size="34pt",
    title_text_color=INK,
    background_fill_color=PAGE_BG,
    bar_line_color=INK_SOFT,
    major_tick_line_color=INK_SOFT,
    width=40,
)
p.add_layout(color_bar, "right")

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

# Slightly more visible grid on the near-black dark basemap
grid_alpha = 0.06 if THEME == "light" else 0.09
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = grid_alpha
p.ygrid.grid_line_alpha = grid_alpha

# Legend
p.legend.location = "top_right"
p.legend.label_text_font_size = "34pt"
p.legend.glyph_height = 40
p.legend.glyph_width = 40
p.legend.label_standoff = 16
p.legend.spacing = 12
p.legend.padding = 20
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
