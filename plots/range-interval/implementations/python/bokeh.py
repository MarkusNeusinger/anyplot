"""anyplot.ai
range-interval: Range Interval Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-18
"""

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

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
MONTH = "Month"  # role: category
LOW = "Minimum temperature (°C)"  # role: min_value
HIGH = "Maximum temperature (°C)"  # role: max_value

# Data: replace this block with your own table, for example df = pd.read_csv("ranges.csv")
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
base_temps = [2, 4, 8, 12, 16, 20, 23, 22, 18, 13, 7, 3]
df = pd.DataFrame(
    {
        MONTH: months,
        LOW: [base - np.random.uniform(3, 6) for base in base_temps],
        HIGH: [base + np.random.uniform(5, 10) for base in base_temps],
    }
)

# Plot: reads only df and the constants above
MID = "Midpoint"
df[MID] = (df[LOW] + df[HIGH]) / 2
source = ColumnDataSource(df)

p = figure(
    width=3200,
    height=1800,
    title="range-interval · python · bokeh · anyplot.ai",
    x_axis_label=MONTH,
    y_axis_label="Temperature (°C)",
    x_range=list(df[MONTH]),
    tools="",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Range bars (segment glyphs)
p.segment(
    x0=MONTH,
    y0=LOW,
    x1=MONTH,
    y1=HIGH,
    source=source,
    line_width=34,
    line_color=IMPRINT_PALETTE[0],
    line_alpha=0.7,
    line_cap="round",
)

# Endpoint and midpoint markers
p.scatter(
    x=MONTH,
    y=LOW,
    source=source,
    size=26,
    color=IMPRINT_PALETTE[0],
    line_color=PAGE_BG,
    line_width=3,
    legend_label="Minimum",
)
p.scatter(
    x=MONTH,
    y=HIGH,
    source=source,
    size=26,
    color=IMPRINT_PALETTE[1],
    line_color=PAGE_BG,
    line_width=3,
    legend_label="Maximum",
)
p.scatter(
    x=MONTH,
    y=MID,
    source=source,
    size=18,
    marker="diamond",
    color=INK_SOFT,
    line_color=PAGE_BG,
    line_width=2,
    legend_label=MID,
)

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

p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10
p.xgrid.grid_line_color = None

p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.axis.axis_line_width = 2
p.outline_line_color = INK_SOFT

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG

p.legend.location = "top_left"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_font_size = "30pt"
p.legend.label_text_color = INK_SOFT
p.legend.padding = 15
p.legend.spacing = 10

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
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
