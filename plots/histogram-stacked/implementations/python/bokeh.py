""" anyplot.ai
histogram-stacked: Stacked Histogram
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-12
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


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - Simulating test scores from three different study groups
np.random.seed(42)

group_a = np.random.normal(loc=75, scale=8, size=150)
group_b = np.random.normal(loc=82, scale=10, size=120)
group_c = np.random.normal(loc=65, scale=12, size=100)

# Cap test scores at realistic range (0-100)
group_a = np.clip(group_a, 0, 100)
group_b = np.clip(group_b, 0, 100)
group_c = np.clip(group_c, 0, 100)

# Create consistent bin edges for all groups
all_data = np.concatenate([group_a, group_b, group_c])
bin_edges = np.linspace(0, 100, 16)

# Compute histograms with same bins
hist_a, _ = np.histogram(group_a, bins=bin_edges)
hist_b, _ = np.histogram(group_b, bins=bin_edges)
hist_c, _ = np.histogram(group_c, bins=bin_edges)

bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
bin_width = bin_edges[1] - bin_edges[0]

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="histogram-stacked · bokeh · anyplot.ai",
    x_axis_label="Test Score (points)",
    y_axis_label="Frequency (count)",
)

# Prepare data for stacking
source_c = ColumnDataSource(
    data={
        "x": bin_centers,
        "top": hist_c,
        "bottom": np.zeros_like(hist_c),
        "width": [bin_width * 0.85] * len(bin_centers),
    }
)

source_a = ColumnDataSource(
    data={"x": bin_centers, "top": hist_c + hist_a, "bottom": hist_c, "width": [bin_width * 0.85] * len(bin_centers)}
)

source_b = ColumnDataSource(
    data={
        "x": bin_centers,
        "top": hist_c + hist_a + hist_b,
        "bottom": hist_c + hist_a,
        "width": [bin_width * 0.85] * len(bin_centers),
    }
)

# Plot stacked bars using ColumnDataSource
p.vbar(
    x="x",
    top="top",
    bottom="bottom",
    width="width",
    source=source_c,
    fill_color=IMPRINT[2],
    line_color="white",
    line_width=2,
    alpha=0.9,
    legend_label="Group C",
)

p.vbar(
    x="x",
    top="top",
    bottom="bottom",
    width="width",
    source=source_a,
    fill_color=IMPRINT[0],
    line_color="white",
    line_width=2,
    alpha=0.9,
    legend_label="Group A",
)

p.vbar(
    x="x",
    top="top",
    bottom="bottom",
    width="width",
    source=source_b,
    fill_color=IMPRINT[1],
    line_color="white",
    line_width=2,
    alpha=0.9,
    legend_label="Group B",
)

# Text sizing for 4800x2700 canvas
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.title.text_color = INK
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

# Legend styling
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT
p.legend.label_text_font_size = "18pt"
p.legend.location = "top_right"

p.y_range.start = 0

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
