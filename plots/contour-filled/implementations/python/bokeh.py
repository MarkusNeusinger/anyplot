""" anyplot.ai
contour-filled: Filled Contour Plot
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-21
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import BasicTicker, ColorBar, FixedTicker, LinearColorMapper
from bokeh.plotting import figure
from scipy.ndimage import zoom
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
TARGET_BANDS = 10  # aim for this many evenly stepped color bands
UPSAMPLE = 12  # grid refinement factor that smooths band boundaries


def lerp_hex(c0, c1, t):
    """Linear blend of two #RRGGBB colors."""
    a = [int(c0[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(c1[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(u + (v - u) * t):02X}" for u, v in zip(a, b, strict=True))


# Columns: set these to your table's column names
EAST = "Distance East (km)"  # role: x
NORTH = "Distance North (km)"  # role: y
ELEVATION = "Terrain Elevation (m)"  # role: z

# Data: replace this block with your own table, for example df = pd.read_csv("terrain.csv")
x_axis = np.linspace(-3, 3, 80)
y_axis = np.linspace(-3, 3, 80)
grid_x, grid_y = np.meshgrid(x_axis, y_axis)
surface = (
    1.5 * np.exp(-((grid_x - 1) ** 2 + (grid_y - 1) ** 2))
    + 2.0 * np.exp(-((grid_x + 1.5) ** 2 + (grid_y + 0.5) ** 2) / 1.5)
    + 1.0 * np.exp(-((grid_x - 0.5) ** 2 + (grid_y + 1.5) ** 2) / 0.8)
    - 0.5 * np.exp(-((grid_x + 0.5) ** 2 + (grid_y - 1.5) ** 2) / 0.5)
)
surface = (surface - surface.min()) / (surface.max() - surface.min()) * 2000
df = pd.DataFrame({EAST: grid_x.ravel(), NORTH: grid_y.ravel(), ELEVATION: surface.ravel()})

# Plot: reads only df and the constants above
field = df.pivot_table(index=NORTH, columns=EAST, values=ELEVATION, sort=True)
xs = field.columns.to_numpy()
ys = field.index.to_numpy()
z = field.to_numpy()
z_min, z_max = np.nanmin(z), np.nanmax(z)

# Evenly stepped levels on round numbers
raw_step = (z_max - z_min) / TARGET_BANDS
magnitude = 10 ** np.floor(np.log10(raw_step))
step = magnitude * next(m for m in (1, 2, 2.5, 5, 10) if m >= raw_step / magnitude)
levels = np.arange(np.floor(z_min / step) * step, z_max + step, step)
n_bands = len(levels) - 1

# Sequential Imprint ramp (green to blue), one color per band
band_colors = [lerp_hex("#009E73", "#4467A3", i / max(n_bands - 1, 1)) for i in range(n_bands)]

p = figure(
    width=3200,
    height=1800,
    title="contour-filled · python · bokeh · anyplot.ai",
    x_axis_label=EAST,
    y_axis_label=NORTH,
    x_range=(xs.min(), xs.max()),
    y_range=(ys.min(), ys.max()),
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=60,
    background_fill_color=PAGE_BG,
    border_fill_color=PAGE_BG,
    outline_line_color=INK_SOFT,
)

# Color mapper: evenly stepped levels give one flat color per band
color_mapper = LinearColorMapper(palette=band_colors, low=levels[0], high=levels[-1])

# Filled bands: cubic upsampling keeps band boundaries smooth curves instead of grid stairs
fine = zoom(z, UPSAMPLE, order=3)
p.image(image=[fine], x=xs.min(), y=ys.min(), dw=xs.max() - xs.min(), dh=ys.max() - ys.min(), color_mapper=color_mapper)

# Color bar shows the same levels
color_bar = ColorBar(
    color_mapper=color_mapper,
    ticker=FixedTicker(ticks=list(levels)) if n_bands <= 14 else BasicTicker(desired_num_ticks=10),
    title=ELEVATION,
    title_text_font_size="34pt",
    title_text_color=INK,
    major_label_text_font_size="30pt",
    major_label_text_color=INK_SOFT,
    major_tick_line_color=INK_SOFT,
    bar_line_color=INK_SOFT,
    background_fill_color=PAGE_BG,
    label_standoff=18,
    title_standoff=24,
    width=60,
    padding=30,
)
p.add_layout(color_bar, "right")

# Style
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
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

# Save HTML, then screenshot it with headless Chrome
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
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
