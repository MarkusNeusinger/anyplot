""" anyplot.ai
chessboard-basic: Chess Board Grid Visualization
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-22
"""

import os
import time
from pathlib import Path

import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Chess board colors (constant across themes; the board is the data)
LIGHT_SQUARE = "#F0D9B5"
DARK_SQUARE = "#B58863"

# Setup
W, H = 2400, 2400

# Columns
FILE = "File"  # role: columns
RANK = "Rank"  # role: rows

# Data - 8x8 chess board, light square at h1 and a8
files = list("abcdefgh")
ranks = list("12345678")
df = pd.DataFrame(
    [
        {FILE: f, RANK: r, "shade": "light" if (i + j) % 2 == 1 else "dark"}
        for j, r in enumerate(ranks)
        for i, f in enumerate(files)
    ]
)

# Plot
df["fill"] = df["shade"].map({"light": LIGHT_SQUARE, "dark": DARK_SQUARE})
p = figure(
    width=W,
    height=H,
    title="chessboard-basic · python · bokeh · anyplot.ai",
    x_range=files,
    y_range=ranks,
    x_axis_label=FILE,
    y_axis_label=RANK,
    tools="",
    toolbar_location=None,
    min_border_left=190,
    min_border_bottom=190,
    min_border_top=190,
    min_border_right=190,
)

p.rect(x=FILE, y=RANK, width=1, height=1, source=ColumnDataSource(df), color="fill", line_color=INK_SOFT, line_width=2)

# Style
p.title.text_font_size = "40pt"
p.title.text_color = INK
p.title.align = "center"

for axis in (p.xaxis, p.yaxis):
    axis.major_label_text_font_size = "34pt"
    axis.major_label_text_color = INK_SOFT
    axis.axis_label_text_font_size = "30pt"
    axis.axis_label_text_color = INK
    axis.axis_line_color = None
    axis.major_tick_line_color = None
    axis.minor_tick_line_color = None

p.xgrid.visible = False
p.ygrid.visible = False

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT
p.outline_line_width = 3

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome
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
