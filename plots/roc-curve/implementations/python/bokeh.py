""" anyplot.ai
roc-curve: ROC Curve with AUC
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-09
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


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Simulated ROC curves for three classifiers with different performance levels
np.random.seed(42)

# Generate ROC curve points using sklearn-like simulation
# Using the parametric approach: FPR = t, TPR = t^(1/k) where k controls curve shape
n_points = 200
t = np.linspace(0, 1, n_points)

# Model 1: Strong classifier (AUC ~0.95) - curve bows far towards top-left
k1 = 0.15
fpr_1 = t
tpr_1 = np.power(t, k1)
auc_1 = np.trapezoid(tpr_1, fpr_1)

# Model 2: Medium classifier (AUC ~0.82) - moderate curve
k2 = 0.35
fpr_2 = t
tpr_2 = np.power(t, k2)
auc_2 = np.trapezoid(tpr_2, fpr_2)

# Model 3: Weak classifier (AUC ~0.68) - closer to diagonal
k3 = 0.6
fpr_3 = t
tpr_3 = np.power(t, k3)
auc_3 = np.trapezoid(tpr_3, fpr_3)

# Random classifier reference line
fpr_random = np.array([0, 1])
tpr_random = np.array([0, 1])

# Create ColumnDataSources
source_1 = ColumnDataSource(data={"fpr": fpr_1, "tpr": tpr_1, "model": ["Model A"] * len(fpr_1)})
source_2 = ColumnDataSource(data={"fpr": fpr_2, "tpr": tpr_2, "model": ["Model B"] * len(fpr_2)})
source_3 = ColumnDataSource(data={"fpr": fpr_3, "tpr": tpr_3, "model": ["Model C"] * len(fpr_3)})
source_random = ColumnDataSource(data={"fpr": fpr_random, "tpr": tpr_random})

# Create figure - Square format preferred for equal aspect ratio
p = figure(
    width=3600,
    height=3600,
    title="roc-curve · bokeh · anyplot.ai",
    x_axis_label="False Positive Rate",
    y_axis_label="True Positive Rate",
    x_range=(-0.02, 1.02),
    y_range=(-0.02, 1.02),
    tools="pan,wheel_zoom,box_zoom,reset,save",
    toolbar_location="right",
)

# Plot random classifier reference line (diagonal)
random_line = p.line(
    x="fpr", y="tpr", source=source_random, line_width=3, line_dash="dashed", line_color=INK_SOFT, alpha=0.5
)

# Plot ROC curves with Okabe-Ito colors
line_1 = p.line(x="fpr", y="tpr", source=source_1, line_width=5, line_color=IMPRINT[0], alpha=0.9)
line_2 = p.line(x="fpr", y="tpr", source=source_2, line_width=5, line_color=IMPRINT[1], alpha=0.9)
line_3 = p.line(x="fpr", y="tpr", source=source_3, line_width=5, line_color=IMPRINT[2], alpha=0.9)

# Add HoverTool for interactivity
hover = HoverTool(tooltips=[("FPR", "@fpr{0.00}"), ("TPR", "@tpr{0.00}")])
p.add_tools(hover)

# Create legend with AUC scores
legend = Legend(
    items=[
        (f"Model A (AUC = {auc_1:.2f})", [line_1]),
        (f"Model B (AUC = {auc_2:.2f})", [line_2]),
        (f"Model C (AUC = {auc_3:.2f})", [line_3]),
        ("Random Classifier", [random_line]),
    ],
    location="center",
)

p.add_layout(legend)
legend.label_text_font_size = "22pt"
legend.glyph_height = 30
legend.glyph_width = 30
legend.spacing = 15
legend.padding = 20
legend.background_fill_color = ELEVATED_BG
legend.background_fill_alpha = 0.9
legend.border_line_color = INK_SOFT
legend.border_line_width = 1
legend.label_text_color = INK_SOFT

# Style the plot
p.title.text_font_size = "28pt"
p.title.text_color = INK
p.title.align = "center"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

# Grid styling - subtle
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10
p.xgrid.grid_line_width = 0.8
p.ygrid.grid_line_width = 0.8

# Background and border
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT
p.outline_line_width = 1

# Axis styling
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.axis_line_width = 1
p.yaxis.axis_line_width = 1
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.major_tick_line_width = 1
p.yaxis.major_tick_line_width = 1

# Save as HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome — Selenium 4 / Selenium Manager
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
