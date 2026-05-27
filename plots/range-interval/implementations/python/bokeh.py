""" anyplot.ai
range-interval: Range Interval Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-18
"""

import os
import time
from pathlib import Path

import numpy as np
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

BRAND = "#009E73"  # Okabe-Ito position 1
ACCENT = "#C475FD"  # Okabe-Ito position 2

# Data - Temperature ranges across months
np.random.seed(42)

months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
base_temps = [2, 4, 8, 12, 16, 20, 23, 22, 18, 13, 7, 3]

min_temps = [base - np.random.uniform(3, 6) for base in base_temps]
max_temps = [base + np.random.uniform(5, 10) for base in base_temps]
mid_temps = [(min_t + max_t) / 2 for min_t, max_t in zip(min_temps, max_temps, strict=True)]

source = ColumnDataSource(data={"month": months, "min_temp": min_temps, "max_temp": max_temps, "mid_temp": mid_temps})

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="range-interval · python · bokeh · anyplot.ai",
    x_axis_label="Month",
    y_axis_label="Temperature (°C)",
    x_range=months,
    tools="",
    toolbar_location=None,
)

# Range bars (segment glyphs)
p.segment(
    x0="month",
    y0="min_temp",
    x1="month",
    y1="max_temp",
    source=source,
    line_width=40,
    line_color=BRAND,
    line_alpha=0.7,
    line_cap="round",
)

# Min endpoint markers
p.scatter(
    x="month",
    y="min_temp",
    source=source,
    size=20,
    color=BRAND,
    line_color=PAGE_BG,
    line_width=3,
    legend_label="Min Temperature",
)

# Max endpoint markers
p.scatter(
    x="month",
    y="max_temp",
    source=source,
    size=20,
    color=ACCENT,
    line_color=PAGE_BG,
    line_width=3,
    legend_label="Max Temperature",
)

# Midpoint markers
p.scatter(
    x="month",
    y="mid_temp",
    source=source,
    size=12,
    marker="diamond",
    color=INK_SOFT,
    line_color=PAGE_BG,
    line_width=2,
    legend_label="Midpoint",
)

# Title styling
p.title.text_font_size = "28pt"
p.title.text_color = INK

# Axis label styling
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK

# Tick label styling
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

# Grid styling
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10
p.xgrid.grid_line_color = None

# Axis and spine styling
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.axis.axis_line_width = 2
p.outline_line_color = INK_SOFT

# Background
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG

# Legend styling
p.legend.location = "top_left"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_font_size = "16pt"
p.legend.label_text_color = INK_SOFT
p.legend.padding = 15
p.legend.spacing = 10

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with Selenium
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
