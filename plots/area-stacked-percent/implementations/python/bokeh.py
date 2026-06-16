""" anyplot.ai
area-stacked-percent: 100% Stacked Area Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-12
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series ALWAYS #009E73)
COLORS = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]
CATEGORIES = ["Product A", "Product B", "Product C", "Product D"]

# Data - Market share evolution over time
np.random.seed(42)
years = np.arange(2015, 2025)

# Generate market share data with more variation to show compositional shifts
product_a = 35 + np.cumsum(np.random.randn(len(years)) * 2.5)
product_b = 28 + np.cumsum(np.random.randn(len(years)) * 2)
product_c = 22 + np.cumsum(np.random.randn(len(years)) * 1.8)
product_d = 15 + np.cumsum(np.random.randn(len(years)) * 1.5)

# Ensure all values are positive
product_a = np.maximum(product_a, 3)
product_b = np.maximum(product_b, 3)
product_c = np.maximum(product_c, 3)
product_d = np.maximum(product_d, 3)

# Normalize to 100%
totals = product_a + product_b + product_c + product_d
pct_a = (product_a / totals) * 100
pct_b = (product_b / totals) * 100
pct_c = (product_c / totals) * 100
pct_d = (product_d / totals) * 100

# Calculate stacked positions
stack_0 = np.zeros(len(years))
stack_a = pct_a
stack_ab = pct_a + pct_b
stack_abc = pct_a + pct_b + pct_c
stack_abcd = pct_a + pct_b + pct_c + pct_d  # Should be 100

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="area-stacked-percent · bokeh · anyplot.ai",
    x_axis_label="Year",
    y_axis_label="Market Share (%)",
    x_range=(2014.5, 2024.5),
    y_range=(0, 105),
    toolbar_location="right",
)

# Add HoverTool for Bokeh interactivity (key differentiator)
hover = HoverTool(tooltips=[("Year", "@x{0}"), ("Percentage", "@y{0.0}%")])
p.add_tools(hover)

# Create patches for stacked areas (bottom to top)
# Product A (bottom layer)
source_a = ColumnDataSource(
    data={"x": np.concatenate([years, years[::-1]]), "y": np.concatenate([stack_a, stack_0[::-1]])}
)
p.patch(
    x="x",
    y="y",
    source=source_a,
    fill_color=COLORS[0],
    fill_alpha=0.85,
    line_color=COLORS[0],
    line_width=2,
    legend_label=CATEGORIES[0],
)

# Product B
source_b = ColumnDataSource(
    data={"x": np.concatenate([years, years[::-1]]), "y": np.concatenate([stack_ab, stack_a[::-1]])}
)
p.patch(
    x="x",
    y="y",
    source=source_b,
    fill_color=COLORS[1],
    fill_alpha=0.85,
    line_color=COLORS[1],
    line_width=2,
    legend_label=CATEGORIES[1],
)

# Product C
source_c = ColumnDataSource(
    data={"x": np.concatenate([years, years[::-1]]), "y": np.concatenate([stack_abc, stack_ab[::-1]])}
)
p.patch(
    x="x",
    y="y",
    source=source_c,
    fill_color=COLORS[2],
    fill_alpha=0.85,
    line_color=COLORS[2],
    line_width=2,
    legend_label=CATEGORIES[2],
)

# Product D (top layer)
source_d = ColumnDataSource(
    data={"x": np.concatenate([years, years[::-1]]), "y": np.concatenate([stack_abcd, stack_abc[::-1]])}
)
p.patch(
    x="x",
    y="y",
    source=source_d,
    fill_color=COLORS[3],
    fill_alpha=0.85,
    line_color=COLORS[3],
    line_width=2,
    legend_label=CATEGORIES[3],
)

# Text sizing for 4800×2700 px
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid styling (subtle per default-style-guide.md)
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

# Legend styling
p.legend.label_text_font_size = "16pt"
p.legend.location = "top_right"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT

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

# Axis tickers
p.xaxis.ticker = list(years)
p.yaxis.ticker = [0, 20, 40, 60, 80, 100]

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome via Selenium (required, not export_png)
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
time.sleep(3)  # let bokeh's JS render the canvas
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
