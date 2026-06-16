""" anyplot.ai
line-timeseries-rolling: Time Series with Rolling Average Overlay
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-13
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

IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - Simulated daily stock prices with 20-day rolling average
np.random.seed(42)
n_days = 250
dates = pd.date_range("2024-01-01", periods=n_days, freq="D")

# Create realistic stock price data with trend and volatility
trend = np.linspace(100, 120, n_days)
noise = np.random.normal(0, 3, n_days)
prices = trend + noise

# Calculate 20-day rolling average
rolling_window = 20
rolling_avg = pd.Series(prices).rolling(window=rolling_window, center=True).mean()

# Create DataFrame
df = pd.DataFrame({"date": dates, "price": prices, "rolling_avg": rolling_avg})

# Create ColumnDataSource for raw data
source_raw = ColumnDataSource(data={"date": df["date"], "price": df["price"]})

# Create ColumnDataSource for rolling average (exclude NaN values)
df_rolling = df.dropna(subset=["rolling_avg"])
source_rolling = ColumnDataSource(data={"date": df_rolling["date"], "rolling_avg": df_rolling["rolling_avg"]})

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="line-timeseries-rolling · bokeh · anyplot.ai",
    x_axis_label="Date",
    y_axis_label="Stock Price ($)",
    x_axis_type="datetime",
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

# Plot raw data - thin line with transparency
p.line(
    x="date",
    y="price",
    source=source_raw,
    line_width=2,
    line_alpha=0.4,
    line_color=IMPRINT[0],
    legend_label="Raw Data",
)

# Plot rolling average - prominent smooth line
p.line(
    x="date",
    y="rolling_avg",
    source=source_rolling,
    line_width=4,
    line_color=IMPRINT[1],
    legend_label=f"{rolling_window}-Day Rolling Average",
)

# Styling for large canvas
p.title.text_font_size = "28pt"
p.title.text_color = INK

p.xaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_color = INK

p.xaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_color = INK_SOFT

p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# Grid styling - subtle
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.15
p.ygrid.grid_line_alpha = 0.15

# Background
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Legend styling
p.legend.label_text_font_size = "18pt"
p.legend.label_text_color = INK_SOFT
p.legend.location = "top_left"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT

# Save as HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome — Selenium 4 / Selenium Manager auto-resolves
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
