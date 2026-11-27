"""anyplot.ai
hexbin-basic: Basic Hexbin Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 94/100 | Created: 2026-05-29
"""

import math
import os
import sys
import time
from itertools import pairwise
from pathlib import Path


# Prevent this file (bokeh.py) from shadowing the installed bokeh package
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _script_dir]

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColorBar, ColumnDataSource, LinearColorMapper
from bokeh.plotting import figure
from bokeh.transform import transform
from bokeh.util.hex import hexbin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential ramp for colored cells (fields), sampled at 256 even steps
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.369, "#009E73"), (0.803, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#404C02"), (0.487, "#009E73"), (1.0, "#CDD9FF")]
)


def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    if not math.isfinite(t):
        return "none"
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


ANYPLOT_SEQ256 = [ramp_color(SEQ_FIELDS, k / 255) for k in range(256)]

# Columns: set these to your table's column names
X = "Distance East (km)"  # role: x
Y = "Distance North (km)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("sensors.csv")
# IoT sensor readings across urban monitoring zones (overlapping plumes)
np.random.seed(42)
centers = [(-3, -1), (2, 1), (-0.5, 3), (1.0, -2), (0.5, 0.5)]
cluster_sizes = [3500, 3000, 1800, 1200, 1500]
spreads = [1.0, 1.3, 0.65, 0.75, 1.6]
x_data, y_data = [], []
for (cx, cy), size, sigma in zip(centers, cluster_sizes, spreads, strict=True):
    x_data.extend(np.random.randn(size) * sigma + cx)
    y_data.extend(np.random.randn(size) * sigma + cy)
df = pd.DataFrame({X: x_data, Y: y_data})

# Plot: reads only df and the constants above
# Bin width: about 42 hexagons across the x range
hex_size = (df[X].max() - df[X].min()) / 42
bins = hexbin(df[X].to_numpy(), df[Y].to_numpy(), hex_size)
source = ColumnDataSource({"q": bins.q, "r": bins.r, "counts": bins.counts})

p = figure(
    width=3200,
    height=1800,
    title="hexbin-basic · python · bokeh · anyplot.ai",
    x_axis_label=X,
    y_axis_label=Y,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=250,
)

mapper = LinearColorMapper(palette=ANYPLOT_SEQ256, low=0, high=float(bins.counts.max()))
p.hex_tile(q="q", r="r", size=hex_size, line_color=None, source=source, fill_color=transform("counts", mapper))

color_bar = ColorBar(
    color_mapper=mapper,
    width=80,
    title="Count",
    title_text_font_size="34pt",
    title_text_color=INK,
    major_label_text_font_size="28pt",
    major_label_text_color=INK_SOFT,
    background_fill_color=PAGE_BG,
    background_fill_alpha=1.0,
    padding=20,
)
p.add_layout(color_bar, "right")

# Chrome — theme-adaptive
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.title.text_font_size = "50pt"
p.title.text_color = INK
p.title.text_font_style = "bold"

p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"

p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

p.xaxis.axis_line_color = None
p.yaxis.axis_line_color = None
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.grid.visible = False

# Save HTML (interactive catalog artifact)
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot via Selenium headless Chrome
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
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
# Paint the page in the theme color so the anti-aliased canvas edge shows no light line
driver.execute_script(
    "document.documentElement.style.background = arguments[0]; document.body.style.background = arguments[0];", PAGE_BG
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
