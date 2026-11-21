"""anyplot.ai
line-markers: Line Plot with Markers
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-12
"""

import calendar
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
MARKERS = ["circle", "square", "triangle", "diamond", "inverted_triangle", "hex", "star", "plus"]

# Columns: set these to your table's column names
MONTH = "Month"  # role: x
Y = ["Station A", "Station B", "Station C"]  # role: y
Y_LABEL = "Temperature (°C)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("temperatures.csv")
np.random.seed(42)
months = np.arange(1, 13)
base_temp = np.array([2, 4, 8, 12, 17, 21, 24, 23, 19, 13, 7, 3])
station_a = base_temp + np.random.randn(12) * 1.5
station_b = base_temp + 3 + np.random.randn(12) * 1.5
station_c = base_temp - 2 + np.random.randn(12) * 1.5
df = pd.DataFrame({MONTH: months, Y[0]: station_a, Y[1]: station_b, Y[2]: station_c})

# Plot: reads only df and the constants above
W, H = 3200, 1800
p = figure(
    width=W,
    height=H,
    title="line-markers · python · bokeh · anyplot.ai",
    x_axis_label=MONTH,
    y_axis_label=Y_LABEL,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=60,
)

source = ColumnDataSource(df.sort_values(MONTH))
for i, station in enumerate(Y):
    color = IMPRINT_PALETTE[i]
    p.line(x=MONTH, y=station, source=source, line_width=5, color=color, alpha=0.9)
    p.scatter(
        x=MONTH,
        y=station,
        source=source,
        size=28,
        marker=MARKERS[i],
        fill_color=color,
        line_color=PAGE_BG,
        line_width=3,
        legend_label=station,
    )

# Month numbers become calendar abbreviations
month_values = df[MONTH].drop_duplicates().sort_values().tolist()
p.xaxis.ticker = month_values
p.xaxis.major_label_overrides = {m: calendar.month_abbr[int(m)] if 1 <= m <= 12 else str(m) for m in month_values}

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

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10
p.xgrid.grid_line_width = 2
p.ygrid.grid_line_width = 2

p.legend.label_text_font_size = "32pt"
p.legend.label_text_color = INK_SOFT
p.legend.glyph_height = 44
p.legend.glyph_width = 44
p.legend.spacing = 14
p.legend.padding = 24
p.legend.location = "top_left"
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 1.0
p.legend.border_line_color = INK_SOFT

# Save HTML, then screenshot it with headless Chrome
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
driver.set_window_size(W, H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
