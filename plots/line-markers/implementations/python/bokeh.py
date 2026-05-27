""" anyplot.ai
line-markers: Line Plot with Markers
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-12
"""

import os
import sys
import time
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Handle import shadowing by temporarily removing current directory from path
saved_path = sys.path.copy()
sys.path = [p for p in sys.path if not (p in ("", ".") or p == os.getcwd())]

from bokeh.io import output_file, save  # noqa: E402
from bokeh.models import ColumnDataSource, Legend  # noqa: E402
from bokeh.plotting import figure  # noqa: E402


# Restore sys.path for the rest of script
sys.path = saved_path

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Monthly temperature readings for three weather stations (°C)
np.random.seed(42)
months = np.arange(1, 13)
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Temperature patterns for different stations
base_temp = np.array([2, 4, 8, 12, 17, 21, 24, 23, 19, 13, 7, 3])
station_a = base_temp + np.random.randn(12) * 1.5
station_b = base_temp + 3 + np.random.randn(12) * 1.5
station_c = base_temp - 2 + np.random.randn(12) * 1.5

# Create ColumnDataSources
source_a = ColumnDataSource(data={"x": months, "y": station_a})
source_b = ColumnDataSource(data={"x": months, "y": station_b})
source_c = ColumnDataSource(data={"x": months, "y": station_c})

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="line-markers · bokeh · anyplot.ai",
    x_axis_label="Month",
    y_axis_label="Temperature (°C)",
)

# Okabe-Ito color palette
color_a = "#009E73"  # Okabe-Ito position 1 (bluish green)
color_b = "#C475FD"  # Okabe-Ito position 2 (vermillion)
color_c = "#4467A3"  # Okabe-Ito position 3 (blue)

# Plot lines with markers - Station A (circles)
line_a = p.line("x", "y", source=source_a, line_width=4, color=color_a, alpha=0.85)
scatter_a = p.scatter("x", "y", source=source_a, size=18, color=color_a, marker="circle", alpha=0.85)

# Station B (squares)
line_b = p.line("x", "y", source=source_b, line_width=4, color=color_b, alpha=0.85)
scatter_b = p.scatter("x", "y", source=source_b, size=18, color=color_b, marker="square", alpha=0.85)

# Station C (triangles)
line_c = p.line("x", "y", source=source_c, line_width=4, color=color_c, alpha=0.85)
scatter_c = p.scatter("x", "y", source=source_c, size=18, color=color_c, marker="triangle", alpha=0.85)

# Legend with improved sizing
legend = Legend(
    items=[("Station A", [line_a, scatter_a]), ("Station B", [line_b, scatter_b]), ("Station C", [line_c, scatter_c])],
    location="top_left",
)

p.add_layout(legend)
p.legend.label_text_font_size = "22pt"
p.legend.glyph_height = 35
p.legend.glyph_width = 35
p.legend.spacing = 12
p.legend.padding = 20
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT
p.legend.background_fill_alpha = 1.0

# Style text for 4800x2700 canvas
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

# Custom x-axis tick labels for months
p.xaxis.ticker = months
p.xaxis.major_label_overrides = dict(zip(months, month_labels, strict=True))

# Theme-adaptive styling
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

# Write the interactive HTML
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
