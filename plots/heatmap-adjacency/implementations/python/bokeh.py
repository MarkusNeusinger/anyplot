""" anyplot.ai
heatmap-adjacency: Network Adjacency Matrix Heatmap
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-15
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
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import BasicTicker, ColorBar, ColumnDataSource, LinearColorMapper
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

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]


def _lerp_hex(c0, c1, t):
    a = [int(c0[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(c1[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b, strict=False))


# Imprint sequential ramp (single polarity): green to blue
IMPRINT_SEQ = [_lerp_hex("#009E73", "#4467A3", t / 255) for t in range(256)]

# Columns: set these to your table's column names
SOURCE = "Source researcher"  # role: source
TARGET = "Target researcher"  # role: target
WEIGHT = "Connection strength"  # role: weight

# Data: replace this block with your own edge list, for example df = pd.read_csv("edges.csv")
# 24 researchers in 4 departments (ordered by department); each undirected edge listed once
np.random.seed(42)
dept_codes = ["Phy", "Chem", "Bio", "Math"]
names = [f"{code}{i:02d}" for code in dept_codes for i in range(1, 7)]
dept_of = {name: k // 6 for k, name in enumerate(names)}
edges = []
for a in range(len(names)):
    for b in range(a + 1, len(names)):
        same_dept = dept_of[names[a]] == dept_of[names[b]]
        if same_dept and np.random.rand() < 0.80:
            edges.append((names[a], names[b], np.random.uniform(0.5, 1.0)))
        elif not same_dept and np.random.rand() < 0.08:
            edges.append((names[a], names[b], np.random.uniform(0.1, 0.4)))
df = pd.DataFrame(edges, columns=[SOURCE, TARGET, WEIGHT])

# Plot: reads only df and the constants above
# Node order: first appearance, sources first, which keeps departments contiguous
nodes = list(pd.unique(pd.concat([df[SOURCE], df[TARGET]], ignore_index=True)))
# Undirected graph: fill both triangles
cells = pd.concat(
    [df.rename(columns={SOURCE: "row", TARGET: "col"}), df.rename(columns={SOURCE: "col", TARGET: "row"})],
    ignore_index=True,
)
source = ColumnDataSource(cells)

mapper = LinearColorMapper(palette=IMPRINT_SEQ, low=df[WEIGHT].min(), high=df[WEIGHT].max(), nan_color=NAN_COLOR)

p = figure(
    width=2400,
    height=2400,
    x_range=nodes,
    y_range=list(reversed(nodes)),
    toolbar_location=None,
    title="Researcher Collaboration · heatmap-adjacency · python · bokeh · anyplot.ai",
    x_axis_label=TARGET,
    y_axis_label=SOURCE,
    min_border_top=90,
    min_border_bottom=60,
    min_border_left=60,
    min_border_right=60,
)

# Absent edges: background cells in a distinct tone, so they never read as weak edges
grid = pd.MultiIndex.from_product([nodes, nodes], names=["row", "col"]).to_frame(index=False)
p.rect(x="col", y="row", width=1, height=1, source=ColumnDataSource(grid), fill_color=NAN_COLOR, line_color=None)

# Edge cells colored by weight
p.rect(
    x="col",
    y="row",
    width=1,
    height=1,
    source=source,
    fill_color={"field": WEIGHT, "transform": mapper},
    line_color=None,
)

colorbar = ColorBar(
    color_mapper=mapper,
    ticker=BasicTicker(desired_num_ticks=6),
    label_standoff=16,
    border_line_color=None,
    location=(0, 0),
    title=WEIGHT,
    title_text_font_size="22pt",
    title_text_color=INK,
    major_label_text_font_size="20pt",
    major_label_text_color=INK_SOFT,
    background_fill_color=PAGE_BG,
    width=50,
)
p.add_layout(colorbar, "right")

# Style
p.title.text_font_size = "34pt"
p.title.text_color = INK
p.title.text_font_style = "normal"

p.xaxis.axis_label_text_font_size = "26pt"
p.yaxis.axis_label_text_font_size = "26pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK

p.xaxis.major_label_text_font_size = "20pt"
p.yaxis.major_label_text_font_size = "20pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.major_label_orientation = math.pi / 3

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
W, H = 2400, 2400
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
