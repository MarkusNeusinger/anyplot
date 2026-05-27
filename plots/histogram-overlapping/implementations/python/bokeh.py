""" anyplot.ai
histogram-overlapping: Overlapping Histograms
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-08
"""

import os
import sys


# Prevent local bokeh.py from being treated as bokeh module
sys.path = [p for p in sys.path if p not in ("", ".", os.getcwd())]

import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
from bokeh.io import output_file, save  # noqa: E402
from bokeh.models import ColumnDataSource, HoverTool  # noqa: E402
from bokeh.plotting import figure  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (canonical order)
BRAND = "#009E73"  # Position 1 - first series
COLOR_2 = "#C475FD"  # Position 2
COLOR_3 = "#4467A3"  # Position 3

# Data - Employee response times (ms) by department
np.random.seed(42)
engineering = np.random.normal(250, 50, 150)
sales = np.random.normal(320, 70, 150)
support = np.random.normal(280, 40, 150)

# Compute histogram bins (aligned across all groups)
all_data = np.concatenate([engineering, sales, support])
bins = np.linspace(all_data.min() - 10, all_data.max() + 10, 30)

# Compute histogram values
eng_hist, eng_edges = np.histogram(engineering, bins=bins)
sales_hist, _ = np.histogram(sales, bins=bins)
support_hist, _ = np.histogram(support, bins=bins)

# Prepare data for ColumnDataSource
bin_centers = (eng_edges[:-1] + eng_edges[1:]) / 2
bin_widths = eng_edges[1:] - eng_edges[:-1]

data = {
    "bin_left": eng_edges[:-1],
    "bin_right": eng_edges[1:],
    "bin_center": bin_centers,
    "eng_count": eng_hist,
    "sales_count": sales_hist,
    "support_count": support_hist,
}

source = ColumnDataSource(data)

# Create figure (4800 x 2700 px)
p = figure(
    width=4800,
    height=2700,
    title="histogram-overlapping · bokeh · anyplot.ai",
    x_axis_label="Response Time (ms)",
    y_axis_label="Frequency",
    tools="pan,wheel_zoom,box_zoom,reset,hover",
    toolbar_location="above",
)

# Plot overlapping histograms
eng_render = p.quad(
    top="eng_count",
    bottom=0,
    left="bin_left",
    right="bin_right",
    source=source,
    fill_color=BRAND,
    fill_alpha=0.5,
    line_color=BRAND,
    line_width=2,
    line_alpha=0.8,
    legend_label="Engineering",
)

sales_render = p.quad(
    top="sales_count",
    bottom=0,
    left="bin_left",
    right="bin_right",
    source=source,
    fill_color=COLOR_2,
    fill_alpha=0.5,
    line_color=COLOR_2,
    line_width=2,
    line_alpha=0.8,
    legend_label="Sales",
)

support_render = p.quad(
    top="support_count",
    bottom=0,
    left="bin_left",
    right="bin_right",
    source=source,
    fill_color=COLOR_3,
    fill_alpha=0.5,
    line_color=COLOR_3,
    line_width=2,
    line_alpha=0.8,
    legend_label="Support",
)

# Configure hover tool
hover = p.select_one(HoverTool)
hover.tooltips = [
    ("Range", "@bin_left ms - @bin_right ms"),
    ("Engineering", "@eng_count"),
    ("Sales", "@sales_count"),
    ("Support", "@support_count"),
]

# Configure text sizes for large canvas
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

# Configure legend
p.legend.location = "top_left"
p.legend.label_text_font_size = "18pt"
p.legend.spacing = 10
p.legend.padding = 15
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT
p.legend.glyph_height = 20
p.legend.glyph_width = 20

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome via Selenium
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
