"""anyplot.ai
line-filled: Filled Line Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-12
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


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: first position is the single-series color
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
MONTH = "Month"  # role: x
VISITORS = "Website visitors (count)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("traffic.csv")
np.random.seed(42)
months = np.arange(1, 13)
base_traffic = 50000
seasonal = 15000 * np.sin(2 * np.pi * (months - 3) / 12)  # peak in summer
trend = 2000 * months  # gradual growth
noise = np.random.normal(0, 3000, 12)
df = pd.DataFrame({MONTH: months, VISITORS: np.maximum(base_traffic + seasonal + trend + noise, 0)})

# Plot
df = df.sort_values(MONTH)
source = ColumnDataSource(df.assign(baseline=0.0))

p = figure(
    width=3200,
    height=1800,
    title="line-filled · python · bokeh · anyplot.ai",
    x_axis_label=MONTH,
    y_axis_label=VISITORS,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
    y_range=Range1d(0, df[VISITORS].max() * 1.1),
)

# Semi-transparent fill down to the zero baseline, line and points on top
p.varea(x=MONTH, y1="baseline", y2=VISITORS, source=source, fill_color=IMPRINT_PALETTE[0], fill_alpha=0.35)
p.line(x=MONTH, y=VISITORS, source=source, line_color=IMPRINT_PALETTE[0], line_width=5)
p.scatter(x=MONTH, y=VISITORS, source=source, size=14, color=IMPRINT_PALETTE[0], fill_alpha=0.9)

p.add_tools(HoverTool(tooltips=[(MONTH, f"@{{{MONTH}}}"), (VISITORS, f"@{{{VISITORS}}}{{0,0}}")]))

# Text sizes
p.title.text_font_size = "50pt"
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"

# Theme-adaptive chrome
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
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# One tick per month
p.xaxis.ticker = df[MONTH].dropna().tolist()

# Save as interactive HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome
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
time.sleep(3)  # let bokeh's JS render the canvas
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
