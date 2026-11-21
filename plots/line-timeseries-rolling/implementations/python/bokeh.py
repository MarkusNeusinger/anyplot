""" anyplot.ai
line-timeseries-rolling: Time Series with Rolling Average Overlay
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-21
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

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
ROLLING_WINDOW = 20
W, H = 3200, 1800

# Columns
DATE = "Date"  # role: date
PRICE = "Stock Price ($)"  # role: value
ROLLING = "Rolling Average ($)"  # role: rolling_avg

# Data - simulated daily stock prices with a trailing-window rolling average
rng = np.random.default_rng(42)
n_days = 250
prices = np.linspace(100, 120, n_days) + rng.normal(0, 3, n_days)
df = pd.DataFrame({DATE: pd.date_range("2024-01-01", periods=n_days, freq="D"), PRICE: prices})
df[ROLLING] = df[PRICE].rolling(window=ROLLING_WINDOW).mean()

# Plot
source_raw = ColumnDataSource(df)
source_rolling = ColumnDataSource(df.dropna(subset=[ROLLING]))

p = figure(
    width=W,
    height=H,
    title="line-timeseries-rolling · python · bokeh · anyplot.ai",
    x_axis_label=DATE,
    y_axis_label=PRICE,
    x_axis_type="datetime",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Raw data: thin, semi-transparent line receding behind the average
p.line(
    x=DATE,
    y=PRICE,
    source=source_raw,
    line_width=3,
    line_alpha=0.65,
    line_color=IMPRINT_PALETTE[0],
    legend_label="Raw Data",
)

# Rolling average: thick, opaque, contrasting line (starts once the window is filled)
p.line(
    x=DATE,
    y=ROLLING,
    source=source_rolling,
    line_width=7,
    line_color=IMPRINT_PALETTE[1],
    legend_label=f"Rolling Average ({ROLLING_WINDOW}-day)",
)

# Chrome
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
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.12
p.ygrid.grid_line_alpha = 0.12

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.legend.label_text_font_size = "34pt"
p.legend.label_text_color = INK_SOFT
p.legend.location = "top_left"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.glyph_width = 60
p.legend.glyph_height = 40
p.legend.padding = 20
p.legend.spacing = 12

# Save as HTML
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
