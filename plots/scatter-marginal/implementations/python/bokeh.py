"""anyplot.ai
scatter-marginal: Scatter Plot with Marginal Distributions
Library: bokeh | Python 3.13
Quality: pending | Created: 2025-12-26
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.layouts import column, row
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

# Data - bivariate normal with correlation
np.random.seed(42)
n_points = 200
x = np.random.randn(n_points) * 15 + 50
y = x * 0.6 + np.random.randn(n_points) * 10 + 20

source = ColumnDataSource(data={"x": x, "y": y})

# Calculate dimensions for 4800x2700 total with marginal plots
main_width = 3800
main_height = 2100
marginal_width = 3800
marginal_height = 550
side_marginal_width = 950
side_marginal_height = 2100

# Histogram bins
n_bins = 30
x_hist, x_edges = np.histogram(x, bins=n_bins)
y_hist, y_edges = np.histogram(y, bins=n_bins)

# Main scatter plot
p_scatter = figure(
    width=main_width,
    height=main_height,
    x_axis_label="Height (cm)",
    y_axis_label="Weight (kg)",
    title="scatter-marginal · bokeh · anyplot.ai",
)

p_scatter.scatter(x="x", y="y", source=source, size=20, color=BRAND, alpha=0.65, line_color=None)

# Style main scatter
p_scatter.title.text_font_size = "28pt"
p_scatter.title.text_color = INK
p_scatter.xaxis.axis_label_text_font_size = "22pt"
p_scatter.yaxis.axis_label_text_font_size = "22pt"
p_scatter.xaxis.axis_label_text_color = INK
p_scatter.yaxis.axis_label_text_color = INK
p_scatter.xaxis.major_label_text_font_size = "18pt"
p_scatter.yaxis.major_label_text_font_size = "18pt"
p_scatter.xaxis.major_label_text_color = INK_SOFT
p_scatter.yaxis.major_label_text_color = INK_SOFT
p_scatter.xaxis.axis_line_color = INK_SOFT
p_scatter.yaxis.axis_line_color = INK_SOFT
p_scatter.xaxis.major_tick_line_color = INK_SOFT
p_scatter.yaxis.major_tick_line_color = INK_SOFT
p_scatter.background_fill_color = PAGE_BG
p_scatter.border_fill_color = PAGE_BG
p_scatter.outline_line_color = INK_SOFT
p_scatter.grid.grid_line_color = INK
p_scatter.grid.grid_line_alpha = 0.10
p_scatter.toolbar_location = None

# Top marginal histogram (X distribution)
p_top = figure(width=marginal_width, height=marginal_height, x_range=p_scatter.x_range, title=None)
p_top.quad(top=x_hist, bottom=0, left=x_edges[:-1], right=x_edges[1:], fill_color=BRAND, line_color=None, alpha=0.6)
p_top.xaxis.visible = False
p_top.yaxis.axis_label = "Count"
p_top.yaxis.axis_label_text_font_size = "18pt"
p_top.yaxis.axis_label_text_color = INK
p_top.yaxis.major_label_text_font_size = "14pt"
p_top.yaxis.major_label_text_color = INK_SOFT
p_top.yaxis.axis_line_color = INK_SOFT
p_top.yaxis.major_tick_line_color = INK_SOFT
p_top.background_fill_color = PAGE_BG
p_top.border_fill_color = PAGE_BG
p_top.outline_line_color = INK_SOFT
p_top.grid.grid_line_color = INK
p_top.grid.grid_line_alpha = 0.10
p_top.min_border_bottom = 0
p_top.min_border_left = p_scatter.min_border_left
p_top.toolbar_location = None

# Right marginal histogram (Y distribution)
p_right = figure(width=side_marginal_width, height=main_height, y_range=p_scatter.y_range, title=None)
p_right.quad(top=y_edges[1:], bottom=y_edges[:-1], left=0, right=y_hist, fill_color=BRAND, line_color=None, alpha=0.6)
p_right.yaxis.visible = False
p_right.xaxis.axis_label = "Count"
p_right.xaxis.axis_label_text_font_size = "18pt"
p_right.xaxis.axis_label_text_color = INK
p_right.xaxis.major_label_text_font_size = "14pt"
p_right.xaxis.major_label_text_color = INK_SOFT
p_right.xaxis.axis_line_color = INK_SOFT
p_right.xaxis.major_tick_line_color = INK_SOFT
p_right.background_fill_color = PAGE_BG
p_right.border_fill_color = PAGE_BG
p_right.outline_line_color = INK_SOFT
p_right.grid.grid_line_color = INK
p_right.grid.grid_line_alpha = 0.10
p_right.min_border_left = 0
p_right.min_border_bottom = p_scatter.min_border_bottom
p_right.toolbar_location = None

# Empty corner placeholder
p_corner = figure(width=side_marginal_width, height=marginal_height, toolbar_location=None)
p_corner.outline_line_color = None
p_corner.xaxis.visible = False
p_corner.yaxis.visible = False
p_corner.grid.visible = False
p_corner.background_fill_color = PAGE_BG
p_corner.border_fill_color = PAGE_BG

# Layout
layout = column(row(p_top, p_corner), row(p_scatter, p_right))

# Save HTML
output_file(f"plot-{THEME}.html")
save(layout)

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
