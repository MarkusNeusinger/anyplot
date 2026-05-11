""" anyplot.ai
histogram-cumulative: Cumulative Histogram
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 95/100 | Updated: 2026-05-11
"""

import os
import sys
import time
from pathlib import Path

import numpy as np


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
BRAND = "#009E73"

# Data - simulating response times (milliseconds) for a web service
np.random.seed(42)
response_times = np.concatenate(
    [np.random.exponential(scale=150, size=400), np.random.normal(loc=500, scale=100, size=100)]
)
response_times = np.clip(response_times, 10, 1000)

# Calculate cumulative histogram
n_bins = 30
hist_counts, bin_edges = np.histogram(response_times, bins=n_bins)
cumulative_counts = np.cumsum(hist_counts)

# Prepare step data for cumulative histogram
step_x = []
step_y = []
step_x.append(bin_edges[0])
step_y.append(0)
for i in range(len(cumulative_counts)):
    step_x.append(bin_edges[i])
    step_y.append(cumulative_counts[i])
    step_x.append(bin_edges[i + 1])
    step_y.append(cumulative_counts[i])

source = ColumnDataSource(data={"x": step_x, "y": step_y})

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="histogram-cumulative · bokeh · anyplot.ai",
    x_axis_label="Response Time (ms)",
    y_axis_label="Cumulative Count",
    toolbar_location=None,
)

# Plot cumulative histogram as step function
p.line(x="x", y="y", source=source, line_width=5, color=BRAND, alpha=0.9)

# Add filled area under the curve
fill_x = step_x + [step_x[-1], step_x[0]]
fill_y = step_y + [0, 0]
fill_source = ColumnDataSource(data={"x": fill_x, "y": fill_y})
p.patch(x="x", y="y", source=fill_source, fill_color=BRAND, fill_alpha=0.15, line_width=0)

# Add markers at bin edges
marker_source = ColumnDataSource(data={"x": bin_edges[1:], "y": cumulative_counts})
p.scatter(x="x", y="y", source=marker_source, size=15, color=BRAND, line_color=INK_SOFT, line_width=2, alpha=0.8)

# Style text - scaled for 4800x2700
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT
p.outline_line_width = 1

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

if p.legend:
    p.legend.background_fill_color = ELEVATED_BG
    p.legend.border_line_color = INK_SOFT
    p.legend.label_text_color = INK_SOFT

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
