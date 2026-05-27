""" anyplot.ai
candlestick-volume: Stock Candlestick Chart with Volume
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-16
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
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette for up/down
COLOR_UP = "#009E73"  # Green (Okabe-Ito position 1)
COLOR_DOWN = "#AE3030"  # imprint red — down days

# Data - Generate 60 trading days of OHLC with volume
np.random.seed(42)
n_days = 60

# Generate realistic stock price data
dates = pd.date_range(start="2024-06-01", periods=n_days, freq="B")  # Business days
dates_str = [d.strftime("%Y-%m-%d") for d in dates]

# Start price and random walk
start_price = 150.0
returns = np.random.normal(0.001, 0.02, n_days)
close_prices = start_price * np.cumprod(1 + returns)

# Generate OHLC from close prices
open_prices = np.roll(close_prices, 1)
open_prices[0] = start_price
high_prices = np.maximum(open_prices, close_prices) * (1 + np.abs(np.random.normal(0, 0.01, n_days)))
low_prices = np.minimum(open_prices, close_prices) * (1 - np.abs(np.random.normal(0, 0.01, n_days)))

# Volume - higher on big price moves
base_volume = 2_000_000
price_change = np.abs(close_prices - open_prices) / open_prices
volume = base_volume * (1 + price_change * 20) * np.random.uniform(0.7, 1.3, n_days)
volume = volume.astype(int)

# Determine up/down days
is_up = close_prices >= open_prices
colors = [COLOR_UP if up else COLOR_DOWN for up in is_up]

# Create DataFrame
df = pd.DataFrame(
    {
        "date": dates_str,
        "open": open_prices,
        "high": high_prices,
        "low": low_prices,
        "close": close_prices,
        "volume": volume,
        "color": colors,
        "is_up": is_up,
    }
)

# Create ColumnDataSource
source = ColumnDataSource(df)

# Create candlestick chart (top pane - 70% height)
p_candle = figure(
    width=4800,
    height=1890,  # 70% of 2700
    x_range=dates_str,
    title="candlestick-volume · bokeh · anyplot.ai",
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

# Add candlestick wicks (high-low lines)
p_candle.segment(x0="date", y0="high", x1="date", y1="low", source=source, line_color="color", line_width=2)

# Add candlestick bodies (rectangles)
candle_width = 0.6
p_candle.vbar(
    x="date",
    top="close",
    bottom="open",
    width=candle_width,
    source=source,
    fill_color="color",
    line_color="color",
    line_width=1,
)

# Add hover tool to candlestick
hover_candle = HoverTool(
    tooltips=[
        ("Date", "@date"),
        ("Open", "$@open{0.00}"),
        ("High", "$@high{0.00}"),
        ("Low", "$@low{0.00}"),
        ("Close", "$@close{0.00}"),
    ]
)
p_candle.add_tools(hover_candle)

# Style candlestick chart - theme-adaptive
p_candle.background_fill_color = PAGE_BG
p_candle.border_fill_color = PAGE_BG
p_candle.outline_line_color = INK_SOFT

p_candle.title.text_font_size = "28pt"
p_candle.title.text_color = INK

p_candle.yaxis.axis_label = "Price ($)"
p_candle.yaxis.axis_label_text_font_size = "22pt"
p_candle.yaxis.axis_label_text_color = INK
p_candle.yaxis.major_label_text_font_size = "18pt"
p_candle.yaxis.major_label_text_color = INK_SOFT
p_candle.yaxis.axis_line_color = INK_SOFT
p_candle.yaxis.major_tick_line_color = INK_SOFT

p_candle.xaxis.major_label_text_font_size = "18pt"
p_candle.xaxis.major_label_text_color = INK_SOFT
p_candle.xaxis.axis_line_color = INK_SOFT
p_candle.xaxis.major_tick_line_color = INK_SOFT
p_candle.xaxis.major_label_orientation = 0.8
p_candle.xaxis.visible = False  # Hide x-axis on top chart (shared with volume)

p_candle.xgrid.grid_line_color = INK
p_candle.ygrid.grid_line_color = INK
p_candle.xgrid.grid_line_alpha = 0.10
p_candle.ygrid.grid_line_alpha = 0.10

p_candle.min_border_left = 120
p_candle.min_border_right = 60

# Create volume chart (bottom pane - 30% height)
p_volume = figure(
    width=4800,
    height=810,  # 30% of 2700
    x_range=p_candle.x_range,  # Share x-range with candlestick
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

# Add volume bars
p_volume.vbar(
    x="date",
    top="volume",
    width=candle_width,
    source=source,
    fill_color="color",
    line_color="color",
    fill_alpha=1.0,
    line_width=1,
)

# Add hover tool to volume
hover_volume = HoverTool(tooltips=[("Date", "@date"), ("Volume", "@volume{0,0}")])
p_volume.add_tools(hover_volume)

# Style volume chart - theme-adaptive
p_volume.background_fill_color = PAGE_BG
p_volume.border_fill_color = PAGE_BG
p_volume.outline_line_color = INK_SOFT

p_volume.yaxis.axis_label = "Volume"
p_volume.yaxis.axis_label_text_font_size = "22pt"
p_volume.yaxis.axis_label_text_color = INK
p_volume.yaxis.major_label_text_font_size = "18pt"
p_volume.yaxis.major_label_text_color = INK_SOFT
p_volume.yaxis.axis_line_color = INK_SOFT
p_volume.yaxis.major_tick_line_color = INK_SOFT

p_volume.xaxis.axis_label = "Date"
p_volume.xaxis.axis_label_text_font_size = "22pt"
p_volume.xaxis.axis_label_text_color = INK
p_volume.xaxis.major_label_text_font_size = "18pt"
p_volume.xaxis.major_label_text_color = INK_SOFT
p_volume.xaxis.axis_line_color = INK_SOFT
p_volume.xaxis.major_tick_line_color = INK_SOFT
p_volume.xaxis.major_label_orientation = 0.8

p_volume.xgrid.grid_line_color = INK
p_volume.ygrid.grid_line_color = INK
p_volume.xgrid.grid_line_alpha = 0.10
p_volume.ygrid.grid_line_alpha = 0.10

p_volume.min_border_left = 120
p_volume.min_border_right = 60

# Format volume y-axis to show millions
p_volume.yaxis.formatter = NumeralTickFormatter(format="0.0a")

# Add linked crosshair tool to both charts
crosshair_candle = CrosshairTool(dimensions="both", line_color=INK_SOFT, line_alpha=0.5, line_width=2)
crosshair_volume = CrosshairTool(dimensions="both", line_color=INK_SOFT, line_alpha=0.5, line_width=2)
p_candle.add_tools(crosshair_candle)
p_volume.add_tools(crosshair_volume)

# Combine charts in vertical layout
layout = column(p_candle, p_volume)

# Save as HTML
output_file(f"plot-{THEME}.html")
save(layout)

# Screenshot with headless Chrome using Selenium
W, H = 4800, 2700
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
time.sleep(3)  # let bokeh's JS render the canvas
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
