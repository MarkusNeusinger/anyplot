""" anyplot.ai
scatter-color-mapped: Color-Mapped Scatter Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-08
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import ColorBar, ColumnDataSource, HoverTool, LinearColorMapper
from bokeh.palettes import Viridis256
from bokeh.plotting import figure
from bokeh.transform import linear_cmap
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data
np.random.seed(42)
n_points = 150
x = np.random.randn(n_points) * 10 + 50
y = 0.6 * x + np.random.randn(n_points) * 8 + 20
intensity = np.sqrt((x - 50) ** 2 + (y - 50) ** 2) + np.random.randn(n_points) * 3

source = ColumnDataSource(data={"x": x, "y": y, "intensity": intensity})

# Create color mapper
color_mapper = LinearColorMapper(palette=Viridis256, low=intensity.min(), high=intensity.max())

# Create figure (4800 x 2700 px)
p = figure(
    width=4800,
    height=2700,
    title="scatter-color-mapped · bokeh · anyplot.ai",
    x_axis_label="X Coordinate (units)",
    y_axis_label="Y Coordinate (units)",
)

# Add HoverTool for interactivity
hover = HoverTool(tooltips=[("X", "@x{0.00}"), ("Y", "@y{0.00}"), ("Intensity", "@intensity{0.00}")])
p.add_tools(hover)

# Plot scatter with color mapping
p.scatter(
    x="x",
    y="y",
    source=source,
    size=35,
    fill_color=linear_cmap("intensity", palette=Viridis256, low=intensity.min(), high=intensity.max()),
    line_color=None,
    fill_alpha=0.8,
)

# Add colorbar
color_bar = ColorBar(
    color_mapper=color_mapper,
    title="Intensity (magnitude)",
    title_text_font_size="22pt",
    title_standoff=20,
    major_label_text_font_size="18pt",
    label_standoff=12,
    width=50,
    padding=40,
)
p.add_layout(color_bar, "right")

# Styling for large canvas
p.title.text_font_size = "28pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

# Grid styling
p.grid.grid_line_color = INK
p.grid.grid_line_alpha = 0.10
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# Background
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Legend styling
if p.legend:
    p.legend.background_fill_color = ELEVATED_BG
    p.legend.border_line_color = INK_SOFT
    p.legend.label_text_color = INK_SOFT

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
