""" anyplot.ai
heatmap-polar: Polar Heatmap for Cyclic Two-Dimensional Data
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 84/100 | Created: 2026-05-13
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import ColorBar, ColumnDataSource, Label, LinearColorMapper
from bokeh.palettes import Viridis256
from bokeh.plotting import figure
from bokeh.transform import transform as bk_transform
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data: hourly website visits by day of week
np.random.seed(42)
n_hours = 24
n_days = 7
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

traffic = np.zeros((n_days, n_hours))
for d in range(n_days):
    for h in range(n_hours):
        if d < 5:
            morning = 820 * np.exp(-0.5 * ((h - 9) / 1.5) ** 2)
            evening = 640 * np.exp(-0.5 * ((h - 20) / 2.0) ** 2)
            traffic[d, h] = 100 + morning + evening
        else:
            afternoon = 510 * np.exp(-0.5 * ((h - 14) / 3.0) ** 2)
            traffic[d, h] = 80 + afternoon
        traffic[d, h] += np.random.normal(0, 25)
        traffic[d, h] = max(20, traffic[d, h])

# Build polar heatmap segments
min_r = 0.28
max_r = 1.05
ring_width = (max_r - min_r) / n_days

inner_radii, outer_radii, start_angles, end_angles, cell_values = [], [], [], [], []

for d in range(n_days):
    ir = min_r + d * ring_width + 0.004
    or_ = min_r + (d + 1) * ring_width - 0.004
    for h in range(n_hours):
        sa = np.pi / 2 - 2 * np.pi * h / n_hours
        ea = np.pi / 2 - 2 * np.pi * (h + 1) / n_hours
        inner_radii.append(ir)
        outer_radii.append(or_)
        start_angles.append(sa)
        end_angles.append(ea)
        cell_values.append(traffic[d, h])

source = ColumnDataSource(
    data={
        "inner_radius": inner_radii,
        "outer_radius": outer_radii,
        "start_angle": start_angles,
        "end_angle": end_angles,
        "value": cell_values,
    }
)

color_mapper = LinearColorMapper(palette=Viridis256, low=min(cell_values), high=max(cell_values))

# Plot
W, H = 3600, 3600
p = figure(
    width=W,
    height=H,
    x_range=(-1.42, 1.42),
    y_range=(-1.42, 1.42),
    title="Website Traffic · heatmap-polar · bokeh · anyplot.ai",
    toolbar_location=None,
)

p.annular_wedge(
    x=0,
    y=0,
    inner_radius="inner_radius",
    outer_radius="outer_radius",
    start_angle="start_angle",
    end_angle="end_angle",
    direction="clock",
    fill_color=bk_transform("value", color_mapper),
    line_color=PAGE_BG,
    line_width=0.6,
    source=source,
)

# Spoke lines at major hour boundaries (every 3 hours)
for h in range(0, 24, 3):
    angle = np.pi / 2 - 2 * np.pi * h / n_hours
    cx, cy = np.cos(angle), np.sin(angle)
    p.segment(
        x0=[min_r * cx],
        y0=[min_r * cy],
        x1=[max_r * cx],
        y1=[max_r * cy],
        line_color=PAGE_BG,
        line_width=1.5,
        line_alpha=0.7,
    )

# Hour labels (every 3 hours, clock layout: midnight top, 6am right, noon bottom, 6pm left)
for h in range(0, 24, 3):
    angle = np.pi / 2 - 2 * np.pi * h / n_hours
    lx = 1.20 * np.cos(angle)
    ly = 1.20 * np.sin(angle)
    hour_12 = h % 12 or 12
    suffix = "am" if h < 12 else "pm"
    p.add_layout(
        Label(
            x=lx,
            y=ly,
            text=f"{hour_12}{suffix}",
            text_align="center",
            text_baseline="middle",
            text_font_size="24px",
            text_color=INK_SOFT,
        )
    )

# Day labels placed at the centroid of the midnight cell for each ring
cell_angle = np.pi / 2 - np.pi / n_hours  # centre of hour-0 wedge (7.5° from top)
for d, day in enumerate(days):
    mid_r = min_r + d * ring_width + ring_width / 2
    lx = mid_r * np.cos(cell_angle)
    ly = mid_r * np.sin(cell_angle)
    p.add_layout(
        Label(
            x=lx,
            y=ly,
            text=day,
            text_align="center",
            text_baseline="middle",
            text_font_size="20px",
            text_color="white",
            text_font_style="bold",
        )
    )

# Colorbar
color_bar = ColorBar(
    color_mapper=color_mapper,
    width=40,
    padding=15,
    location=(0, 0),
    title="Hourly Visits",
    title_text_font_size="22px",
    title_text_color=INK,
    major_label_text_font_size="20px",
    major_label_text_color=INK_SOFT,
    background_fill_color=PAGE_BG,
)
p.add_layout(color_bar, "right")

# Chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.title.text_font_size = "28px"
p.title.text_color = INK
p.title.text_font_style = "normal"
p.title.align = "center"

p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome via Selenium
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
