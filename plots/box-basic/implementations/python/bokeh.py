"""anyplot.ai
box-basic: Basic Box Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-28
"""

import os
import sys
import time
from pathlib import Path


# Remove this script's own directory from sys.path so the installed
# bokeh package is found instead of this file (also named bokeh.py).
_own_dir = os.path.dirname(os.path.realpath(__file__))
sys.path = [p for p in sys.path if os.path.realpath(p or ".") != _own_dir]

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Range1d, Whisker
from bokeh.plotting import figure
from bokeh.transform import factor_cmap
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
CLASS = "Class"  # role: category
SCORE = "Test score (points)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
np.random.seed(42)
scores = {
    "Class A": np.random.normal(75, 10, 100),
    "Class B": np.concatenate([np.random.normal(85, 5, 90), np.array([65, 68, 70])]),
    "Class C": np.clip(np.random.normal(68, 14, 100), 30, None),
    "Class D": np.concatenate([np.random.normal(78, 8, 95), np.array([100, 102, 50, 52])]),
}
df = pd.DataFrame(
    {CLASS: np.repeat(list(scores), [len(v) for v in scores.values()]), SCORE: np.concatenate(list(scores.values()))}
)

# Plot: reads only df and the constants above
categories = list(df[CLASS].unique())

# Box plot statistics: quartiles, whiskers at the most extreme values within 1.5 x IQR
box_rows = []
outlier_x = []
outlier_y = []
for cat in categories:
    values = df.loc[df[CLASS] == cat, SCORE].dropna().to_numpy()
    q1, q2, q3 = np.percentile(values, [25, 50, 75])
    iqr = q3 - q1
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr
    box_rows.append(
        {
            "cat": cat,
            "q1": q1,
            "q2": q2,
            "q3": q3,
            "upper": values[values <= upper_fence].max(),
            "lower": values[values >= lower_fence].min(),
        }
    )
    outliers = values[(values < lower_fence) | (values > upper_fence)]
    outlier_x.extend([cat] * len(outliers))
    outlier_y.extend(outliers)

source = ColumnDataSource(pd.DataFrame(box_rows))

# Figure
title = "box-basic · python · bokeh · anyplot.ai"
W, H = 3200, 1800
p = figure(
    x_range=categories,
    width=W,
    height=H,
    title=title,
    x_axis_label=CLASS,
    y_axis_label=SCORE,
    toolbar_location=None,
    tools="",
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Boxes (q1–q3)
cmap = factor_cmap("cat", palette=IMPRINT_PALETTE, factors=categories)
box_width = 0.7

p.vbar(
    x="cat",
    top="q3",
    bottom="q2",
    source=source,
    width=box_width,
    fill_color=cmap,
    line_color=INK_SOFT,
    line_width=2,
    fill_alpha=0.85,
)
p.vbar(
    x="cat",
    top="q2",
    bottom="q1",
    source=source,
    width=box_width,
    fill_color=cmap,
    line_color=INK_SOFT,
    line_width=2,
    fill_alpha=0.85,
)

# Median line
p.rect(x="cat", y="q2", width=box_width, height=0.3, source=source, fill_color=INK, line_color=INK)

# Whiskers
whisker = Whisker(
    base="cat", upper="upper", lower="lower", source=source, level="underlay", line_width=3, line_color=INK_SOFT
)
whisker.upper_head.size = 40
whisker.lower_head.size = 40
whisker.upper_head.line_width = 3
whisker.lower_head.line_width = 3
p.add_layout(whisker)

# Outliers
if outlier_x:
    outlier_source = ColumnDataSource(data={"x": outlier_x, "y": outlier_y})
    p.scatter(
        x="x",
        y="y",
        source=outlier_source,
        size=24,
        fill_color=PAGE_BG,
        line_color=INK_SOFT,
        line_width=2.5,
        marker="circle",
        alpha=0.9,
    )

# Styling
p.title.text_font_size = "50pt"
p.title.text_font_style = "normal"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.x_range.range_padding = 0.12
span = df[SCORE].max() - df[SCORE].min()
p.y_range = Range1d(df[SCORE].min() - 0.05 * span, df[SCORE].max() + 0.05 * span)

# Grid
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.15
p.ygrid.grid_line_width = 1

# Background
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome; the viewport is pinned to W x H through CDP
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
driver.execute_script(
    "document.documentElement.style.background = arguments[0]; document.body.style.background = arguments[0];", PAGE_BG
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
