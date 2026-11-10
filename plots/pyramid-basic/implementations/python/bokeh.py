""" anyplot.ai
pyramid-basic: Basic Pyramid Chart
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-10
"""

import math
import os
import time
from pathlib import Path

import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, CustomJSTickFormatter, HoverTool, Range1d, Span
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
AGE_GROUP = "Age group"  # role: category
MALE = "Male"  # role: value_left
FEMALE = "Female"  # role: value_right
VALUE_LABEL = "Population (thousands)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("population.csv")
df = pd.DataFrame(
    {
        AGE_GROUP: ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"],
        MALE: [45, 52, 68, 82, 75, 65, 48, 32, 15],
        FEMALE: [43, 50, 72, 85, 78, 70, 55, 40, 22],
    }
)

# Plot: reads only df and the constants above
categories = list(df[AGE_GROUP])
limit = math.ceil(max(df[MALE].max(), df[FEMALE].max()) * 1.1 / 10) * 10  # one symmetric scale

p = figure(
    width=3200,
    height=1800,
    y_range=categories,
    x_range=Range1d(-limit, limit),
    title="pyramid-basic · python · bokeh · anyplot.ai",
    x_axis_label=VALUE_LABEL,
    y_axis_label=AGE_GROUP,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

sides = [(MALE, -1, IMPRINT_PALETTE[0]), (FEMALE, 1, IMPRINT_PALETTE[1])]
for name, sign, color in sides:
    source = ColumnDataSource(data={"age": categories, "bar": sign * df[name], "value": df[name]})
    bars = p.hbar(y="age", right="bar", height=0.7, source=source, color=color, alpha=0.85, legend_label=name)
    p.add_tools(HoverTool(renderers=[bars], tooltips=[(AGE_GROUP, "@age"), (name, "@value{0,0} thousand")]))

# Shared central axis
p.add_layout(Span(location=0, dimension="height", line_color=INK_SOFT, line_width=3, line_alpha=0.5))

# Magnitudes on both sides instead of negative numbers on the left
p.xaxis.formatter = CustomJSTickFormatter(code="return Math.abs(tick).toString()")

# Style
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.title.text_color = INK
p.title.text_font_size = "50pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10
p.xgrid.grid_line_dash = [6, 4]
p.ygrid.grid_line_dash = [6, 4]

p.legend.location = "bottom_right"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT
p.legend.label_text_font_size = "34pt"
p.legend.background_fill_alpha = 0.9

# Save
output_file(f"plot-{THEME}.html")
save(p)

W, H = 3200, 1800
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
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
