""" anyplot.ai
area-basic: Basic Area Chart
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-26
"""

import io
import os
import sys
import time
from pathlib import Path


# Prevent this file's directory from shadowing the installed bokeh package
sys.path = [p for p in sys.path if os.path.abspath(p) != os.path.dirname(os.path.abspath(__file__))]

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Range1d
from bokeh.plotting import figure
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1 — always first series

# Constants
TITLE = "Daily Website Traffic · area-basic · python · bokeh · anyplot.ai"

# Columns: set these to your table's column names
DATE = "Date (March 2024)"  # role: x
VISITORS = "Daily Visitors (count)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("traffic.csv")
np.random.seed(42)
dates = pd.date_range(start="2024-03-01", periods=31, freq="D")
visitors = (
    4200 + np.linspace(0, 800, 31) + 600 * np.sin(np.arange(31) * 2 * np.pi / 7 - 1.2) + np.random.randn(31) * 300
)
visitors = np.maximum(visitors, 1800)
visitors[7:9] = [2100, 2400]  # scheduled maintenance
visitors[21:24] = [11400, 9900, 7700]  # tutorial hits the Hacker News front page
df = pd.DataFrame({DATE: dates, VISITORS: visitors})

# Plot: reads only df and the constants above
n = len(TITLE)
ratio = 67 / n if n > 67 else 1.0
title_fontsize = f"{max(34, round(50 * ratio))}pt"
source = ColumnDataSource(df)

# Figure — 3200×1800 landscape
p = figure(
    width=3200,
    height=1800,
    title=TITLE,
    x_axis_label=DATE,
    y_axis_label=VISITORS,
    x_axis_type="datetime",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Area fill + edge line
p.varea(x=DATE, y1=0, y2=VISITORS, source=source, fill_color=BRAND, fill_alpha=0.35)
p.line(x=DATE, y=VISITORS, source=source, line_color=BRAND, line_width=4)

# Invisible scatter for hover hit targets
p.scatter(x=DATE, y=VISITORS, source=source, size=18, fill_alpha=0, line_alpha=0)

# HoverTool with datetime formatter
hover = HoverTool(
    tooltips=[("Date", f"@{{{DATE}}}{{%b %d, %Y}}"), ("Visitors", f"@{{{VISITORS}}}{{0,0}}")],
    formatters={f"@{{{DATE}}}": "datetime"},
    mode="vline",
)
p.add_tools(hover)

# Text sizing — canonical bokeh values for 3200×1800
p.title.text_font_size = title_fontsize
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_font_style = "normal"
p.yaxis.axis_label_text_font_style = "normal"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.title.text_color = INK
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# Grid — subtle, y-axis only for area chart
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.15

# Area baseline at zero, headroom from the data
p.y_range = Range1d(0, df[VISITORS].max() * 1.08)

# Save HTML (interactive catalog artifact)
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome (Selenium 4 / Selenium Manager).
# Chrome's internal UI overhead shrinks the viewport below --window-size by ~139 px.
# Use a taller window (H + 200 buffer) so the viewport is >= H, then crop to exact dims.
W, H = 3200, 1800
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H + 200}",
    "--hide-scrollbars",
    "--force-device-scale-factor=1",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, H + 200)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)
raw = driver.get_screenshot_as_png()
driver.quit()
img = Image.open(io.BytesIO(raw)).crop((0, 0, W, H))
img.save(f"plot-{THEME}.png")
