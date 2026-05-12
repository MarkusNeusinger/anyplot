"""anyplot.ai
line-filled: Filled Line Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Updated: 2026-05-12
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data - Monthly website traffic over a year
np.random.seed(42)
months = np.arange(1, 13)
# Simulate traffic with seasonal trend (higher in summer/winter holidays)
base_traffic = 50000
seasonal = 15000 * np.sin(2 * np.pi * (months - 3) / 12)  # Peak in summer
trend = 2000 * months  # Gradual growth
noise = np.random.normal(0, 3000, 12)
traffic = base_traffic + seasonal + trend + noise
traffic = np.maximum(traffic, 0)  # Ensure positive values

# Create ColumnDataSource
source = ColumnDataSource(data={"month": months, "traffic": traffic, "traffic_zero": np.zeros(len(months))})

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="line-filled · bokeh · anyplot.ai",
    x_axis_label="Month",
    y_axis_label="Website Visitors (count)",
)

# Filled area using varea
p.varea(x="month", y1="traffic_zero", y2="traffic", source=source, fill_color=BRAND, fill_alpha=0.35)

# Line on top of the fill
p.line(x="month", y="traffic", source=source, line_color=BRAND, line_width=4)

# Add points for visual emphasis
p.scatter(x="month", y="traffic", source=source, size=12, color=BRAND, fill_alpha=0.8)

# Add hover tool
hover = HoverTool(tooltips=[("Month", "@month"), ("Visitors", "@traffic{0,0}")])
p.add_tools(hover)

# Styling for large canvas
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Theme-adaptive text colors
p.title.text_color = INK
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

# Grid styling
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK

# Axis styling
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# Background
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# X-axis ticks for each month
p.xaxis.ticker = list(range(1, 13))

# Save as interactive HTML
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
time.sleep(3)  # Let bokeh's JS render the canvas
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
