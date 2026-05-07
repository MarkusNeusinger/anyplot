""" anyplot.ai
bar-horizontal: Horizontal Bar Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-07
"""

import os
import sys
import time
from pathlib import Path


if sys.path and sys.path[0] in ("", "."):
    sys.path.pop(0)

from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Top Programming Languages by Developer Popularity (%)
categories = ["JavaScript", "Python", "TypeScript", "Java", "C#", "C++", "PHP", "Go", "Rust", "Kotlin"]
values = [65.6, 49.3, 38.5, 33.3, 28.7, 22.4, 18.2, 14.3, 13.1, 9.2]

# Sort by value (smallest to largest for bottom-to-top display)
sorted_data = sorted(zip(categories, values, strict=True), key=lambda x: x[1])
categories_sorted = [x[0] for x in sorted_data]
values_sorted = [x[1] for x in sorted_data]

# Create data source
source = ColumnDataSource(data={"categories": categories_sorted, "values": values_sorted})

# Create figure with categorical y-axis (4800 × 2700 px)
p = figure(
    width=4800,
    height=2700,
    y_range=categories_sorted,
    x_axis_label="Developer Popularity (%)",
    title="bar-horizontal · bokeh · anyplot.ai",
    toolbar_location=None,
)

# Draw horizontal bars with Okabe-Ito color #009E73
p.hbar(
    y="categories",
    right="values",
    height=0.7,
    source=source,
    color="#009E73",
    line_color=INK_SOFT,
    line_width=2,
    alpha=0.9,
)

# Style title
p.title.text_font_size = "28pt"
p.title.align = "center"
p.title.text_color = INK

# Style axes for large canvas
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.axis_label_standoff = 20
p.yaxis.axis_label_standoff = 20
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# Configure grid
p.xgrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0

# Theme-adaptive background
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Set x-axis range starting from 0
p.x_range.start = 0
p.x_range.end = 75

# Add padding on left for category labels
p.min_border_left = 200

# Save as HTML for interactivity
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
