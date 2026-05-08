""" anyplot.ai
heatmap-adjacency: Network Adjacency Matrix Heatmap
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 85/100 | Created: 2026-05-08
"""

# ruff: noqa: E402
import sys


# Prevent this script's directory from shadowing the installed bokeh package
_script_dir = sys.path[0] if sys.path else ""
if _script_dir and "implementations/python" in _script_dir:
    sys.path = sys.path[1:]

import math
import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import BasicTicker, ColorBar, ColumnDataSource, LinearColorMapper
from bokeh.palettes import Viridis256
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
NAN_COLOR = "#E8E5DE" if THEME == "light" else "#252520"

# Data — 24 researchers across 4 departments, ordered by department
np.random.seed(42)
dept_codes = ["Phy", "Chem", "Bio", "Math"]
n_per_dept = 6
node_names = [f"{code}{i:02d}" for code in dept_codes for i in range(1, n_per_dept + 1)]
node_community = [idx for idx in range(len(dept_codes)) for _ in range(n_per_dept)]

n = len(node_names)

# Weighted symmetric adjacency matrix
adj = np.zeros((n, n))
for i in range(n):
    for j in range(i + 1, n):
        same_dept = node_community[i] == node_community[j]
        if same_dept and np.random.rand() < 0.80:
            w = np.random.uniform(0.5, 1.0)
            adj[i, j] = w
            adj[j, i] = w
        elif not same_dept and np.random.rand() < 0.08:
            w = np.random.uniform(0.1, 0.4)
            adj[i, j] = w
            adj[j, i] = w

# NaN encodes absent edges (no self-loops shown)
adj_nan = adj.astype(float)
adj_nan[adj == 0] = np.nan

# Flatten to row-per-cell format for ColumnDataSource
xs, ys, weights = [], [], []
for i in range(n):
    for j in range(n):
        xs.append(node_names[j])  # column = target node
        ys.append(node_names[i])  # row = source node
        weights.append(adj_nan[i, j])

source = ColumnDataSource({"x": xs, "y": ys, "weight": weights})

# Continuous color mapper — viridis for edge weights
mapper = LinearColorMapper(palette=Viridis256, low=0.1, high=1.0, nan_color=NAN_COLOR)

# Figure (square canvas for symmetric matrix)
p = figure(
    width=3600,
    height=3600,
    x_range=node_names,
    y_range=list(reversed(node_names)),
    toolbar_location=None,
    title="Researcher Collaboration · heatmap-adjacency · bokeh · anyplot.ai",
)

# Heatmap rectangles
p.rect(
    x="x", y="y", width=1, height=1, source=source, fill_color={"field": "weight", "transform": mapper}, line_color=None
)

# Colorbar
colorbar = ColorBar(
    color_mapper=mapper,
    ticker=BasicTicker(desired_num_ticks=6),
    label_standoff=20,
    border_line_color=None,
    location=(0, 0),
    title="Connection Strength",
    title_text_font_size="20pt",
    title_text_color=INK,
    major_label_text_font_size="18pt",
    major_label_text_color=INK_SOFT,
    background_fill_color=ELEVATED_BG,
    width=60,
)
p.add_layout(colorbar, "right")

# Typography
p.title.text_font_size = "28pt"
p.title.text_color = INK
p.title.text_font_style = "normal"

p.xaxis.axis_label = "Researcher (Target)"
p.yaxis.axis_label = "Researcher (Source)"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK

p.xaxis.major_label_text_font_size = "15pt"
p.yaxis.major_label_text_font_size = "15pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.major_label_orientation = math.pi / 3

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome via Selenium
W, H = 3600, 3600
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
