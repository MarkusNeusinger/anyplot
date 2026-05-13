""" anyplot.ai
line-stepwise: Step Line Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-13
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
BRAND = "#009E73"

# Data - CPU usage readings over time with discrete state changes
np.random.seed(42)
n_points = 24
hours = np.arange(n_points)

# Realistic CPU usage that stays at levels then jumps
# Removed random noise to better represent discrete state changes
cpu_usage = np.array(
    [35, 42, 55, 72, 85, 92, 88, 70, 55, 40, 32, 28, 35, 52, 78, 88, 95, 90, 75, 60, 48, 42, 32, 25], dtype=float
)

# Create step function data by duplicating points for post-step behavior
# For 'post' step style: value changes after the point
x_step = []
y_step = []
for i in range(len(hours)):
    x_step.append(hours[i])
    y_step.append(cpu_usage[i])
    if i < len(hours) - 1:
        x_step.append(hours[i + 1])
        y_step.append(cpu_usage[i])

# Create data source for the step line
source = ColumnDataSource(data={"x": x_step, "y": y_step})

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="line-stepwise · bokeh · anyplot.ai",
    x_axis_label="Hour of Day",
    y_axis_label="CPU Usage (%)",
)

# Plot step line
p.line(x="x", y="y", source=source, line_width=4, line_color=BRAND, line_alpha=0.9)

# Add markers at actual data points for clarity - larger for visibility
marker_source = ColumnDataSource(data={"x": hours, "y": cpu_usage})
p.scatter(x="x", y="y", source=marker_source, size=16, color=BRAND, alpha=0.9)

# Add HoverTool for enhanced interactivity
hover = HoverTool(tooltips=[("Hour", "@x{0}"), ("Usage", "@y{0.0}%")])
p.add_tools(hover)

# Style text sizes for large canvas
p.title.text_font_size = "28pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_color = INK_SOFT

# Theme-adaptive styling
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Subtle grid with theme-adaptive colors
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

# Legend styling if present
if p.legend:
    p.legend.background_fill_color = ELEVATED_BG
    p.legend.border_line_color = INK_SOFT
    p.legend.label_text_color = INK_SOFT

# Axis ranges
p.y_range.start = 0
p.y_range.end = 105

# Save as HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome using Selenium
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
