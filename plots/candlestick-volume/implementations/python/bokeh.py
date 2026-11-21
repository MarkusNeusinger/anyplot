""" anyplot.ai
candlestick-volume: Stock Candlestick Chart with Volume
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-21
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, CrosshairTool, HoverTool, NumeralTickFormatter
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
COLOR_UP = IMPRINT_PALETTE[0]  # brand green: up days
COLOR_DOWN = IMPRINT_PALETTE[4]  # imprint red: down days

# Columns: set these to your table's column names
DATE = "Date"  # role: date
OPEN = "Open (USD)"  # role: open
HIGH = "High (USD)"  # role: high
LOW = "Low (USD)"  # role: low
CLOSE = "Close (USD)"  # role: close
VOLUME = "Volume (shares)"  # role: volume

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv", parse_dates=["Date"])
np.random.seed(42)
n_days = 60
dates = pd.date_range(start="2024-06-01", periods=n_days, freq="B")
returns = np.random.normal(0.001, 0.02, n_days)
close_prices = 150.0 * np.cumprod(1 + returns)
open_prices = np.roll(close_prices, 1)
open_prices[0] = 150.0
high_prices = np.maximum(open_prices, close_prices) * (1 + np.abs(np.random.normal(0, 0.01, n_days)))
low_prices = np.minimum(open_prices, close_prices) * (1 - np.abs(np.random.normal(0, 0.01, n_days)))
price_change = np.abs(close_prices - open_prices) / open_prices
volume = (2_000_000 * (1 + price_change * 20) * np.random.uniform(0.7, 1.3, n_days)).astype(int)
df = pd.DataFrame(
    {DATE: dates, OPEN: open_prices, HIGH: high_prices, LOW: low_prices, CLOSE: close_prices, VOLUME: volume}
)

# Plot: reads only df and the constants above
df = df.assign(color=np.where(df[CLOSE] >= df[OPEN], COLOR_UP, COLOR_DOWN))
source = ColumnDataSource(df)
bar_width = pd.Timedelta(days=0.7) / pd.Timedelta(milliseconds=1)  # bokeh datetime widths are in ms

W, H = 3200, 1800
price_height = round(H * 0.72)
volume_height = H - price_height
tools = "pan,wheel_zoom,box_zoom,reset,save"

p_candle = figure(
    width=W,
    height=price_height,
    x_axis_type="datetime",
    title="candlestick-volume · python · bokeh · anyplot.ai",
    tools=tools,
    toolbar_location=None,
    min_border_left=260,
    min_border_right=60,
    min_border_top=110,
    min_border_bottom=20,
)
p_candle.segment(x0=DATE, y0=HIGH, x1=DATE, y1=LOW, source=source, line_color="color", line_width=3)
p_candle.vbar(
    x=DATE, top=CLOSE, bottom=OPEN, width=bar_width, source=source, fill_color="color", line_color="color", line_width=1
)
p_candle.add_tools(
    HoverTool(
        tooltips=[
            (DATE, f"@{{{DATE}}}{{%F}}"),
            ("Open", f"$@{{{OPEN}}}{{0.00}}"),
            ("High", f"$@{{{HIGH}}}{{0.00}}"),
            ("Low", f"$@{{{LOW}}}{{0.00}}"),
            ("Close", f"$@{{{CLOSE}}}{{0.00}}"),
        ],
        formatters={f"@{{{DATE}}}": "datetime"},
    )
)

p_volume = figure(
    width=W,
    height=volume_height,
    x_axis_type="datetime",
    x_range=p_candle.x_range,
    tools=tools,
    toolbar_location=None,
    min_border_left=260,
    min_border_right=60,
    min_border_top=20,
    min_border_bottom=150,
)
p_volume.vbar(x=DATE, top=VOLUME, width=bar_width, source=source, fill_color="color", line_color="color")
p_volume.add_tools(
    HoverTool(
        tooltips=[(DATE, f"@{{{DATE}}}{{%F}}"), ("Volume", f"@{{{VOLUME}}}{{0,0}}")],
        formatters={f"@{{{DATE}}}": "datetime"},
    )
)
p_volume.y_range.start = 0
p_volume.yaxis.formatter = NumeralTickFormatter(format="0.0a")

# Style: theme-adaptive chrome shared by both panes
for p in (p_candle, p_volume):
    p.background_fill_color = PAGE_BG
    p.border_fill_color = PAGE_BG
    p.outline_line_color = INK_SOFT
    p.axis.axis_label_text_font_size = "36pt"
    p.axis.axis_label_text_color = INK
    p.axis.major_label_text_font_size = "30pt"
    p.axis.major_label_text_color = INK_SOFT
    p.axis.axis_line_color = INK_SOFT
    p.axis.major_tick_line_color = INK_SOFT
    p.axis.minor_tick_line_color = None
    p.grid.grid_line_color = INK
    p.grid.grid_line_alpha = 0.10
    p.add_tools(CrosshairTool(dimensions="both", line_color=INK_SOFT, line_alpha=0.5, line_width=2))

p_candle.title.text_font_size = "50pt"
p_candle.title.text_color = INK
p_candle.xaxis.visible = False  # the x-axis is shared with the volume pane below
p_candle.yaxis.axis_label = "Price (USD)"
p_volume.yaxis.axis_label = VOLUME
p_volume.xaxis.axis_label = DATE

layout = column(p_candle, p_volume)

# Save as HTML, then screenshot with headless Chrome
output_file(f"plot-{THEME}.html")
save(layout)

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
time.sleep(3)  # let bokeh's JS render the canvas
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
