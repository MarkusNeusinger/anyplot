""" anyplot.ai
bar-spine: Spine Plot for Two-Variable Proportions
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 85/100 | Created: 2026-05-08
"""

import os
import sys
import time
from pathlib import Path


# Prevent this file (bokeh.py) from shadowing the installed bokeh package
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.normpath(p or ".") != os.path.normpath(_here)]

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, FixedTicker, HoverTool, NumeralTickFormatter
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data: project completion status by department
np.random.seed(42)
departments = ["Engineering", "Marketing", "Sales", "Operations"]
statuses = ["On Time", "Delayed", "Cancelled"]

# Counts per (department, status) — columns map to statuses
counts = np.array(
    [
        [85, 35, 10],  # Engineering: 130 projects
        [50, 15, 5],  # Marketing:    70 projects
        [110, 30, 10],  # Sales:       150 projects
        [68, 10, 2],  # Operations:   80 projects
    ]
)

# Marginal totals and normalised bar widths
dept_totals = counts.sum(axis=1)
grand_total = int(dept_totals.sum())
bar_widths = dept_totals / grand_total
bar_lefts = np.concatenate([[0.0], np.cumsum(bar_widths[:-1])])
bar_rights = bar_lefts + bar_widths
x_centers = (bar_lefts + bar_rights) / 2

# Conditional proportions within each bar
cond_props = counts / dept_totals[:, np.newaxis]

# Build figure
p = figure(
    width=4800,
    height=2700,
    x_range=(0.0, 1.0),
    y_range=(0.0, 1.0),
    title="Project Completion Status by Department · bar-spine · bokeh · anyplot.ai",
    toolbar_location=None,
)

# Draw one quad call per status so legend_label works correctly
for j, status in enumerate(statuses):
    bottoms = [float(cond_props[i, :j].sum()) for i in range(len(departments))]
    tops = [float(cond_props[i, : j + 1].sum()) for i in range(len(departments))]

    source = ColumnDataSource(
        data={
            "left": list(bar_lefts),
            "right": list(bar_rights),
            "bottom": bottoms,
            "top": tops,
            "department": departments,
            "status": [status] * len(departments),
            "count": [int(counts[i, j]) for i in range(len(departments))],
            "pct": [f"{cond_props[i, j]:.1%}" for i in range(len(departments))],
        }
    )

    p.quad(
        left="left",
        right="right",
        bottom="bottom",
        top="top",
        color=IMPRINT[j],
        line_color=PAGE_BG,
        line_width=2,
        alpha=0.92,
        legend_label=status,
        source=source,
    )

# Hover tool
hover = HoverTool(
    tooltips=[("Department", "@department"), ("Status", "@status"), ("Projects", "@count"), ("Share", "@pct")]
)
p.add_tools(hover)

# Percentage labels for segments >= 8% of bar height
label_x, label_y, label_text = [], [], []
for i in range(len(departments)):
    for j in range(len(statuses)):
        prop = float(cond_props[i, j])
        if prop >= 0.08:
            bottom = float(cond_props[i, :j].sum())
            label_x.append(float(x_centers[i]))
            label_y.append(bottom + prop / 2)
            label_text.append(f"{prop:.0%}")

p.text(
    x=label_x,
    y=label_y,
    text=label_text,
    text_align="center",
    text_baseline="middle",
    text_font_size="16pt",
    text_font_style="bold",
    text_color="#FFFFFF",
)

# X-axis: fixed ticks centred on each bar, labelled with department name
p.xaxis.ticker = FixedTicker(ticks=[float(c) for c in x_centers])
p.xaxis.major_label_overrides = {float(x_centers[i]): departments[i] for i in range(len(departments))}

# Y-axis formatted as percentages
p.yaxis.formatter = NumeralTickFormatter(format="0%")

# Axis labels
p.xaxis.axis_label = "Department  (bar width ∝ project count)"
p.yaxis.axis_label = "Proportion of Projects"

# Text sizes
p.title.text_font_size = "28pt"
p.title.text_font_style = "normal"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

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
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10

# Legend styling
p.legend.location = "top_right"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT
p.legend.label_text_font_size = "18pt"
p.legend.padding = 20
p.legend.spacing = 12

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome via Selenium
W, H = 4800, 2700
# Use a taller window to avoid browser chrome clipping the bottom axis labels
WIN_H = H + 200
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{WIN_H}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, WIN_H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
