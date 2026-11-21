"""anyplot.ai
histogram-cumulative: Cumulative Histogram
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
"""

import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd


sys.path.pop(0)

from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: single series uses position 1
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

# Constants
N_BINS = 30  # number of contiguous bins of the cumulative histogram

# Columns: set these to your table's column names
RESPONSE_TIME = "Response Time (ms)"  # role: numeric
CUMULATIVE = "Cumulative Count"

# Data: replace this block with your own table, for example df = pd.read_csv("response_times.csv")
np.random.seed(42)
response_times = np.concatenate(
    [np.random.exponential(scale=150, size=400), np.random.normal(loc=500, scale=100, size=100)]
)
df = pd.DataFrame({RESPONSE_TIME: np.clip(response_times, 10, 1000)})

# Plot
values = df[RESPONSE_TIME].dropna()
hist_counts, bin_edges = np.histogram(values, bins=N_BINS)
cumulative_counts = np.cumsum(hist_counts)

# Step outline: rises at each bin's lower edge, stays flat to its upper edge
step_x, step_y = [bin_edges[0]], [0]
for i, total in enumerate(cumulative_counts):
    step_x += [bin_edges[i], bin_edges[i + 1]]
    step_y += [total, total]

step_source = ColumnDataSource({RESPONSE_TIME: step_x, CUMULATIVE: step_y})
fill_source = ColumnDataSource({RESPONSE_TIME: step_x + [step_x[-1], step_x[0]], CUMULATIVE: step_y + [0, 0]})
marker_source = ColumnDataSource({RESPONSE_TIME: bin_edges[1:], CUMULATIVE: cumulative_counts})

p = figure(
    width=3200,
    height=1800,
    title="histogram-cumulative · python · bokeh · anyplot.ai",
    x_axis_label=RESPONSE_TIME,
    y_axis_label=CUMULATIVE,
    toolbar_location=None,
    y_range=Range1d(0, cumulative_counts[-1] * 1.05),
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Cumulative step function with filled area and a marker at each bin's upper edge
p.patch(x=RESPONSE_TIME, y=CUMULATIVE, source=fill_source, fill_color=BRAND, fill_alpha=0.15, line_width=0)
p.line(x=RESPONSE_TIME, y=CUMULATIVE, source=step_source, line_width=4, color=BRAND, alpha=0.9)
p.scatter(x=RESPONSE_TIME, y=CUMULATIVE, source=marker_source, size=11, color=BRAND, line_color=INK_SOFT, line_width=2)

# Style
p.title.text_font_size = "50pt"
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"

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
W, H = 3200, 1800
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
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
