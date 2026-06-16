""" anyplot.ai
line-multi: Multi-Line Comparison Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-06
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

# Okabe-Ito palette (first series is #009E73)
COLORS = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data: Monthly sales (thousands) for 4 product lines over 12 months
np.random.seed(42)
months = np.arange(1, 13)

# Generate realistic sales trends for different products
electronics = 45 + np.cumsum(np.random.randn(12) * 3) + months * 2
clothing = 35 + np.cumsum(np.random.randn(12) * 2.5) + np.sin(months * np.pi / 6) * 8
furniture = 25 + np.cumsum(np.random.randn(12) * 2) + months * 0.5
groceries = 55 + np.cumsum(np.random.randn(12) * 1.5)

# Create figure (4800 x 2700 px for 16:9)
p = figure(
    width=4800,
    height=2700,
    title="line-multi · bokeh · anyplot.ai",
    x_axis_label="Month",
    y_axis_label="Sales (thousands $)",
)

# Series data
series_names = ["Electronics", "Clothing", "Furniture", "Groceries"]
series_data = [electronics, clothing, furniture, groceries]
line_dashes = ["solid", "solid", "dashed", "dashed"]

# Plot each series with lines and markers
renderers = []
for name, data, color, dash in zip(series_names, series_data, COLORS, line_dashes, strict=True):
    source = ColumnDataSource(
        data={
            "x": months,
            "y": data,
            "month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        }
    )

    # Line
    line = p.line(x="x", y="y", source=source, line_width=5, line_color=color, line_dash=dash, line_alpha=0.9)

    # Markers
    scatter = p.scatter(x="x", y="y", source=source, size=18, color=color, alpha=0.9)

    # HoverTool for interactivity
    hover = HoverTool(renderers=[scatter], tooltips=[("Month", "@month"), ("Sales", "$@y{0,0.0}k")])
    p.add_tools(hover)

    renderers.append((name, [line, scatter]))

# Create legend
legend = Legend(items=renderers, location="top_left")
legend.label_text_font_size = "20pt"
legend.glyph_height = 30
legend.glyph_width = 30
legend.spacing = 10
legend.padding = 20
legend.background_fill_alpha = 0.9
p.add_layout(legend, "right")

# Title styling
p.title.text_font_size = "28pt"
p.title.align = "center"
p.title.text_color = INK

# Axis label styling
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

# Axis and grid styling
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

# Legend styling
if p.legend:
    p.legend.background_fill_color = ELEVATED_BG
    p.legend.border_line_color = INK_SOFT
    p.legend.label_text_color = INK_SOFT

# Background and outline
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT
p.outline_line_width = 1

# Month labels
p.xaxis.ticker = list(range(1, 13))
p.xaxis.major_label_overrides = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec",
}

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome
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
