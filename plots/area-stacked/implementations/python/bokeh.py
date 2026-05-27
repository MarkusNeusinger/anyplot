""" anyplot.ai
area-stacked: Stacked Area Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-07
"""

import os
import sys
import time
from pathlib import Path


# Remove current directory from sys.path to avoid shadowing bokeh module
if "" in sys.path:
    sys.path.remove("")
if "." in sys.path:
    sys.path.remove(".")

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, FixedTicker, HoverTool, Legend
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series is #009E73)
IMPRINT = [
    "#009E73",  # bluish green (brand)
    "#C475FD",  # vermillion
    "#4467A3",  # blue
    "#BD8233",  # reddish purple
]

# Data - Monthly revenue by product category over 2 years
np.random.seed(42)
months = pd.date_range("2023-01-01", periods=24, freq="MS")

# Generate realistic revenue data with trends
base_electronics = 150 + np.arange(24) * 3 + np.random.randn(24) * 15
base_clothing = 100 + np.sin(np.linspace(0, 4 * np.pi, 24)) * 20 + np.random.randn(24) * 10
base_home = 80 + np.arange(24) * 1.5 + np.random.randn(24) * 8
base_sports = 50 + np.cos(np.linspace(0, 4 * np.pi, 24)) * 15 + np.random.randn(24) * 5

# Ensure all values are positive
electronics = np.maximum(base_electronics, 20)
clothing = np.maximum(base_clothing, 15)
home_garden = np.maximum(base_home, 10)
sports = np.maximum(base_sports, 8)

# Order series by size (largest at bottom for better reading)
# Average values: Electronics (150+), Clothing (100+), Home (80+), Sports (50+)
series_data = [("Electronics", electronics), ("Clothing", clothing), ("Home & Garden", home_garden), ("Sports", sports)]

# Calculate stacked values (cumulative sums for stacking)
x_values = np.arange(len(months))
x_labels = [d.strftime("%b %Y") for d in months]

# Stack from bottom up
stacked = {}
cumsum = np.zeros(len(months))
for name, values in series_data:
    stacked[name] = cumsum.copy()
    cumsum += values

# Create figure
title = "area-stacked · bokeh · anyplot.ai"
p = figure(
    width=4800,
    height=2700,
    title=title,
    x_axis_label="Month",
    y_axis_label="Revenue ($K)",
    x_range=(-0.5, 23.5),
    y_range=(0, cumsum.max() * 1.1),
)

# Plot stacked areas with HoverTool
legend_items = []
for idx, (name, values) in enumerate(series_data):
    y1 = stacked[name]
    y2 = y1 + values
    source = ColumnDataSource(
        data={"x": x_values, "y1": y1, "y2": y2, "month": x_labels, "value": values, "name": [name] * len(x_values)}
    )

    renderer = p.varea(x="x", y1="y1", y2="y2", source=source, fill_color=IMPRINT[idx], fill_alpha=0.85)
    legend_items.append((name, [renderer]))

    # Add HoverTool for this series
    hover = HoverTool(
        renderers=[renderer], tooltips=[("Month", "@month"), ("Category", "@name"), ("Value", "@value{0,0} $K")]
    )
    p.add_tools(hover)

# Add legend
legend = Legend(items=legend_items, location="top_left")
legend.label_text_font_size = "18pt"
legend.glyph_height = 40
legend.glyph_width = 40
legend.spacing = 15
legend.padding = 20
legend.background_fill_color = ELEVATED_BG
legend.background_fill_alpha = 0.9
legend.border_line_color = INK_SOFT
legend.label_text_color = INK_SOFT
p.add_layout(legend, "right")

# Style text sizes for large canvas
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

# Custom x-axis tick labels (show every 3 months)
p.xaxis.ticker = FixedTicker(ticks=[0, 3, 6, 9, 12, 15, 18, 21, 23])
p.xaxis.major_label_overrides = {i: x_labels[i] for i in range(len(x_labels))}
p.xaxis.major_label_orientation = 0.6

# Grid styling
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

# Background and borders
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Axis styling
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

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
