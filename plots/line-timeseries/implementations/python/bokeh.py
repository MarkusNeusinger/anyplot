""" anyplot.ai
line-timeseries: Time Series Line Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-09
"""

import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Fix name collision: temporarily remove local directory from sys.path
_local_path = str(Path.cwd())
_sys_path_backup = sys.path.copy()
sys.path = [p for p in sys.path if p != "" and p != "." and p != _local_path]

from bokeh.io import output_file, save  # noqa: E402
from bokeh.models import ColumnDataSource  # noqa: E402
from bokeh.plotting import figure  # noqa: E402


sys.path = _sys_path_backup

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - Stock price simulation over one year
np.random.seed(42)
dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
n_points = len(dates)

# Simulate stock price with trend, seasonality, and noise
base_price = 150
trend = np.linspace(0, 30, n_points)
seasonality = 10 * np.sin(np.linspace(0, 4 * np.pi, n_points))
noise = np.cumsum(np.random.randn(n_points) * 0.8)
prices = base_price + trend + seasonality + noise
prices = np.maximum(prices, 50)

source = ColumnDataSource(data={"date": dates, "price": prices})

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="line-timeseries · bokeh · anyplot.ai",
    x_axis_label="Date",
    y_axis_label="Stock Price (USD)",
    x_axis_type="datetime",
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

# Plot the line
p.line(x="date", y="price", source=source, line_width=3, line_color=BRAND, legend_label="Stock Price")

# Styling - text sizes for 4800x2700 px canvas
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

# Grid styling
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK

# Legend styling
p.legend.location = "top_left"
p.legend.label_text_font_size = "18pt"
p.legend.label_text_color = INK_SOFT
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.border_line_width = 1
p.legend.glyph_height = 25
p.legend.glyph_width = 40

# Axis styling
p.xaxis.major_label_orientation = 0.8
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# Background
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome
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
