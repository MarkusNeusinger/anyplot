"""anyplot.ai
candlestick-basic: Basic Candlestick Chart
Library: bokeh | Python 3.14
Quality: 90/100 | Updated: 2026-05-30
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
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — semantic exception for finance: up=green, down=red
COLOR_BULL = "#009E73"  # Imprint position 1 — bullish (gain/up)
COLOR_BEAR = "#AE3030"  # Imprint position 5 — bearish (loss/down)

# Data — 30 trading days of OHLC data for ACME Corp
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

df = pd.DataFrame({"date": dates, "open": open_prices, "high": high_prices, "low": low_prices, "close": close_prices})
df["bullish"] = df["close"] >= df["open"]
df["date_str"] = df["date"].dt.strftime("%b %d, %Y")

bullish_df = df[df["bullish"]].copy()
bearish_df = df[~df["bullish"]].copy()
source_bullish = ColumnDataSource(bullish_df)
source_bearish = ColumnDataSource(bearish_df)

# Figure — 3200×1800 landscape; reserved borders for 42pt axis labels
title = "ACME Corp Stock · candlestick-basic · python · bokeh · anyplot.ai"
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
x_pad = pd.Timedelta(days=1)
p.x_range = Range1d(start=dates[0] - x_pad, end=dates[-1] + x_pad)

# Candle width — 75% of one business day in milliseconds
candle_width = 0.75 * 24 * 60 * 60 * 1000

# Wicks — colored to match candle bodies, visibly thinner than bodies
p.segment(x0="date", y0="high", x1="date", y1="low", source=source_bullish, color=COLOR_BULL, line_width=3)
p.segment(x0="date", y0="high", x1="date", y1="low", source=source_bearish, color=COLOR_BEAR, line_width=3)

# Candle bodies
bull_bars = p.vbar(
    x="date",
    top="close",
    bottom="open",
    width=candle_width,
    source=source_bullish,
    fill_color=COLOR_BULL,
    line_color=COLOR_BULL,
    line_width=1,
)
bear_bars = p.vbar(
    x="date",
    top="open",
    bottom="close",
    width=candle_width,
    source=source_bearish,
    fill_color=COLOR_BEAR,
    line_color=COLOR_BEAR,
    line_width=1,
)

# Hover tooltips — Bokeh interactive feature
hover = HoverTool(
    renderers=[bull_bars, bear_bars],
    tooltips=[
        ("Date", "@date_str"),
        ("Open", "@open{$0.00}"),
        ("High", "@high{$0.00}"),
        ("Low", "@low{$0.00}"),
        ("Close", "@close{$0.00}"),
    ],
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
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
