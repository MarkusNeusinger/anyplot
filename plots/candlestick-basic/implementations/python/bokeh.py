"""anyplot.ai
candlestick-basic: Basic Candlestick Chart
Library: bokeh 3.10.2 | Python 3.14.10
Quality: pending | Updated: 2026-11-27
"""

import os
import sys
import time
from pathlib import Path


# Remove this file's directory from sys.path so `import bokeh` resolves
# the installed package rather than this file (bokeh.py).
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _here]

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, NumeralTickFormatter, Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — semantic exception for finance: up=green, down=red
COLOR_BULL = "#009E73"  # Imprint position 1 — bullish (gain/up)
COLOR_BEAR = "#AE3030"  # Imprint position 5 — bearish (loss/down)

# Column names, written the way the axis titles read
DATE = "date"  # role: date
OPEN = "open"  # role: open
HIGH = "high"  # role: high
LOW = "low"  # role: low
CLOSE = "close"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv", parse_dates=["date"])
np.random.seed(42)
n_days = 30
start_price = 150.0
dates = pd.date_range(start="2024-01-02", periods=n_days, freq="B")

returns = np.random.randn(n_days) * 0.018
returns[:10] -= 0.002
returns[10:20] -= 0.005
returns[20:] += 0.008
prices = start_price * np.cumprod(1 + returns)

open_prices = []
high_prices = []
low_prices = []
close_prices = []

for i, close in enumerate(prices):
    if i == 0:
        open_price = start_price
    else:
        open_price = close_prices[-1]
    daily_range = abs(np.random.randn()) * 0.012 * close
    high = max(open_price, close) + daily_range
    low = min(open_price, close) - daily_range
    open_prices.append(open_price)
    high_prices.append(high)
    low_prices.append(low)
    close_prices.append(close)

df = pd.DataFrame({DATE: dates, OPEN: open_prices, HIGH: high_prices, LOW: low_prices, CLOSE: close_prices})

# Plot
bullish_df = df[df[CLOSE] >= df[OPEN]]
bearish_df = df[df[CLOSE] < df[OPEN]]
source_bullish = ColumnDataSource(bullish_df)
source_bearish = ColumnDataSource(bearish_df)

# Figure — 3200×1800 landscape; reserved borders for 42pt axis labels
title = "Northwind (NWLG) · candlestick-basic · python · bokeh · anyplot.ai"
p = figure(
    width=3200,
    height=1800,
    x_axis_type="datetime",
    title=title,
    x_axis_label="Date",
    y_axis_label="Price (USD)",
    tools="",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Tighten x-range
step = df[DATE].diff().median()
p.x_range = Range1d(start=df[DATE].min() - step, end=df[DATE].max() + step)

# Candle width — 75% of the typical period, in milliseconds
candle_width = 0.75 * step.total_seconds() * 1000

# Wicks — colored to match candle bodies, visibly thinner than bodies
p.segment(x0=DATE, y0=HIGH, x1=DATE, y1=LOW, source=source_bullish, color=COLOR_BULL, line_width=3)
p.segment(x0=DATE, y0=HIGH, x1=DATE, y1=LOW, source=source_bearish, color=COLOR_BEAR, line_width=3)

# Candle bodies
bull_bars = p.vbar(
    x=DATE,
    top=CLOSE,
    bottom=OPEN,
    width=candle_width,
    source=source_bullish,
    fill_color=COLOR_BULL,
    line_color=COLOR_BULL,
    line_width=1,
    legend_label="Bullish",
)
bear_bars = p.vbar(
    x=DATE,
    top=OPEN,
    bottom=CLOSE,
    width=candle_width,
    source=source_bearish,
    fill_color=PAGE_BG,  # hollow body — CVD-safe: solid=bullish, hollow=bearish
    line_color=COLOR_BEAR,
    line_width=3,
    legend_label="Bearish",
)

# Hover tooltips — Bokeh interactive feature
hover = HoverTool(
    renderers=[bull_bars, bear_bars],
    tooltips=[
        ("Date", f"@{DATE}{{%b %d, %Y}}"),
        ("Open", f"@{OPEN}{{$0.00}}"),
        ("High", f"@{HIGH}{{$0.00}}"),
        ("Low", f"@{LOW}{{$0.00}}"),
        ("Close", f"@{CLOSE}{{$0.00}}"),
    ],
    formatters={f"@{DATE}": "datetime"},
    mode="vline",
)
p.add_tools(hover)

# Typography — 3200×1800 sizing (title 65 chars → full 50pt)
p.title.text_font_size = "50pt"
p.title.text_font_style = "normal"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

# Y-axis dollar formatting
p.yaxis.formatter = NumeralTickFormatter(format="$0")

# Grid — y-axis only, subtle
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.15
p.ygrid.grid_line_width = 1

# Axis chrome — theme-adaptive, minimalist
p.outline_line_color = None
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Background — Imprint warm surface
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG

# Legend — bull/bear guide for viewers unfamiliar with candlestick conventions
p.legend.location = "top_left"
p.legend.label_text_font_size = "34pt"
p.legend.glyph_height = 40
p.legend.glyph_width = 40
p.legend.label_standoff = 16
p.legend.label_text_color = INK_SOFT
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.margin = 20
p.legend.padding = 20
p.legend.spacing = 12

# Save HTML (interactive with hover tooltips)
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome — Selenium 4 / Selenium Manager
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
driver.execute_script(
    "document.documentElement.style.background = arguments[0]; document.body.style.background = arguments[0];", PAGE_BG
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
