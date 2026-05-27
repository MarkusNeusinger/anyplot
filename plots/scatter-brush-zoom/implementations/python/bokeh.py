""" anyplot.ai
scatter-brush-zoom: Interactive Scatter Plot with Brush Selection and Zoom
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-16
"""

import os
import site
import sys
import time
from pathlib import Path


# Ensure site-packages is at the front to avoid shadowing the bokeh package
site_packages_list = site.getsitepackages() or []
for sp in reversed(site_packages_list):
    sys.path.insert(0, sp)

import numpy as np  # noqa: E402
from bokeh.io import output_file, save  # noqa: E402
from bokeh.models import (  # noqa: E402
    BoxSelectTool,
    ColumnDataSource,
    HoverTool,
    Legend,
    LegendItem,
    PanTool,
    ResetTool,
    WheelZoomTool,
)
from bokeh.plotting import figure  # noqa: E402
from bokeh.transform import factor_cmap  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Generate clustered data for demonstrating brush selection
np.random.seed(42)

n_per_cluster = 75
clusters = []
labels = ["Cluster A", "Cluster B", "Cluster C", "Cluster D"]
centers = [(20, 30), (60, 70), (25, 75), (70, 25)]
spreads = [8, 10, 6, 9]

for i, (cx, cy) in enumerate(centers):
    x_vals = np.random.normal(cx, spreads[i], n_per_cluster)
    y_vals = np.random.normal(cy, spreads[i], n_per_cluster)
    cluster = np.full(n_per_cluster, labels[i])
    clusters.append((x_vals, y_vals, cluster))

x = np.concatenate([c[0] for c in clusters])
y = np.concatenate([c[1] for c in clusters])
category = np.concatenate([c[2] for c in clusters])

# Create ColumnDataSource
source = ColumnDataSource(data={"x": x, "y": y, "category": category})

# Plot
p = figure(
    width=4800,
    height=2700,
    title="scatter-brush-zoom · bokeh · anyplot.ai",
    x_axis_label="Measurement X",
    y_axis_label="Measurement Y",
    tools="",
    output_backend="webgl",
)

# Interactive tools
box_select = BoxSelectTool()
wheel_zoom = WheelZoomTool()
pan = PanTool()
reset = ResetTool()
hover = HoverTool(tooltips=[("Category", "@category"), ("X", "@x{0.00}"), ("Y", "@y{0.00}")])

p.add_tools(box_select, wheel_zoom, pan, reset, hover)
p.toolbar.active_drag = box_select
p.toolbar.active_scroll = wheel_zoom

# Color mapping with Okabe-Ito palette
color_map = factor_cmap("category", palette=IMPRINT, factors=labels)

# Scatter plot with selection styling
p.scatter(
    "x",
    "y",
    source=source,
    size=15,
    fill_color=color_map,
    line_color=PAGE_BG,
    line_width=2,
    alpha=0.8,
    selection_fill_color=color_map,
    selection_line_color=INK,
    selection_line_width=4,
    selection_alpha=1.0,
    nonselection_fill_color=color_map,
    nonselection_line_color=PAGE_BG,
    nonselection_alpha=0.2,
)

# Style title
p.title.text_font_size = "28pt"
p.title.text_color = INK

# Style axes
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

# Spine styling
p.outline_line_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# Grid styling
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

# Background
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG

# Legend
legend_items = []
for i, label in enumerate(labels):
    r = p.scatter([], [], fill_color=IMPRINT[i], line_color=PAGE_BG, size=15)
    legend_items.append(LegendItem(label=label, renderers=[r]))

legend = Legend(items=legend_items, location="top_right")
legend.label_text_font_size = "18pt"
legend.label_text_color = INK_SOFT
legend.background_fill_color = ELEVATED_BG
legend.border_line_color = INK_SOFT
legend.glyph_height = 25
legend.glyph_width = 25
legend.spacing = 12
legend.padding = 15
p.add_layout(legend)

# Margins
p.min_border_left = 100
p.min_border_bottom = 100
p.min_border_right = 50
p.min_border_top = 80

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
