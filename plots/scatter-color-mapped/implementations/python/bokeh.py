"""anyplot.ai
scatter-color-mapped: Color-Mapped Scatter Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-08
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColorBar, ColumnDataSource, HoverTool, LinearColorMapper
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


def _lerp_hex(c0, c1, t):
    r0, g0, b0 = (int(c0[i : i + 2], 16) for i in (1, 3, 5))
    r1, g1, b1 = (int(c1[i : i + 2], 16) for i in (1, 3, 5))
    r, g, b = (round(a + (b - a) * t) for a, b in ((r0, r1), (g0, g1), (b0, b1)))
    return f"#{r:02X}{g:02X}{b:02X}"


# Imprint sequential ramp (single polarity): first palette position to the blue position
IMPRINT_SEQ256 = [_lerp_hex("#009E73", "#4467A3", t / 255.0) for t in range(256)]

# Columns: set these to your table's column names
X = "X coordinate (m)"  # role: x
Y = "Y coordinate (m)"  # role: y
INTENSITY = "Intensity (a.u.)"  # role: color

# Data: replace this block with your own table, for example df = pd.read_csv("measurements.csv")
rng = np.random.default_rng(42)
n_points = 150
x_values = rng.normal(50, 10, n_points)
y_values = 0.6 * x_values + rng.normal(0, 8, n_points) + 20
intensity_values = np.sqrt((x_values - 50) ** 2 + (y_values - 50) ** 2) + rng.normal(0, 3, n_points)
df = pd.DataFrame({X: x_values, Y: y_values, INTENSITY: intensity_values})

# Plot: reads only df and the constants above
source = ColumnDataSource(df)
color_mapper = LinearColorMapper(palette=IMPRINT_SEQ256, low=df[INTENSITY].min(), high=df[INTENSITY].max())

p = figure(
    width=3200,
    height=1800,
    title="scatter-color-mapped · python · bokeh · anyplot.ai",
    x_axis_label=X,
    y_axis_label=Y,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

p.scatter(
    x=X,
    y=Y,
    source=source,
    size=26,
    fill_color={"field": INTENSITY, "transform": color_mapper},
    fill_alpha=0.85,
    line_color=INK_SOFT,
    line_width=1.5,
    line_alpha=0.6,
)

hover = HoverTool(
    tooltips=[("X", f"@{{{X}}}{{0.00}}"), ("Y", f"@{{{Y}}}{{0.00}}"), ("Intensity", f"@{{{INTENSITY}}}{{0.00}}")]
)
p.add_tools(hover)

color_bar = ColorBar(
    color_mapper=color_mapper,
    title=INTENSITY,
    title_text_font_size="34pt",
    title_text_color=INK,
    title_standoff=20,
    major_label_text_font_size="30pt",
    major_label_text_color=INK_SOFT,
    major_tick_line_color=INK_SOFT,
    bar_line_color=INK_SOFT,
    background_fill_color=PAGE_BG,
    label_standoff=14,
    width=50,
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

p.grid.grid_line_color = INK
p.grid.grid_line_alpha = 0.10
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with Selenium
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
