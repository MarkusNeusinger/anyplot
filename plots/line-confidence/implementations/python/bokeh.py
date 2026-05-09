"""pyplots.ai
line-confidence: Line Plot with Confidence Interval
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Regenerated: 2025-05-09
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Legend
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme-adaptive colors
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Simulating model predictions with 95% confidence interval
np.random.seed(42)
x = np.linspace(0, 10, 50)

# True underlying function with some curvature
y_true = 2 + 0.5 * x + 0.1 * x**2

# Add noise to create observed "predictions"
y = y_true + np.random.normal(0, 0.5, len(x))

# Confidence interval (widens slightly over prediction horizon)
uncertainty = 0.8 + 0.15 * x
y_lower = y - 1.96 * uncertainty
y_upper = y + 1.96 * uncertainty

# Create ColumnDataSource
source = ColumnDataSource(data={"x": x, "y": y, "y_lower": y_lower, "y_upper": y_upper})

# Create figure (4800 x 2700 px for 16:9 aspect ratio)
p = figure(
    width=4800,
    height=2700,
    title="line-confidence · bokeh · pyplots.ai",
    x_axis_label="Time (units)",
    y_axis_label="Predicted Value",
)

# Style the plot - scaled for large canvas
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Add confidence band using varea
band = p.varea(x="x", y1="y_lower", y2="y_upper", source=source, fill_color="#009E73", fill_alpha=0.3)

# Add central trend line
line = p.line(x="x", y="y", source=source, line_color="#009E73", line_width=4)

# Add HoverTool for interactivity
hover = HoverTool(tooltips=[("Time", "@x{0.00}"), ("Prediction", "@y{0.00}")])
p.add_tools(hover)

# Add legend with improved placement
legend = Legend(items=[("Prediction", [line]), ("95% Confidence Interval", [band])], location="bottom_right")
legend.label_text_font_size = "18pt"
legend.glyph_height = 30
legend.glyph_width = 30
legend.spacing = 15
legend.padding = 20
legend.background_fill_alpha = 0.9
p.add_layout(legend)

# Theme-adaptive styling
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
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

if p.legend:
    p.legend.background_fill_color = ELEVATED_BG
    p.legend.border_line_color = INK_SOFT
    p.legend.label_text_color = INK_SOFT

# Write the interactive HTML (also a required catalog artifact)
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot it with headless Chrome — Selenium 4 / Selenium Manager
# auto-resolves a working driver for the system Chrome.
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
time.sleep(3)  # let bokeh's JS render the canvas
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
