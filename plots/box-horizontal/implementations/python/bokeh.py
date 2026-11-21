""" anyplot.ai
box-horizontal: Horizontal Box Plot
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-21
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, FactorRange
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
WHISKER_IQR = 1.5  # whiskers reach the furthest value within this many IQRs of the box

# Columns: set these to your table's column names
SERVICE = "Service type"  # role: categories
RESPONSE = "Response time (ms)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("response_times.csv")
np.random.seed(42)
samples = {
    "Cache Layer": np.random.normal(15, 5, 80),
    "API Gateway": np.random.normal(45, 12, 80),
    "Authentication": np.concatenate([np.random.normal(65, 15, 75), [130, 145, 150]]),
    "Database Query": np.concatenate([np.random.normal(120, 30, 80), [220, 240]]),
    "File Storage": np.random.normal(200, 50, 80),
}
df = pd.DataFrame(
    {
        SERVICE: [name for name, values in samples.items() for _ in values],
        RESPONSE: np.concatenate(list(samples.values())),
    }
)

# Plot: reads only df and the constants above
groups = df.groupby(SERVICE, sort=False)[RESPONSE]
q1, median, q3 = groups.quantile(0.25), groups.median(), groups.quantile(0.75)
iqr = q3 - q1
fence_lo, fence_hi = q1 - WHISKER_IQR * iqr, q3 + WHISKER_IQR * iqr

lo, hi = df[SERVICE].map(fence_lo), df[SERVICE].map(fence_hi)  # per-row fences
inside = df[(df[RESPONSE] >= lo) & (df[RESPONSE] <= hi)]
outliers = df[(df[RESPONSE] < lo) | (df[RESPONSE] > hi)]

box = pd.DataFrame(
    {
        "q1": q1,
        "median": median,
        "q3": q3,
        "low": inside.groupby(SERVICE)[RESPONSE].min(),
        "high": inside.groupby(SERVICE)[RESPONSE].max(),
    }
).sort_values("median")  # slowest service at the top
box.index.name = SERVICE
box = box.reset_index()
categories = list(box[SERVICE])
source = ColumnDataSource(box)

p = figure(
    width=3200,
    height=1800,
    y_range=FactorRange(*categories),
    x_axis_label=RESPONSE,
    y_axis_label=SERVICE,
    title="box-horizontal · python · bokeh · anyplot.ai",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=60,
)
# Whiskers, then caps
p.segment(x0="low", x1="q1", y0=SERVICE, y1=SERVICE, source=source, line_color=INK_SOFT, line_width=5)
p.segment(x0="q3", x1="high", y0=SERVICE, y1=SERVICE, source=source, line_color=INK_SOFT, line_width=5)
for end in ("low", "high"):
    p.hbar(y=SERVICE, left=end, right=end, height=0.3, source=source, line_color=INK_SOFT, line_width=5)

# Box from first to third quartile
p.hbar(
    y=SERVICE,
    left="q1",
    right="q3",
    height=0.6,
    source=source,
    fill_color=IMPRINT_PALETTE[0],
    fill_alpha=0.75,
    line_color=INK_SOFT,
    line_width=4,
)

# Median line, in the ink color so it stands out on the box fill in both themes
p.hbar(y=SERVICE, left="median", right="median", height=0.6, source=source, line_color=INK, line_width=9)

# Outliers at their values
p.scatter(
    x=RESPONSE,
    y=SERVICE,
    source=ColumnDataSource(outliers),
    size=26,
    fill_color=IMPRINT_PALETTE[0],
    fill_alpha=0.75,
    line_color=INK_SOFT,
    line_width=3,
)

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

p.xgrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.15
p.ygrid.grid_line_alpha = 0.0

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# Save HTML and screenshot it with headless Chrome
os.chdir(Path(__file__).parent)
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
