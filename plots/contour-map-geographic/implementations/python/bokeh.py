"""anyplot.ai
contour-map-geographic: Contour Lines on Geographic Map
Library: bokeh 3.10.2 | Python 3.14.10
Quality: pending | Updated: 2026-11-26
"""

import os
import time
from itertools import pairwise
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColorBar, ColumnDataSource, Label, LabelSet, LinearColorMapper
from bokeh.plotting import figure
from contourpy import contour_generator
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")

PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: water blue for the coastline, purple for the border
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential ramp for fields (cells that fill the plot), low -> high
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.369, "#009E73"), (0.803, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#404C02"), (0.487, "#009E73"), (1.0, "#CDD9FF")]
)


def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


IMPRINT_SEQ256 = [ramp_color(SEQ_FIELDS, k / 255) for k in range(256)]

# Constants
CONTOUR_STEP = 250  # contour interval in metres
LABEL_STEP = 500  # every second contour carries a value label
MAJOR_STEP = 1000  # heavier line on the major contours

# Columns
LON = "Longitude (°W)"  # role: x
LAT = "Latitude (°N)"  # role: y
ELEVATION = "Elevation (m)"  # role: value

# Data: simulated elevation, Pacific Northwest (Oregon -> Washington)
rng = np.random.default_rng(42)
lon_min, lon_max = -125.0, -117.0
lat_min, lat_max = 42.0, 49.0
n_points = 50
lon_grid, lat_grid = np.meshgrid(np.linspace(lon_min, lon_max, n_points), np.linspace(lat_min, lat_max, n_points))

base_elevation = (lon_grid - lon_min) / (lon_max - lon_min) * 1000  # rises west -> east
cascade_height = np.exp(-((lon_grid + 121.5) ** 2) / (2 * 0.7**2))  # Cascade Range ridge
cascade_elevation = cascade_height * 1700 * (1 + 0.3 * np.sin(lat_grid * 2))

terrain_noise = rng.standard_normal((n_points, n_points)) * 100
for _ in range(3):
    terrain_noise = (
        np.roll(terrain_noise, 1, axis=0)
        + np.roll(terrain_noise, -1, axis=0)
        + np.roll(terrain_noise, 1, axis=1)
        + np.roll(terrain_noise, -1, axis=1)
    ) / 4

df = pd.DataFrame(
    {
        LON: lon_grid.ravel(),
        LAT: lat_grid.ravel(),
        ELEVATION: np.clip(base_elevation + cascade_elevation + terrain_noise, 0, None).ravel(),
    }
)

# Plot
grid = df.pivot(index=LAT, columns=LON, values=ELEVATION)
lons, lats, elevation = grid.columns.to_numpy(), grid.index.to_numpy(), grid.to_numpy()
lon_grid, lat_grid = np.meshgrid(lons, lats)
lon_lo, lon_hi, lat_lo, lat_hi = lons.min(), lons.max(), lats.min(), lats.max()
elev_top = df[ELEVATION].max()

# The two Cascade Range peaks, north and south of the midlatitude
lat_split = (lat_lo + lat_hi) / 2 - 0.25
peaks = []
for name, mask in (("S. Cascades", lat_grid <= lat_split), ("N. Cascades", lat_grid > lat_split)):
    idx = np.unravel_index(np.argmax(np.where(mask, elevation, -np.inf)), elevation.shape)
    peaks.append((lons[idx[1]], lats[idx[0]], int(elevation[idx]), name))

gen = contour_generator(x=lon_grid, y=lat_grid, z=elevation)
levels = np.arange(CONTOUR_STEP, elev_top, CONTOUR_STEP)

W, H = 3200, 1800
p = figure(
    width=W,
    height=H,
    title="contour-map-geographic · python · bokeh · anyplot.ai",
    x_axis_label=LON,
    y_axis_label=LAT,
    x_range=(lon_lo, lon_hi),
    y_range=(lat_lo, lat_hi),
    toolbar_location=None,
    tools="pan,wheel_zoom,reset",
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=80,
)

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

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

# Elevation raster
color_mapper = LinearColorMapper(palette=IMPRINT_SEQ256, low=0, high=elev_top)
p.image(
    image=[elevation], x=lon_lo, y=lat_lo, dw=lon_hi - lon_lo, dh=lat_hi - lat_lo, color_mapper=color_mapper, alpha=0.72
)

# Contour lines with overlap-aware label placement
MIN_LABEL_DIST = 0.8  # minimum degrees between label centers
label_data = {"x": [], "y": [], "text": []}
for level in levels:
    for path in gen.lines(level):
        if path is None or len(path) < 5:
            continue
        line_width = 3.5 if level % MAJOR_STEP == 0 else 2.0
        p.line(x=path[:, 0], y=path[:, 1], line_color=PAGE_BG, line_width=line_width + 3, line_alpha=0.55)
        p.line(x=path[:, 0], y=path[:, 1], line_color=INK, line_width=line_width, line_alpha=0.9)
        if level % LABEL_STEP == 0 and len(path) > 20:
            cx, cy = path[len(path) // 2]
            too_close = any(
                (cx - ex) ** 2 + (cy - ey) ** 2 < MIN_LABEL_DIST**2
                for ex, ey in zip(label_data["x"], label_data["y"], strict=True)
            )
            if not too_close:
                label_data["x"].append(cx)
                label_data["y"].append(cy)
                label_data["text"].append(f"{int(level)}m")

p.add_layout(
    LabelSet(
        x="x",
        y="y",
        text="text",
        source=ColumnDataSource(data=label_data),
        text_font_size="28pt",
        text_color=INK,
        text_font_style="bold",
        background_fill_color=ELEVATED_BG,
        background_fill_alpha=0.90,
        border_line_color=INK_SOFT,
        border_line_alpha=0.35,
    )
)

# Approximate Pacific coastline (blue = water)
coast_lons = [-125.0, -124.8, -124.5, -124.2, -124.0, -123.8, -124.0, -124.3, -124.5]
coast_lats = [42.0, 43.5, 45.0, 46.0, 46.5, 47.5, 48.0, 48.5, 49.0]
p.line(x=coast_lons, y=coast_lats, line_color=IMPRINT_PALETTE[2], line_width=5, legend_label="Coastline (approx.)")

# Oregon / Washington state border (lat ~ 46.2)
p.line(
    x=[lon_lo, -124.0],
    y=[46.2, 46.2],
    line_color=IMPRINT_PALETTE[1],
    line_width=3.5,
    line_dash="dashed",
    legend_label="OR / WA Border",
)

# Cascade Range peak markers and annotations
for peak_lon, peak_lat, peak_elev, name in peaks:
    p.add_layout(
        Label(
            x=peak_lon + 0.15,
            y=peak_lat + 0.12,
            text=f"{name}\n~{peak_elev:,} m",
            text_font_size="24pt",
            text_color=INK,
            text_font_style="bold",
            background_fill_color=ELEVATED_BG,
            background_fill_alpha=0.88,
            border_line_color=INK_SOFT,
            border_line_alpha=0.5,
        )
    )
p.scatter(
    x=[pk[0] for pk in peaks], y=[pk[1] for pk in peaks], marker="inverted_triangle", size=28, color=INK, alpha=0.75
)

p.add_layout(
    ColorBar(
        color_mapper=color_mapper,
        label_standoff=14,
        width=55,
        location=(0, 0),
        title=ELEVATION,
        title_text_font_size="34pt",
        title_text_color=INK,
        major_label_text_font_size="30pt",
        major_label_text_color=INK_SOFT,
        background_fill_color=PAGE_BG,
    ),
    "right",
)

p.legend.location = "bottom_right"
p.legend.label_text_font_size = "34pt"
p.legend.label_text_color = INK_SOFT
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.background_fill_alpha = 0.92
p.legend.glyph_height = 40
p.legend.glyph_width = 40
p.legend.label_standoff = 16
p.legend.spacing = 12
p.legend.padding = 20

# Save HTML + PNG via headless Chrome
output_file(f"plot-{THEME}.html")
save(p)

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
driver.execute_script(
    "document.documentElement.style.background = arguments[0]; document.body.style.background = arguments[0];", PAGE_BG
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
