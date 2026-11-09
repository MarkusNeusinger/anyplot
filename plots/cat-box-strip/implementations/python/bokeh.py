""" anyplot.ai
cat-box-strip: Box Plot with Strip Overlay
Library: bokeh 3.10.1 | Python 3.14.10
Quality: 87/100 | Updated: 2026-11-09
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Whisker
from bokeh.plotting import figure
from bokeh.transform import dodge, jitter
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: single series, first position
BRAND = "#009E73"

# Columns: set these to your table's column names
SOIL = "Soil Type"  # role: category
GROWTH = "Plant Growth (cm)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("growth.csv")
np.random.seed(42)
rows = []
for soil, n in zip(["Sandy", "Clay", "Loamy", "Silty"], [35, 40, 45, 38], strict=True):
    if soil == "Sandy":
        values = np.random.normal(25, 6, n)  # lower growth, moderate variance
    elif soil == "Clay":
        values = np.append(np.random.normal(32, 8, n), [55, 58])  # medium growth, high outliers
    elif soil == "Loamy":
        values = np.random.normal(42, 5, n)  # high growth, low variance
    else:
        values = np.append(np.random.normal(35, 7, n), [12, 14])  # medium-high growth, low outliers
    rows.extend({SOIL: soil, GROWTH: v} for v in values)
df = pd.DataFrame(rows)

# Plot: reads only df and the constants above
df = df.dropna(subset=[SOIL]).astype({SOIL: str, GROWTH: float})
categories = list(df[SOIL].unique())

# Box statistics per category: quartiles, and whiskers at the furthest points within 1.5 IQR
grouped = df.groupby(SOIL, sort=False)[GROWTH]
stats = pd.DataFrame({"q1": grouped.quantile(0.25), "q2": grouped.median(), "q3": grouped.quantile(0.75)})
iqr = stats["q3"] - stats["q1"]
stats["lower"] = [
    df.loc[(df[SOIL] == c) & (df[GROWTH] >= stats.at[c, "q1"] - 1.5 * iqr[c]), GROWTH].min() for c in stats.index
]
stats["upper"] = [
    df.loc[(df[SOIL] == c) & (df[GROWTH] <= stats.at[c, "q3"] + 1.5 * iqr[c]), GROWTH].max() for c in stats.index
]
stats = stats.rename_axis("category").reset_index()
box_source = ColumnDataSource(stats)

title = "cat-box-strip · python · bokeh · anyplot.ai"
p = figure(
    width=3200,
    height=1800,
    x_range=categories,
    title=title,
    x_axis_label=SOIL,
    y_axis_label=GROWTH,
    tools="",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Whiskers from the box edges out to the whisker ends
for low, high in (("lower", "q1"), ("q3", "upper")):
    whisker = Whisker(source=box_source, base="category", lower=low, upper=high, line_color=INK_SOFT, line_width=3)
    whisker.lower_head.size = 40 if low == "lower" else 0
    whisker.upper_head.size = 40 if high == "upper" else 0
    for head in (whisker.lower_head, whisker.upper_head):
        head.line_color = INK_SOFT
        head.line_width = 3
    p.add_layout(whisker)

# Box from Q1 to Q3
box_width = 0.5
p.vbar(
    x="category",
    top="q3",
    bottom="q1",
    width=box_width,
    source=box_source,
    fill_color=BRAND,
    fill_alpha=0.18,
    line_color=INK_SOFT,
    line_width=3,
)

# Median line across the full box width
p.segment(
    x0=dodge("category", -box_width / 2, range=p.x_range),
    x1=dodge("category", box_width / 2, range=p.x_range),
    y0="q2",
    y1="q2",
    source=box_source,
    line_color=INK,
    line_width=6,
)

# Strip overlay: translucent points jittered within each category's band
p.scatter(
    x=jitter(SOIL, width=0.3, range=p.x_range),
    y=GROWTH,
    source=ColumnDataSource(df),
    size=20,
    fill_color=BRAND,
    fill_alpha=0.55,
    line_color=BRAND,
    line_alpha=0.9,
    line_width=1.5,
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
p.xaxis.axis_label_standoff = 30
p.yaxis.axis_label_standoff = 30
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.yaxis.minor_tick_line_color = None
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.15

# Save HTML, then screenshot it with headless Chrome
output_file(f"plot-{THEME}.html", title=title)
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
