"""anyplot.ai
streamgraph-basic: Basic Stream Graph
Library: bokeh | Python 3.13
Quality: pending | Updated: 2026-05-05
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Legend
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette — first series always #009E73
COLORS = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9"]

# Data: monthly streaming hours by music genre over two years
np.random.seed(42)

months = pd.date_range(start="2022-01-01", periods=24, freq="ME")
categories = ["Pop", "Rock", "Hip-Hop", "Electronic", "Jazz", "Classical"]

n_points = len(months)
base = np.linspace(0, 4 * np.pi, n_points)

raw = {
    "Pop": 45 + 18 * np.sin(base) + np.random.randn(n_points) * 3,
    "Rock": 38 + 12 * np.sin(base + 0.8) + np.random.randn(n_points) * 2.5,
    "Hip-Hop": 35 + 22 * np.sin(base + 1.6) + np.random.randn(n_points) * 4,
    "Electronic": 28 + 14 * np.sin(base + 2.4) + np.random.randn(n_points) * 2.5,
    "Jazz": 18 + 10 * np.sin(base + 3.2) + np.random.randn(n_points) * 2,
    "Classical": 14 + 6 * np.sin(base + 4.0) + np.random.randn(n_points) * 1.5,
}

for cat in categories:
    raw[cat] = np.maximum(raw[cat], 5)

df = pd.DataFrame(raw)

# Symmetric baseline — center the stack around zero
values = df[categories].values
total = values.sum(axis=1)
baseline_offset = total / 2

y_bottom = np.zeros_like(values)
y_top = np.zeros_like(values)
for i in range(len(categories)):
    if i == 0:
        y_bottom[:, i] = -baseline_offset
        y_top[:, i] = y_bottom[:, i] + values[:, i]
    else:
        y_bottom[:, i] = y_top[:, i - 1]
        y_top[:, i] = y_bottom[:, i] + values[:, i]

# Smooth interpolation for flowing curves
x_numeric = np.arange(n_points)
n_smooth = n_points * 10
x_smooth = np.linspace(0, n_points - 1, n_smooth)

months_smooth = pd.date_range(start=months.min(), end=months.max(), periods=n_smooth)
y_bottom_smooth = np.zeros((n_smooth, len(categories)))
y_top_smooth = np.zeros((n_smooth, len(categories)))

for i in range(len(categories)):
    deg = min(10, n_points - 1)
    y_bottom_smooth[:, i] = np.polyval(np.polyfit(x_numeric, y_bottom[:, i], deg), x_smooth)
    y_top_smooth[:, i] = np.polyval(np.polyfit(x_numeric, y_top[:, i], deg), x_smooth)

# Plot
p = figure(
    width=4800,
    height=2700,
    title="streamgraph-basic · bokeh · anyplot.ai",
    x_axis_label="Time",
    y_axis_label="Streaming Hours (relative)",
    x_axis_type="datetime",
)

# Font sizes for 4800×2700 px canvas
p.title.text_font_size = "32pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
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

# Draw streamgraph patches
x_values = months_smooth.values
legend_items = []
hover_renderers = []

for i, cat in enumerate(categories):
    xs = np.concatenate([x_values, x_values[::-1]])
    ys = np.concatenate([y_top_smooth[:, i], y_bottom_smooth[:, i][::-1]])

    source = ColumnDataSource(data={"x": xs, "y": ys, "genre": [cat] * len(xs)})
    renderer = p.patch(
        x="x", y="y", source=source, fill_color=COLORS[i], fill_alpha=0.85, line_color=COLORS[i], line_width=2
    )
    legend_items.append((cat, [renderer]))
    hover_renderers.append(renderer)

# HoverTool — shows genre name on hover
hover = HoverTool(renderers=hover_renderers, tooltips=[("Genre", "@genre")])
p.add_tools(hover)

# Legend outside the plot area
legend = Legend(items=legend_items, location="center")
legend.label_text_font_size = "22pt"
legend.label_text_color = INK_SOFT
legend.glyph_height = 40
legend.glyph_width = 40
legend.spacing = 15
legend.background_fill_color = ELEVATED_BG
legend.border_line_color = INK_SOFT
p.add_layout(legend, "right")

p.toolbar_location = "above"

# Save interactive HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome (export_png unavailable in this environment)
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
