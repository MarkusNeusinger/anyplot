""" anyplot.ai
bar-error: Bar Chart with Error Bars
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-10
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, TeeHead, Whisker
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - Quarterly revenue by product line with standard deviation
np.random.seed(42)
categories = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books"]
values = np.array([85.2, 62.8, 48.5, 71.3, 35.7])
errors = np.array([8.5, 5.2, 6.8, 9.1, 4.2])

# Calculate upper and lower bounds
upper = values + errors
lower = values - errors

# Create ColumnDataSource
source = ColumnDataSource(data={"categories": categories, "values": values, "upper": upper, "lower": lower})

# Create figure
p = figure(
    x_range=categories,
    width=4800,
    height=2700,
    title="bar-error · bokeh · anyplot.ai",
    x_axis_label="Product Category",
    y_axis_label="Quarterly Revenue ($ millions)",
    toolbar_location=None,
)

# Draw bars
p.vbar(
    x="categories",
    top="values",
    width=0.6,
    source=source,
    fill_color=BRAND,
    line_color=BRAND,
    line_width=3,
    fill_alpha=0.85,
)

# Add error bars with whiskers and caps
whisker = Whisker(
    source=source,
    base="categories",
    upper="upper",
    lower="lower",
    line_color=INK_SOFT,
    line_width=5,
    upper_head=TeeHead(size=40, line_color=INK_SOFT, line_width=5),
    lower_head=TeeHead(size=40, line_color=INK_SOFT, line_width=5),
)
p.add_layout(whisker)

# Style
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

# Axis styling
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.major_tick_line_width = 2
p.yaxis.major_tick_line_width = 2

# Grid
p.xgrid.visible = False
p.ygrid.grid_line_color = INK_SOFT
p.ygrid.grid_line_alpha = 0.10
p.ygrid.grid_line_width = 1

# Background
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Y-axis range
p.y_range.start = 0
p.y_range.end = max(upper) + 15

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
