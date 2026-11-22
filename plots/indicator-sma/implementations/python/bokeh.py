""" anyplot.ai
indicator-sma: Simple Moving Average (SMA) Indicator Chart
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-22
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Legend
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
SMA_PERIODS = [20, 50, 200]  # standard short, medium and long windows for daily data
SMA_DASHES = ["dashed", "dashdot", "dotted"]  # one dash pattern per SMA

# Columns: set these to your table's column names
DATE = "Trading date"  # role: date
CLOSE = "Close price ($)"  # role: close
SMA_SHORT = "SMA 20"  # role: sma_short
SMA_MEDIUM = "SMA 50"  # role: sma_medium
SMA_LONG = "SMA 200"  # role: sma_long

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
# Engineered to produce visible golden cross / death cross signals
np.random.seed(42)
n_days = 300
dates = pd.date_range(start="2024-01-01", periods=n_days, freq="B")
returns = np.concatenate(
    [np.random.normal(0.001, 0.012, 100), np.random.normal(-0.002, 0.015, 80), np.random.normal(0.003, 0.013, 120)]
)
price = 100 * np.exp(np.cumsum(returns))

close = pd.Series(price)
df = pd.DataFrame(
    {
        DATE: dates,
        CLOSE: price,
        SMA_SHORT: close.rolling(window=SMA_PERIODS[0]).mean(),
        SMA_MEDIUM: close.rolling(window=SMA_PERIODS[1]).mean(),
        SMA_LONG: close.rolling(window=SMA_PERIODS[2]).mean(),
    }
)

# Plot: reads only df and the constants above
sma_columns = [SMA_SHORT, SMA_MEDIUM, SMA_LONG]
source = ColumnDataSource(df)

p = figure(
    width=3200,
    height=1800,
    title="indicator-sma · python · bokeh · anyplot.ai",
    x_axis_label=DATE,
    y_axis_label=CLOSE,
    x_axis_type="datetime",
    tools="pan,wheel_zoom,box_zoom,reset,save",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

close_line = p.line(x=DATE, y=CLOSE, source=source, line_width=6, color=IMPRINT_PALETTE[0])
legend_items = [(CLOSE, [close_line])]
for i, column in enumerate(sma_columns):
    line = p.line(
        x=DATE, y=column, source=source, line_width=5, color=IMPRINT_PALETTE[i + 1], alpha=0.95, line_dash=SMA_DASHES[i]
    )
    legend_items.append((column, [line]))

# HoverTool for exact values on mouseover
hover = HoverTool(
    tooltips=[
        (DATE, f"@{{{DATE}}}{{%F}}"),
        (CLOSE, f"@{{{CLOSE}}}{{$0.2f}}"),
        (SMA_SHORT, f"@{{{SMA_SHORT}}}{{$0.2f}}"),
        (SMA_MEDIUM, f"@{{{SMA_MEDIUM}}}{{$0.2f}}"),
        (SMA_LONG, f"@{{{SMA_LONG}}}{{$0.2f}}"),
    ],
    formatters={f"@{{{DATE}}}": "datetime"},
    mode="vline",
)
p.add_tools(hover)

# Legend
legend = Legend(items=legend_items, location="top_left")
p.add_layout(legend)
p.legend.label_text_font_size = "34pt"
p.legend.glyph_width = 90
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT

# Chrome
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

p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

# Save HTML then screenshot with headless Chrome
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
