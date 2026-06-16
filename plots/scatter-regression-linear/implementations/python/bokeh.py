""" anyplot.ai
scatter-regression-linear: Scatter Plot with Linear Regression
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-06
"""

import os
import sys
import time
from pathlib import Path


sys.path.pop(0)

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import Band, ColumnDataSource, HoverTool, Label
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Data - Study hours vs exam scores
np.random.seed(42)
n_points = 80
x = np.random.uniform(1, 10, n_points)  # Study hours
noise = np.random.normal(0, 7, n_points)
y = 45 + 5 * x + noise  # Exam scores
y = np.clip(y, 0, 100)  # Ensure realistic scores (0-100%)

# Linear regression calculation
slope, intercept = np.polyfit(x, y, 1)
y_pred = slope * x + intercept

# Calculate R-squared
ss_res = np.sum((y - y_pred) ** 2)
ss_tot = np.sum((y - np.mean(y)) ** 2)
r_squared = 1 - (ss_res / ss_tot)

# Calculate 95% confidence interval
n = len(x)
x_mean = np.mean(x)
se = np.sqrt(ss_res / (n - 2))
t_value = 1.99  # t-value for 95% CI with ~78 degrees of freedom

# Create sorted x values for smooth regression line and confidence band
x_line = np.linspace(x.min(), x.max(), 100)
y_line = slope * x_line + intercept

# Standard error of prediction for confidence interval
se_y = se * np.sqrt(1 / n + (x_line - x_mean) ** 2 / np.sum((x - x_mean) ** 2))
ci_upper = y_line + t_value * se_y
ci_lower = y_line - t_value * se_y

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="scatter-regression-linear · bokeh · anyplot.ai",
    x_axis_label="Study Hours",
    y_axis_label="Exam Score (%)",
    toolbar_location="right",
)

# Create data sources
scatter_source = ColumnDataSource(data={"x": x, "y": y, "y_pred": y_pred})
line_source = ColumnDataSource(data={"x": x_line, "y": y_line})
band_source = ColumnDataSource(data={"x": x_line, "lower": ci_lower, "upper": ci_upper})

# Add confidence interval band
band = Band(
    base="x",
    lower="lower",
    upper="upper",
    source=band_source,
    fill_color=IMPRINT[0],
    fill_alpha=0.15,
    line_color=IMPRINT[0],
    line_alpha=0.2,
    line_width=1,
)
p.add_layout(band)

# Add regression line
p.line("x", "y", source=line_source, line_color=IMPRINT[1], line_width=5, legend_label="Linear Regression")

# Add scatter points with hover tooltip
scatter = p.scatter(
    "x", "y", source=scatter_source, size=16, color=IMPRINT[0], alpha=0.65, legend_label="Data Points"
)

# Add hover tooltip
hover = HoverTool(tooltips=[("Study Hours", "@x{0.0}"), ("Exam Score", "@y{0.0}"), ("Predicted", "@y_pred{0.0}")])
p.add_tools(hover)

# Add R² and equation annotation
r2_text = f"R² = {r_squared:.3f}"
equation_text = f"y = {slope:.2f}x + {intercept:.2f}"
annotation = Label(
    x=1.5,
    y=92,
    text=f"{equation_text}\n{r2_text}",
    text_font_size="22pt",
    text_color=INK,
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.85,
    border_line_color=INK_SOFT,
)
p.add_layout(annotation)

# Styling - theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

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

p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

p.legend.label_text_font_size = "18pt"
p.legend.location = "bottom_right"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT

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
