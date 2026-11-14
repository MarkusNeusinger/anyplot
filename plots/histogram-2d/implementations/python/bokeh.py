"""anyplot.ai
histogram-2d: 2D Histogram Heatmap
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-08
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColorBar, HoverTool, LinearColorMapper
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]


def lerp_hex(c0, c1, t):
    """Linear blend between two hex colors."""
    a = [int(c0[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(c1[i : i + 2], 16) for i in (1, 3, 5)]
    r, g, bl = (round(x + (y - x) * t) for x, y in zip(a, b, strict=True))
    return f"#{r:02X}{g:02X}{bl:02X}"


# Imprint sequential ramp: position 1 (green) to position 3 (blue)
IMPRINT_SEQ = [lerp_hex(IMPRINT_PALETTE[0], IMPRINT_PALETTE[2], t / 255) for t in range(256)]

# Constants
BINS = 35  # bins per axis, fits a sample of a few thousand points

# Columns: set these to your table's column names
TECH = "Tech stock return (%)"  # role: x
COMMODITY = "Commodity return (%)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("returns.csv")
np.random.seed(42)
sample = np.random.multivariate_normal([0.5, 0.5], [[1, 0.6], [0.6, 1]], 5000)
df = pd.DataFrame({TECH: sample[:, 0], COMMODITY: sample[:, 1]})

# Plot: reads only df and the constants above
hist, x_edges, y_edges = np.histogram2d(df[TECH].dropna(), df[COMMODITY].dropna(), bins=BINS)

p = figure(
    width=3200,
    height=1800,
    title="histogram-2d · python · bokeh · anyplot.ai",
    x_axis_label=TECH,
    y_axis_label=COMMODITY,
    x_range=(x_edges[0], x_edges[-1]),
    y_range=(y_edges[0], y_edges[-1]),
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
    tools="",
)

# Empty bins stay blank (NaN) so the lowest counts read against the page
counts = np.where(hist > 0, hist, np.nan)
color_mapper = LinearColorMapper(palette=IMPRINT_SEQ, low=1, high=np.nanmax(counts), nan_color="rgba(0,0,0,0)")
p.image(
    image=[counts.T],
    x=x_edges[0],
    y=y_edges[0],
    dw=x_edges[-1] - x_edges[0],
    dh=y_edges[-1] - y_edges[0],
    color_mapper=color_mapper,
)
p.add_tools(HoverTool(tooltips=[("Count", "@image")]))

color_bar = ColorBar(
    color_mapper=color_mapper,
    width=60,
    location=(0, 0),
    title="Count per bin",
    title_text_font_size="38pt",
    title_text_color=INK,
    major_label_text_font_size="30pt",
    major_label_text_color=INK_SOFT,
    title_standoff=20,
    background_fill_color=PAGE_BG,
    major_tick_line_color=INK_SOFT,
    bar_line_color=INK_SOFT,
)
p.add_layout(color_bar, "right")

# Style
p.title.text_font_size = "50pt"
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.title.text_color = INK
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_alpha = 0.0
p.ygrid.grid_line_alpha = 0.0

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome
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
