"""anyplot.ai
scatter-basic: Basic Scatter Plot
Library: bokeh | Python 3.13
Quality: pending | Updated: 2026-06-25
"""

import os
import sys
import time
from pathlib import Path


# Remove script directory from sys.path so 'import bokeh' finds the installed
# package rather than this file (bokeh.py would shadow itself otherwise).
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _script_dir]

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
BRAND = "#009E73"  # Imprint palette position 1 — ALWAYS first series

# Data — study hours vs exam scores, moderate positive correlation
np.random.seed(42)
n_points = 180
study_hours = np.random.uniform(0.8, 9.6, n_points)
exam_scores = study_hours * 7.2 + np.random.normal(0, 6.5, n_points) + 26
exam_scores = np.clip(exam_scores, 18, 99)

source = ColumnDataSource(data={"study_hours": study_hours, "exam_scores": exam_scores})

# Plot — 3200×1800 canonical landscape canvas
W, H = 3200, 1800
title = "scatter-basic · python · bokeh · anyplot.ai"

p = figure(
    width=W,
    height=H,
    title=title,
    x_axis_label="Study Hours per Day",
    y_axis_label="Exam Score (%)",
    toolbar_location=None,
    x_range=(0, 10.5),
    y_range=(10, 104),
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

scatter_renderer = p.scatter(
    x="study_hours", y="exam_scores", source=source, size=28, color=BRAND, alpha=0.7, line_color=PAGE_BG, line_width=1.2
)

# HoverTool — Bokeh's distinctive interactive feature (HTML only; PNG stays clean)
hover = HoverTool(
    renderers=[scatter_renderer],
    tooltips=[("Study Hours", "@study_hours{0.1} hrs"), ("Exam Score", "@exam_scores{0.0}%")],
)
p.add_tools(hover)

# Typography — bokeh.md canonical values for 3200×1800 canvas
p.title.text_font_size = "50pt"
p.title.text_font_style = "bold"
p.title.text_color = INK
p.title.align = "center"

p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_font_style = "normal"
p.yaxis.axis_label_text_font_style = "normal"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.axis_label_standoff = 28
p.yaxis.axis_label_standoff = 28

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Grid — both axes for scatter (style guide), subtle weight
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10
p.xgrid.grid_line_width = 1
p.ygrid.grid_line_width = 1

p.xaxis.ticker.desired_num_ticks = 10
p.yaxis.ticker.desired_num_ticks = 8

# Save — HTML first (interactive catalog artifact), then PNG via Selenium
output_file(f"plot-{THEME}.html", title="scatter-basic · python · bokeh · anyplot.ai")
save(p)

opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H + 200}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
# Force exact viewport via CDP so browser chrome doesn't steal pixels
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
