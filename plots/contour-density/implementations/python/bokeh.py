""" anyplot.ai
contour-density: Density Contour Plot
Library: bokeh 3.10.1 | Python 3.14.10
Quality: 87/100 | Updated: 2026-11-09
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, PrintfTickFormatter
from bokeh.plotting import figure
from scipy import stats
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint sequential ramp (imprint_seq): brand green (low density) → blue (high density)
SEQ_LOW, SEQ_HIGH = "#009E73", "#4467A3"
ANYPLOT_SEQ256 = [
    "#{:02X}{:02X}{:02X}".format(
        *(
            round(int(SEQ_LOW[k : k + 2], 16) * (1 - t / 255) + int(SEQ_HIGH[k : k + 2], 16) * t / 255)
            for k in (1, 3, 5)
        )
    )
    for t in range(256)
]

# Constants
N_LEVELS = 8  # number of density contour levels

# Columns: set these to your table's column names
HEIGHT = "Height (cm)"  # role: x
WEIGHT = "Weight (kg)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("body_measurements.csv")
# Adult height and weight survey: two groups with their own centres, weight rising with height
np.random.seed(42)
n_group = 250
height_f = np.random.normal(163, 6, n_group)
height_m = np.random.normal(178, 7, n_group)
weight_f = 62 + 0.6 * (height_f - 163) + np.random.normal(0, 6, n_group)
weight_m = 82 + 0.7 * (height_m - 178) + np.random.normal(0, 7, n_group)
df = pd.DataFrame({HEIGHT: np.concatenate([height_f, height_m]), WEIGHT: np.concatenate([weight_f, weight_m])})

# Plot: reads only df and the constants above
points = df[[HEIGHT, WEIGHT]].dropna()
kde = stats.gaussian_kde(points.to_numpy().T)

x_lo, x_hi = points[HEIGHT].min(), points[HEIGHT].max()
y_lo, y_hi = points[WEIGHT].min(), points[WEIGHT].max()
x_pad, y_pad = 0.08 * (x_hi - x_lo), 0.08 * (y_hi - y_lo)
x_min, x_max, y_min, y_max = x_lo - x_pad, x_hi + x_pad, y_lo - y_pad, y_hi + y_pad

xx, yy = np.meshgrid(np.linspace(x_min, x_max, 160), np.linspace(y_min, y_max, 160))
density = kde(np.vstack([xx.ravel(), yy.ravel()])).reshape(xx.shape)
density /= density.max()  # relative density: the peak is 1

levels = np.linspace(0, 1, N_LEVELS + 2)[1:-1]
level_colors = [ANYPLOT_SEQ256[round(i * 255 / (N_LEVELS - 1))] for i in range(N_LEVELS)]

p = figure(
    width=3200,
    height=1800,
    title="contour-density · python · bokeh · anyplot.ai",
    x_axis_label=HEIGHT,
    y_axis_label=WEIGHT,
    x_range=(x_min, x_max),
    y_range=(y_min, y_max),
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=80,
)

# Scatter overlay: small faint points behind the contours, for context only
source = ColumnDataSource(points)
p.scatter(x=HEIGHT, y=WEIGHT, source=source, size=9, color=INK_MUTED, alpha=0.35, line_color=None)

# Density contours (native bokeh contour renderer), inner rings = higher density
contours = p.contour(xx, yy, density, levels, line_color=level_colors, line_width=4.5, line_alpha=0.95)

color_bar = contours.construct_color_bar(
    title="Relative density (peak = 1)",
    title_text_font_size="30pt",
    title_text_color=INK,
    title_standoff=24,
    major_label_text_font_size="30pt",
    formatter=PrintfTickFormatter(format="%.2f"),
    major_label_text_color=INK_SOFT,
    major_tick_line_color=None,
    width=60,
    background_fill_color=PAGE_BG,
    bar_line_color=None,
    padding=30,
)
p.add_layout(color_bar, "right")

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

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
