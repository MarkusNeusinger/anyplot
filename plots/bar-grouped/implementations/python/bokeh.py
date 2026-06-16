""" anyplot.ai
bar-grouped: Grouped Bar Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-06
"""

import os
import time
from pathlib import Path

from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, FactorRange, Legend, LegendItem
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series is always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - Quarterly revenue by product line (in thousands)
categories = ["Q1", "Q2", "Q3", "Q4"]
groups = ["Electronics", "Clothing", "Home & Garden"]

data = {"Electronics": [245, 278, 312, 385], "Clothing": [180, 165, 210, 295], "Home & Garden": [125, 198, 245, 178]}

# Create factors for grouped bars
x = [(cat, group) for cat in categories for group in groups]
values = [data[group][i] for i, cat in enumerate(categories) for group in groups]
colors = [IMPRINT[groups.index(factor[1])] for factor in x]

source = ColumnDataSource(data={"x": x, "values": values, "color": colors})

# Create figure with categorical axis
p = figure(
    x_range=FactorRange(*x, group_padding=0.3),
    width=4800,
    height=2700,
    title="Quarterly Revenue by Product · bar-grouped · bokeh · anyplot.ai",
)

# Create grouped bars with theme-adaptive colors from source
bars = p.vbar(x="x", top="values", width=0.85, source=source, fill_color="color", line_color="white", line_width=3)

# Add value labels on top of bars
for factor, value in zip(x, values, strict=True):
    p.text(
        x=[factor],
        y=[value + 5],
        text=[f"${value}K"],
        text_align="center",
        text_baseline="bottom",
        text_font_size="16pt",
        text_color=INK,
    )

# Title styling
p.title.text_font_size = "28pt"
p.title.text_color = INK

# X-axis styling
p.xaxis.axis_label = "Quarter"
p.xaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_label_text_color = INK

# Y-axis styling
p.yaxis.axis_label = "Revenue ($ Thousands)"
p.yaxis.axis_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_color = INK_SOFT
p.yaxis.axis_label_text_color = INK

# Grid styling
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10

# Background and outline
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# Create legend with correct colors for each group
legend_items = [
    LegendItem(label=groups[0], renderers=[bars], index=0),
    LegendItem(label=groups[1], renderers=[bars], index=3),
    LegendItem(label=groups[2], renderers=[bars], index=6),
]
legend = Legend(items=legend_items, location="top_right", orientation="vertical")
legend.label_text_font_size = "16pt"
legend.label_text_color = INK_SOFT
legend.background_fill_color = ELEVATED_BG
legend.background_fill_alpha = 1.0
legend.border_line_color = INK_SOFT
legend.glyph_height = 20
legend.glyph_width = 20
legend.spacing = 10
legend.padding = 15
p.add_layout(legend)

# Set y-axis range to accommodate labels
p.y_range.start = 0
p.y_range.end = 430

# Save HTML output
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
