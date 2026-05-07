"""anyplot.ai
spiral-timeseries: Spiral Time Series Chart
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-05-07
"""

import os
import sys
import time
from pathlib import Path


# Remove current directory from sys.path to avoid shadowing bokeh module
if "" in sys.path:
    sys.path.remove("")
if "." in sys.path:
    sys.path.remove(".")

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColorBar, ColumnDataSource, Label, LinearColorMapper
from bokeh.palettes import Viridis256
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Data — daily average temperatures (synthetic) for a temperate city, 2019–2023
np.random.seed(42)
dates = pd.date_range("2019-01-01", "2023-12-31", freq="D")
n = len(dates)
day_of_year = dates.day_of_year.values.astype(float)
year_offset = (dates.year.values - 2019).astype(float)

# Seasonal sinusoidal pattern with slight warming trend and noise
temperature = (
    12.0 + 14.0 * np.sin(2 * np.pi * (day_of_year - 80) / 365) + 0.3 * year_offset + np.random.normal(0, 2.5, n)
)

# Archimedean spiral: r grows linearly with θ; one year ≈ one full revolution
days_elapsed = (dates - dates[0]).days.values.astype(float)
num_rev = 5.0
theta = 2 * np.pi * days_elapsed / 365.25  # continuous accumulated angle

inner_r = 220.0
outer_r = 950.0
r = inner_r + (outer_r - inner_r) * theta / (num_rev * 2 * np.pi)

# Cartesian coordinates — start at 12 o'clock (top), advance clockwise
phi0 = np.pi / 2
x = r * np.cos(phi0 - theta)
y = r * np.sin(phi0 - theta)

# Segment endpoints + midpoint temperatures for color mapping
x0, y0, x1, y1 = x[:-1], y[:-1], x[1:], y[1:]
seg_temp = (temperature[:-1] + temperature[1:]) / 2
source = ColumnDataSource({"x0": x0, "y0": y0, "x1": x1, "y1": y1, "temp": seg_temp})

# Color mapper (Viridis for continuous temperature values)
t_min, t_max = float(temperature.min()), float(temperature.max())
mapper = LinearColorMapper(palette=Viridis256, low=t_min, high=t_max)

# Figure
p = figure(
    width=3600,
    height=3600,
    title="Daily Temperatures 2019–2023 · spiral-timeseries · bokeh · anyplot.ai",
    toolbar_location=None,
    x_range=(-1200, 1200),
    y_range=(-1200, 1200),
)

# Month radial dividers and labels (one per month, at fixed angular positions)
month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
# Days elapsed since Jan 1 for each month's start (0-indexed, non-leap)
month_day_offsets = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]

for doy_offset, mname in zip(month_day_offsets, month_names, strict=True):
    ang = phi0 - 2 * np.pi * doy_offset / 365.25
    r_inner_line = inner_r * 0.82
    r_outer_line = outer_r * 1.07
    p.line(
        [r_inner_line * np.cos(ang), r_outer_line * np.cos(ang)],
        [r_inner_line * np.sin(ang), r_outer_line * np.sin(ang)],
        line_color=INK_SOFT,
        line_alpha=0.25,
        line_width=2,
        line_dash="dashed",
    )
    label_r = outer_r * 1.17
    p.add_layout(
        Label(
            x=label_r * np.cos(ang),
            y=label_r * np.sin(ang),
            text=mname,
            text_align="center",
            text_baseline="middle",
            text_color=INK_MUTED,
            text_font_size="20pt",
        )
    )

# Year labels — placed just to the right of the Jan 1 mark on each revolution
for yi in range(5):
    yr_r = inner_r + (outer_r - inner_r) * yi / num_rev
    p.add_layout(
        Label(
            x=65,
            y=yr_r - 12,
            text=str(2019 + yi),
            text_align="left",
            text_baseline="top",
            text_color=INK,
            text_font_size="22pt",
            text_font_style="bold",
        )
    )

# Spiral segments colored by temperature
p.segment(
    x0="x0", y0="y0", x1="x1", y1="y1", line_color={"field": "temp", "transform": mapper}, line_width=6, source=source
)

# Color bar
color_bar = ColorBar(
    color_mapper=mapper,
    title="Temperature (°C)",
    title_text_font_size="20pt",
    title_text_color=INK_SOFT,
    major_label_text_font_size="18pt",
    major_label_text_color=INK_SOFT,
    background_fill_color=ELEVATED_BG,
    bar_line_color=INK_SOFT,
    width=40,
    height=600,
    label_standoff=14,
)
p.add_layout(color_bar, "right")

# Theme chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
p.title.text_color = INK
p.title.text_font_size = "28pt"
p.title.text_font_style = "normal"
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome via Selenium
W, H = 4000, 3700
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
driver.execute_script(
    f"document.body.style.backgroundColor='{PAGE_BG}';document.body.style.margin='0';document.body.style.padding='0';"
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
