""" anyplot.ai
histogram-basic: Basic Histogram
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-26
"""

import os
import sys
import time
from pathlib import Path


# Prevent this file's directory from shadowing the installed bokeh package
sys.path = [p for p in sys.path if os.path.abspath(p) != os.path.dirname(os.path.abspath(__file__))]

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, NumeralTickFormatter, Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
FINISH_TIME = "Finish time (min)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("times.csv")
# Marathon finish times: a main recreational group, a slower group and a few stragglers
rng = np.random.default_rng(42)
times = np.concatenate(
    [
        rng.normal(loc=240, scale=30, size=380),
        rng.normal(loc=305, scale=18, size=100),
        rng.normal(loc=370, scale=12, size=20),
    ]
)
df = pd.DataFrame({FINISH_TIME: times[(times > 120) & (times < 420)]})

# Plot: reads only df and the constants above
counts, edges = np.histogram(df[FINISH_TIME].dropna(), bins=28)
source = ColumnDataSource(
    data={
        "left": edges[:-1],
        "right": edges[1:],
        "top": counts,
        "bottom": np.zeros(len(counts)),
        "bin_start": [f"{e:.0f}" for e in edges[:-1]],
        "bin_end": [f"{e:.0f}" for e in edges[1:]],
    }
)

W, H = 3200, 1800
TITLE = "histogram-basic · python · bokeh · anyplot.ai"
title_pt = max(34, round(50 * (67 / len(TITLE) if len(TITLE) > 67 else 1.0)))
pad = (edges[-1] - edges[0]) * 0.03
p = figure(
    width=W,
    height=H,
    title=TITLE,
    x_axis_label=FINISH_TIME,
    y_axis_label="Number of runners",
    toolbar_location=None,
    x_range=Range1d(edges[0] - pad, edges[-1] + pad),
    y_range=Range1d(0, counts.max() * 1.08),
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=60,
)

bars = p.quad(
    left="left",
    right="right",
    top="top",
    bottom="bottom",
    source=source,
    fill_color=IMPRINT_PALETTE[0],
    line_color=PAGE_BG,
    line_width=2,
    hover_fill_color=IMPRINT_PALETTE[0],
    hover_fill_alpha=0.75,
)
p.add_tools(
    HoverTool(renderers=[bars], tooltips=[("Range", "@bin_start–@bin_end min"), ("Runners", "@top")], mode="mouse")
)

# Style
p.title.text_font_size = f"{title_pt}pt"
p.title.text_color = INK
p.title.text_font_style = "bold"
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.yaxis.formatter = NumeralTickFormatter(format="0,0")

p.xgrid.visible = False
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.15
p.ygrid.grid_line_width = 1

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
for axis in (p.xaxis, p.yaxis):
    axis.axis_line_width = 2
    axis.axis_line_color = INK_SOFT
    axis.major_tick_line_color = INK_SOFT
    axis.minor_tick_line_color = None

# Save HTML (interactive artifact)
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome at the exact canvas size
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
# Pin the viewport exactly: headless --window-size still reserves a phantom title bar
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
# Paint the page in the theme color so the anti-aliased canvas edge shows no white line
driver.execute_script(
    "document.documentElement.style.background = arguments[0]; document.body.style.background = arguments[0];", PAGE_BG
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
