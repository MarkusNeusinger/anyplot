""" anyplot.ai
line-styled: Styled Line Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-12
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Legend
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
IMPRINT = [
    "#009E73",  # bluish green (brand)
    "#C475FD",  # vermillion
    "#4467A3",  # blue
    "#BD8233",  # reddish purple
]

# Data - Monthly performance metrics over a year
np.random.seed(42)
months = np.arange(1, 13)

# Generate realistic trending data for different metrics
base = np.array([65, 68, 72, 75, 78, 82, 85, 84, 80, 77, 74, 70])
cpu_usage = base + np.random.randn(12) * 3
memory_usage = base * 0.85 + np.random.randn(12) * 4 + 10
disk_io = base * 0.7 + np.random.randn(12) * 5 + 20
network = base * 1.1 + np.random.randn(12) * 2 - 5

# Create ColumnDataSource
source = ColumnDataSource(
    data={"month": months, "cpu": cpu_usage, "memory": memory_usage, "disk": disk_io, "network": network}
)

# Create figure (4800 × 2700 px)
p = figure(
    width=4800,
    height=2700,
    title="line-styled · bokeh · anyplot.ai",
    x_axis_label="Month",
    y_axis_label="Utilization (%)",
)

# Define line styles and colors
line_styles = ["solid", [20, 10], [4, 8], [20, 8, 4, 8]]
series_names = ["CPU Usage", "Memory Usage", "Disk I/O", "Network Traffic"]
y_columns = ["cpu", "memory", "disk", "network"]

# Create legend items
legend_items = []

for col, style, color, name in zip(y_columns, line_styles, IMPRINT, series_names, strict=True):
    # Add line with appropriate style
    line = p.line(x="month", y=col, source=source, line_width=6, color=color, line_dash=style)

    # Add scatter points for better visibility
    scatter = p.scatter(x="month", y=col, source=source, size=25, color=color, alpha=0.9)

    legend_items.append((name, [line, scatter]))

# Create and configure legend
legend = Legend(items=legend_items, location="top_left")
legend.label_text_font_size = "28pt"
legend.label_text_color = INK_SOFT
legend.glyph_height = 40
legend.glyph_width = 80
legend.spacing = 15
legend.padding = 20
legend.background_fill_alpha = 0.95
legend.background_fill_color = ELEVATED_BG
legend.border_line_color = INK_SOFT
legend.border_line_width = 2
p.add_layout(legend, "center")

# Style configuration - larger fonts for 4800x2700 canvas
p.title.text_font_size = "48pt"
p.title.text_color = INK
p.title.align = "center"
p.xaxis.axis_label_text_font_size = "36pt"
p.yaxis.axis_label_text_font_size = "36pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "28pt"
p.yaxis.major_label_text_font_size = "28pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

# Grid styling
p.grid.grid_line_alpha = 0.10
p.grid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

# Axis styling
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

# Background and outline
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Axis line styling
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.major_tick_line_width = 2
p.yaxis.major_tick_line_width = 2

# Save as HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with Selenium (headless Chrome)
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
