"""anyplot.ai
strip-basic: Basic Strip Plot
Library: bokeh | Python 3.13
Quality: pending | Updated: 2026-05-04
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
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

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data - Survey response scores by department
np.random.seed(42)

categories = ["Engineering", "Marketing", "Sales", "HR"]
n_per_category = [45, 38, 52, 30]

data = {
    "Engineering": np.clip(np.random.normal(7.2, 1.5, n_per_category[0]), 1, 10),
    "Marketing": np.clip(np.random.normal(6.8, 1.8, n_per_category[1]), 1, 10),
    "Sales": np.clip(np.random.normal(7.5, 1.2, n_per_category[2]), 1, 10),
    "HR": np.clip(np.random.normal(8.0, 1.0, n_per_category[3]), 1, 10),
}

# Build arrays for plotting with jitter
x_values = []
y_values = []
colors = []
color_map = dict(zip(categories, OKABE_ITO, strict=True))

jitter_width = 0.25

for i, cat in enumerate(categories):
    values = data[cat]
    n = len(values)
    jittered_x = i + np.random.uniform(-jitter_width, jitter_width, n)
    x_values.extend(jittered_x)
    y_values.extend(values)
    colors.extend([color_map[cat]] * n)

source = ColumnDataSource(data={"x": x_values, "y": y_values, "color": colors})

# Plot
p = figure(
    width=4800,
    height=2700,
    title="strip-basic · bokeh · anyplot.ai",
    x_axis_label="Department",
    y_axis_label="Survey Score (1–10)",
    x_range=(-0.5, len(categories) - 0.5),
    y_range=(0, 11),
)

p.scatter(x="x", y="y", source=source, size=28, color="color", alpha=0.6, line_color=PAGE_BG, line_width=2)

# Mean reference lines — one legend entry shared across all categories
for i, cat in enumerate(categories):
    mean_val = float(np.mean(data[cat]))
    legend_kw = {"legend_label": "Group Mean"} if i == 0 else {}
    p.line(x=[i - 0.35, i + 0.35], y=[mean_val, mean_val], line_color=INK_SOFT, line_width=5, **legend_kw)

# Text sizes for 4800×2700 px
p.title.text_font_size = "42pt"
p.xaxis.axis_label_text_font_size = "32pt"
p.yaxis.axis_label_text_font_size = "32pt"
p.xaxis.major_label_text_font_size = "26pt"
p.yaxis.major_label_text_font_size = "26pt"

# Categorical tick labels on x-axis
p.xaxis.ticker = list(range(len(categories)))
p.xaxis.major_label_overrides = dict(enumerate(categories))

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
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10

if p.legend:
    p.legend.background_fill_color = ELEVATED_BG
    p.legend.border_line_color = INK_SOFT
    p.legend.label_text_color = INK_SOFT
    p.legend.label_text_font_size = "22pt"
    p.legend.location = "top_right"

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome (use taller window to capture x-axis labels)
W, H = 4800, 3000
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
