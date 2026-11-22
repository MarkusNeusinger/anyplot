"""anyplot.ai
heatmap-geographic: Geographic Heatmap for Spatial Density
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-18
"""

import os
import sys
import time
from pathlib import Path


# Keep the sibling per-library files in this folder from shadowing real packages
sys.path = [p for p in sys.path if p not in (str(Path(__file__).parent.absolute()), "")]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from bokeh.io import output_file, save  # noqa: E402
from bokeh.models import BasicTicker, ColorBar, ColumnDataSource, HoverTool, LinearColorMapper, WMTSTileSource  # noqa: E402
from bokeh.plotting import figure  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: first series is always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]


def lerp_hex(c0, c1, t):
    """Linear blend between two hex colors."""
    a = [int(c0[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(c1[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b, strict=True))


# Imprint sequential ramp (single polarity): green (sparse) to blue (dense)
IMPRINT_SEQ256 = [lerp_hex("#009E73", "#4467A3", t / 255.0) for t in range(256)]

# Constants
MIN_VISIBLE = 0.01  # share of the color-scale top below which the layer stays transparent
SIGMA_CELLS = 4  # Gaussian smoothing bandwidth, in grid cells
GRID_CELLS = 200  # density grid resolution along the longer side
PAD_DEGREES = 1.0  # map margin around the data, in degrees

# Columns: set these to your table's column names
LATITUDE = "Latitude (°)"  # role: latitude
LONGITUDE = "Longitude (°)"  # role: longitude
VALUE = "AQI"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("stations.csv")
rng = np.random.default_rng(42)
n_points = 500
clusters = [(36.5, -121.0, 0.8, 0.5), (34.0, -118.0, 0.6, 0.7), (38.5, -121.5, 0.5, 0.4)]
sizes = [n_points // 3, n_points // 3, n_points - 2 * (n_points // 3)]
df = pd.concat(
    [
        pd.DataFrame({LATITUDE: rng.normal(lat, s_lat, n), LONGITUDE: rng.normal(lon, s_lon, n)})
        for (lat, lon, s_lat, s_lon), n in zip(clusters, sizes, strict=True)
    ],
    ignore_index=True,
)
df[VALUE] = rng.exponential(scale=50, size=len(df)) + 20

# Plot: reads only df and the constants above
R_EARTH = 20037508.34


def to_mercator(lat, lon):
    x = np.asarray(lon) * R_EARTH / 180
    y = np.log(np.tan((90 + np.asarray(lat)) * np.pi / 360)) / (np.pi / 180) * R_EARTH / 180
    return x, y


df["x"], df["y"] = to_mercator(df[LATITUDE], df[LONGITUDE])

# Map extent: the data's bounds plus a margin
x_min, y_min = to_mercator(df[LATITUDE].min() - PAD_DEGREES, df[LONGITUDE].min() - PAD_DEGREES)
x_max, y_max = to_mercator(df[LATITUDE].max() + PAD_DEGREES, df[LONGITUDE].max() + PAD_DEGREES)

# Weighted 2D histogram, then Gaussian smoothing for a continuous density surface
nx = GRID_CELLS
ny = max(2, round(GRID_CELLS * (y_max - y_min) / (x_max - x_min)))
heatmap, _, _ = np.histogram2d(
    df["x"], df["y"], bins=[np.linspace(x_min, x_max, nx + 1), np.linspace(y_min, y_max, ny + 1)], weights=df[VALUE]
)
offsets = np.arange(-3 * SIGMA_CELLS, 3 * SIGMA_CELLS + 1)
kernel = np.exp(-(offsets**2) / (2 * SIGMA_CELLS**2))
kernel /= kernel.sum()
smooth = np.apply_along_axis(lambda v: np.convolve(v, kernel, mode="same"), 0, heatmap)
smooth = np.apply_along_axis(lambda v: np.convolve(v, kernel, mode="same"), 1, smooth)

top = np.percentile(smooth[smooth > 0], 95)
display = np.where(smooth < top * MIN_VISIBLE, np.nan, smooth)
color_mapper = LinearColorMapper(palette=IMPRINT_SEQ256, low=0, high=top, nan_color="rgba(0, 0, 0, 0)")

p = figure(
    width=3200,
    height=1800,
    x_range=(x_min, x_max),
    y_range=(y_min, y_max),
    x_axis_type="mercator",
    y_axis_type="mercator",
    match_aspect=True,
    toolbar_location=None,
    title="California AQI Monitoring · heatmap-geographic · python · bokeh · anyplot.ai",
    x_axis_label=LONGITUDE,
    y_axis_label=LATITUDE,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Theme-appropriate basemap tiles
style = "World_Light_Gray_Base" if THEME == "light" else "World_Dark_Gray_Base"
p.add_tile(
    WMTSTileSource(
        url=f"https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/{style}/MapServer/tile/{{Z}}/{{Y}}/{{X}}"
    )
)

p.image(image=[display.T], x=x_min, y=y_min, dw=x_max - x_min, dh=y_max - y_min, color_mapper=color_mapper, alpha=0.7)

# Monitoring stations, hover shows the AQI reading
stations = p.scatter(
    x="x",
    y="y",
    source=ColumnDataSource(df),
    size=12,
    color=IMPRINT_PALETTE[0],
    line_color=INK,
    line_width=1.5,
    alpha=0.8,
    legend_label="Monitoring stations",
)
p.add_tools(
    HoverTool(
        renderers=[stations],
        tooltips=[
            (VALUE, f"@{{{VALUE}}}{{0.0}}"),
            ("Lat / Lon", f"@{{{LATITUDE}}}{{0.00}}° / @{{{LONGITUDE}}}{{0.00}}°"),
        ],
    )
)

color_bar = ColorBar(
    color_mapper=color_mapper,
    ticker=BasicTicker(),
    label_standoff=16,
    border_line_color=None,
    location=(0, 0),
    title="AQI-weighted density",
    title_text_font_size="34pt",
    title_text_color=INK,
    major_label_text_font_size="34pt",
    major_label_text_color=INK_SOFT,
    width=50,
    background_fill_color=PAGE_BG,
)
p.add_layout(color_bar, "right")

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT
p.title.text_font_size = "50pt"
p.title.text_color = INK
for axis in (p.xaxis, p.yaxis):
    axis.axis_label_text_font_size = "42pt"
    axis.major_label_text_font_size = "34pt"
    axis.axis_label_text_color = INK
    axis.major_label_text_color = INK_SOFT
    axis.axis_line_color = INK_SOFT
    axis.major_tick_line_color = INK_SOFT
for grid in (p.xgrid, p.ygrid):
    grid.grid_line_color = INK
    grid.grid_line_alpha = 0.10

p.legend.location = "top_right"
p.legend.label_text_font_size = "34pt"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT

# Save HTML, then screenshot it with headless Chrome
output_file(f"plot-{THEME}.html", title="Geographic Heatmap for Spatial Density")
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
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
