"""anyplot.ai
scatter-marginal: Scatter Plot with Marginal Distributions
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_BINS = 30  # histogram bins for both marginals

# Columns: set these to your table's column names
HEIGHT = "Height (cm)"  # role: x
WEIGHT = "Weight (kg)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("measurements.csv")
rng = np.random.default_rng(42)
heights = rng.normal(170, 9, 200)
weights = 70 + 0.9 * (heights - 170) + rng.normal(0, 8, 200)
df = pd.DataFrame({HEIGHT: heights, WEIGHT: weights})

# Plot: reads only df and the constants above
source = ColumnDataSource(df)
x_hist, x_edges = np.histogram(df[HEIGHT].dropna(), bins=N_BINS)
y_hist, y_edges = np.histogram(df[WEIGHT].dropna(), bins=N_BINS)

# Canvas: 3200 x 1800 in total, split into scatter, top marginal (with the title) and right marginal
SIDE_W = 600
TOP_H = 430
LEFT_BORDER = 200
BOTTOM_BORDER = 170
total_w, total_h = 3200, 1800
main_w = total_w - SIDE_W
main_h = total_h - TOP_H


def style_axes(p, axis):
    """Apply the theme chrome to the visible axis of a panel."""
    p.background_fill_color = PAGE_BG
    p.border_fill_color = PAGE_BG
    p.outline_line_color = INK_SOFT
    p.grid.grid_line_color = INK
    p.grid.grid_line_alpha = 0.10
    axis.axis_line_color = INK_SOFT
    axis.major_tick_line_color = INK_SOFT
    axis.minor_tick_line_color = None
    axis.axis_label_text_color = INK
    axis.major_label_text_color = INK_SOFT
    p.toolbar_location = None


# Main scatter
p_scatter = figure(
    width=main_w,
    height=main_h,
    x_axis_label=HEIGHT,
    y_axis_label=WEIGHT,
    toolbar_location=None,
    min_border_left=LEFT_BORDER,
    min_border_bottom=BOTTOM_BORDER,
    min_border_top=10,
    min_border_right=10,
)
p_scatter.scatter(x=HEIGHT, y=WEIGHT, source=source, size=22, color=IMPRINT_PALETTE[0], alpha=0.65, line_color=None)
style_axes(p_scatter, p_scatter.xaxis)
p_scatter.yaxis.axis_line_color = INK_SOFT
p_scatter.yaxis.major_tick_line_color = INK_SOFT
p_scatter.yaxis.minor_tick_line_color = None
p_scatter.yaxis.axis_label_text_color = INK
p_scatter.yaxis.major_label_text_color = INK_SOFT
p_scatter.xaxis.axis_label_text_font_size = "42pt"
p_scatter.yaxis.axis_label_text_font_size = "42pt"
p_scatter.xaxis.major_label_text_font_size = "34pt"
p_scatter.yaxis.major_label_text_font_size = "34pt"

# Top marginal: x distribution, shares the scatter's x range; carries the title
p_top = figure(
    width=main_w,
    height=TOP_H,
    x_range=p_scatter.x_range,
    title="scatter-marginal · python · bokeh · anyplot.ai",
    toolbar_location=None,
    min_border_left=LEFT_BORDER,
    min_border_bottom=0,
    min_border_top=90,
    min_border_right=10,
)
p_top.quad(
    top=x_hist,
    bottom=0,
    left=x_edges[:-1],
    right=x_edges[1:],
    fill_color=IMPRINT_PALETTE[0],
    fill_alpha=0.45,
    line_color=PAGE_BG,
    line_width=2,
)
style_axes(p_top, p_top.yaxis)
p_top.xaxis.visible = False
p_top.y_range.start = 0
p_top.yaxis.axis_label = "Count"
p_top.yaxis.axis_label_text_font_size = "34pt"
p_top.yaxis.major_label_text_font_size = "28pt"
p_top.title.text_font_size = "50pt"
p_top.title.text_color = INK

# Right marginal: y distribution, shares the scatter's y range, grows away from the scatter
p_right = figure(
    width=SIDE_W,
    height=main_h,
    y_range=p_scatter.y_range,
    toolbar_location=None,
    min_border_left=0,
    min_border_bottom=BOTTOM_BORDER,
    min_border_top=10,
    min_border_right=40,
)
p_right.quad(
    top=y_edges[1:],
    bottom=y_edges[:-1],
    left=0,
    right=y_hist,
    fill_color=IMPRINT_PALETTE[0],
    fill_alpha=0.45,
    line_color=PAGE_BG,
    line_width=2,
)
style_axes(p_right, p_right.xaxis)
p_right.yaxis.visible = False
p_right.x_range.start = 0
p_right.xaxis.axis_label = "Count"
p_right.xaxis.axis_label_text_font_size = "34pt"
p_right.xaxis.major_label_text_font_size = "28pt"

# Empty top-right corner
p_corner = figure(width=SIDE_W, height=TOP_H, toolbar_location=None, min_border=0)
p_corner.outline_line_color = None
p_corner.xaxis.visible = False
p_corner.yaxis.visible = False
p_corner.grid.visible = False
p_corner.background_fill_color = PAGE_BG
p_corner.border_fill_color = PAGE_BG

layout = column(row(p_top, p_corner, spacing=0), row(p_scatter, p_right, spacing=0), spacing=0)

# Save HTML
output_file(f"plot-{THEME}.html")
save(layout)

# Screenshot with headless Chrome
W, H = total_w, total_h
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
