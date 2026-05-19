"""anyplot.ai
indicator-sma: Simple Moving Average (SMA) Indicator Chart
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-05-19
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

# Okabe-Ito palette (positions 1-4)
COLOR_CLOSE = "#009E73"  # brand green — close price (first series)
COLOR_SMA20 = "#D55E00"  # vermillion
COLOR_SMA50 = "#0072B2"  # blue
COLOR_SMA200 = "#CC79A7"  # reddish purple

# Data — engineered to produce visible golden cross / death cross signals
np.random.seed(42)
n_days = 300
dates = pd.date_range(start="2024-01-01", periods=n_days, freq="B")
returns = np.concatenate(
    [np.random.normal(0.001, 0.012, 100), np.random.normal(-0.002, 0.015, 80), np.random.normal(0.003, 0.013, 120)]
)
price = 100 * np.exp(np.cumsum(returns))

df = pd.DataFrame({"date": dates, "close": price})
df["sma_20"] = df["close"].rolling(window=20).mean()
df["sma_50"] = df["close"].rolling(window=50).mean()
df["sma_200"] = df["close"].rolling(window=200).mean()

source = ColumnDataSource(df)

# Plot
p = figure(
    width=4800,
    height=2700,
    title="indicator-sma · python · bokeh · anyplot.ai",
    x_axis_label="Date",
    y_axis_label="Price ($)",
    x_axis_type="datetime",
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

close_line = p.line(x="date", y="close", source=source, line_width=3, color=COLOR_CLOSE, alpha=0.9)
sma20_line = p.line(x="date", y="sma_20", source=source, line_width=3, color=COLOR_SMA20, alpha=0.9)
sma50_line = p.line(x="date", y="sma_50", source=source, line_width=3, color=COLOR_SMA50, alpha=0.9)
sma200_line = p.line(x="date", y="sma_200", source=source, line_width=3, color=COLOR_SMA200, alpha=0.9)

# HoverTool for exact values on mouseover
hover = HoverTool(
    tooltips=[
        ("Date", "@date{%F}"),
        ("Close", "@close{$0.2f}"),
        ("SMA 20", "@sma_20{$0.2f}"),
        ("SMA 50", "@sma_50{$0.2f}"),
        ("SMA 200", "@sma_200{$0.2f}"),
    ],
    formatters={"@date": "datetime"},
    mode="vline",
)
p.add_tools(hover)

# Legend
legend = Legend(
    items=[
        ("Close Price", [close_line]),
        ("SMA 20", [sma20_line]),
        ("SMA 50", [sma50_line]),
        ("SMA 200", [sma200_line]),
    ],
    location="top_left",
)
p.add_layout(legend)
p.legend.label_text_font_size = "22pt"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT

# Chrome
p.title.text_font_size = "28pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Save HTML then screenshot with headless Chrome
output_file(f"plot-{THEME}.html")
save(p)

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
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
