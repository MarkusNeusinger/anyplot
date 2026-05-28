""" anyplot.ai
scatter-regression-lowess: Scatter Plot with LOWESS Regression
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-14
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
from statsmodels.nonparametric.smoothers_lowess import lowess


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"  # Okabe-Ito position 1
ACCENT = "#C475FD"  # Okabe-Ito position 2 for LOWESS curve

# Data: Simulate a complex non-linear relationship (e.g., temperature vs enzyme activity)
np.random.seed(42)
n = 200

# Create x values (temperature in Celsius)
x = np.linspace(10, 50, n) + np.random.normal(0, 1, n)
x = np.sort(x)

# Create y with complex non-linear relationship (enzyme activity %)
# Activity increases, peaks around 35°C, then decreases (typical enzyme behavior)
y_true = 20 + 60 * np.exp(-0.5 * ((x - 35) / 8) ** 2)
y = y_true + np.random.normal(0, 5, n)

# Calculate LOWESS regression
lowess_result = lowess(y, x, frac=0.4)
x_lowess = lowess_result[:, 0]
y_lowess = lowess_result[:, 1]

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="scatter-regression-lowess · bokeh · anyplot.ai",
    x_axis_label="Temperature (°C)",
    y_axis_label="Enzyme Activity (%)",
)

# Scatter points with HoverTool
source_scatter = ColumnDataSource(data={"x": x, "y": y})
scatter = p.scatter(x="x", y="y", source=source_scatter, size=18, color=BRAND, alpha=0.6, legend_label="Data Points")

# Add hover tool for interactivity
hover = HoverTool(tooltips=[("Temperature", "@x{0.0}°C"), ("Activity", "@y{0.0}%")], renderers=[scatter])
p.add_tools(hover)

# LOWESS curve
source_lowess = ColumnDataSource(data={"x": x_lowess, "y": y_lowess})
p.line(x="x", y="y", source=source_lowess, line_width=5, color=ACCENT, legend_label="LOWESS Fit")

# Styling - larger text for 4800x2700 canvas
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

# Grid styling - solid, subtle
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

# Background and border colors
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Axis styling
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# Legend styling - increased size for canvas scale
p.legend.label_text_font_size = "18pt"
p.legend.label_text_color = INK_SOFT
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.location = "top_right"

# Save HTML output
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
