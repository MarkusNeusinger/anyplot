"""anyplot.ai
scatter-basic: Basic Scatter Plot
Library: bokeh 3.9.0 | Python 3.14.4
Quality: pending | Updated: 2026-04-23
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1

W, H = 3200, 1800

X = "Study Hours per Day"  # role: x
Y = "Exam Score (%)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
rng = np.random.default_rng(42)
hours = rng.uniform(0.8, 9.6, 180)
scores = np.clip(hours * 7.2 + rng.normal(0, 6.5, 180) + 26, 18, 99)
df = pd.DataFrame({X: hours, Y: scores})

# Plot
x_pad = (df[X].max() - df[X].min()) * 0.06
y_pad = (df[Y].max() - df[Y].min()) * 0.06
p = figure(
    width=W,
    height=H,
    title="scatter-basic · bokeh · anyplot.ai",
    x_axis_label=X,
    y_axis_label=Y,
    toolbar_location=None,
    x_range=Range1d(df[X].min() - x_pad, df[X].max() + x_pad),
    y_range=Range1d(df[Y].min() - y_pad, df[Y].max() + y_pad),
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

source = ColumnDataSource(df)
points = p.scatter(x=X, y=Y, source=source, size=24, color=BRAND, alpha=0.7, line_color=PAGE_BG, line_width=1)

# HoverTool: Bokeh's distinctive interactive feature (HTML only; PNG stays clean)
p.add_tools(HoverTool(renderers=[points], tooltips=[(X, f"@{{{X}}}{{0.1}}"), (Y, f"@{{{Y}}}{{0.0}}")]))

# Typography
p.title.text_font_size = "50pt"
p.title.text_font_style = "bold"
p.title.text_color = INK
p.title.align = "center"
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_font_style = "normal"
p.yaxis.axis_label_text_font_style = "normal"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10
p.xgrid.grid_line_width = 1
p.ygrid.grid_line_width = 1

# Save
output_file(f"plot-{THEME}.html", title="scatter-basic · bokeh · anyplot.ai")
save(p)

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
