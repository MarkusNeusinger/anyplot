""" anyplot.ai
line-navigator: Line Chart with Mini Navigator
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-27
"""

import io
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, HoverTool, RangeTool
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
BRAND = "#009E73"  # anyplot palette position 1 — ALWAYS first series
ANYPLOT_AMBER = "#DDCC77"  # selection highlight (semantic anchor)

# Data — daily sensor readings over 3 years (1095 points)
np.random.seed(42)
n_points = 1095
dates = pd.date_range(start="2022-01-01", periods=n_points, freq="D")

trend = np.linspace(50, 80, n_points)
seasonal = 15 * np.sin(2 * np.pi * np.arange(n_points) / 365)
noise = np.random.randn(n_points) * 5
values = trend + seasonal + noise

source = ColumnDataSource(data={"date": dates, "value": values})

title = "line-navigator · python · bokeh · anyplot.ai"

# Main chart — shows selected range in detail
main_plot = figure(
    width=3200,
    height=1500,
    title=title,
    x_axis_type="datetime",
    x_axis_label="Date",
    y_axis_label="Sensor Reading (units)",
    x_range=(dates[700], dates[900]),
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

main_plot.line("date", "value", source=source, line_width=4, line_color=BRAND, alpha=0.9)

hover = HoverTool(tooltips=[("Date", "@date{%F}"), ("Reading", "@value{0.1f} units")], formatters={"@date": "datetime"})
main_plot.add_tools(hover)

# Theme-adaptive chrome — main plot
main_plot.background_fill_color = PAGE_BG
main_plot.border_fill_color = PAGE_BG
main_plot.outline_line_color = INK_SOFT
main_plot.title.text_font_size = "50pt"
main_plot.title.text_color = INK
main_plot.xaxis.axis_label_text_font_size = "42pt"
main_plot.yaxis.axis_label_text_font_size = "42pt"
main_plot.xaxis.axis_label_text_color = INK
main_plot.yaxis.axis_label_text_color = INK
main_plot.xaxis.major_label_text_font_size = "34pt"
main_plot.yaxis.major_label_text_font_size = "34pt"
main_plot.xaxis.major_label_text_color = INK_SOFT
main_plot.yaxis.major_label_text_color = INK_SOFT
main_plot.xaxis.axis_line_color = INK_SOFT
main_plot.yaxis.axis_line_color = INK_SOFT
main_plot.xaxis.major_tick_line_color = INK_SOFT
main_plot.yaxis.major_tick_line_color = INK_SOFT
main_plot.xgrid.grid_line_color = INK
main_plot.ygrid.grid_line_color = INK
main_plot.xgrid.grid_line_alpha = 0.15
main_plot.ygrid.grid_line_alpha = 0.15

# Navigator — shows full data extent at reduced scale
navigator = figure(
    width=3200,
    height=300,
    x_axis_type="datetime",
    y_axis_type=None,
    y_range=main_plot.y_range,
    toolbar_location=None,
    min_border_bottom=100,
    min_border_left=180,
    min_border_top=30,
    min_border_right=50,
)

navigator.line("date", "value", source=source, line_width=2, line_color=BRAND, alpha=0.6)

range_tool = RangeTool(x_range=main_plot.x_range)
range_tool.overlay.fill_color = ANYPLOT_AMBER
range_tool.overlay.fill_alpha = 0.3
navigator.add_tools(range_tool)

# Theme-adaptive chrome — navigator
navigator.background_fill_color = PAGE_BG
navigator.border_fill_color = PAGE_BG
navigator.outline_line_color = INK_SOFT
navigator.xaxis.major_label_text_font_size = "28pt"
navigator.xaxis.major_label_text_color = INK_SOFT
navigator.xaxis.axis_line_color = INK_SOFT
navigator.xaxis.major_tick_line_color = INK_SOFT
navigator.ygrid.grid_line_color = INK
navigator.ygrid.grid_line_alpha = 0.15

# Layout — total canvas 3200 × 1800
layout = column(main_plot, navigator, sizing_mode="fixed", spacing=0, width=3200, height=1800)

# Save HTML (required catalog artifact)
output_file(f"plot-{THEME}.html")
save(layout)

# Screenshot with headless Chrome — Selenium Manager resolves the driver.
# Chrome's inner viewport is ~139px shorter than the requested window height,
# so request a larger window and crop the PNG to the exact target dimensions.
W, H = 3200, 1800
WIN_W, WIN_H = W, H + 200  # overshoot so viewport comfortably contains W×H content
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={WIN_W},{WIN_H}",
    "--hide-scrollbars",
    "--force-device-scale-factor=1",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.set_window_size(WIN_W, WIN_H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)
png_bytes = driver.get_screenshot_as_png()
driver.quit()
img = Image.open(io.BytesIO(png_bytes)).crop((0, 0, W, H))
img.save(f"plot-{THEME}.png")
