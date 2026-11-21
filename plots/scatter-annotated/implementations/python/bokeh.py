""" anyplot.ai
scatter-annotated: Annotated Scatter Plot with Text Labels
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-21
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, LabelSet, Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: position 1 is the single series
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
REVENUE = "Revenue (billion USD)"  # role: x
MARKET_CAP = "Market cap (billion USD)"  # role: y
COMPANY = "Company"  # role: label

# Data: replace this block with your own table, for example df = pd.read_csv("companies.csv")
df = pd.DataFrame(
    {
        COMPANY: [
            "TechCorp",
            "DataSys",
            "CloudNet",
            "AIVenture",
            "NetFlow",
            "CodeBase",
            "ByteWorks",
            "DigiCore",
            "InfoTech",
            "WebScale",
            "AppLogic",
            "SoftPeak",
            "CyberLink",
            "DevOps",
            "QuantumBit",
        ],
        REVENUE: [12.5, 8.3, 22.1, 5.7, 15.8, 9.2, 18.4, 6.9, 11.3, 25.6, 7.4, 14.2, 19.8, 4.5, 10.1],
        MARKET_CAP: [45.2, 28.1, 85.3, 32.5, 52.8, 35.6, 68.9, 25.4, 41.7, 98.2, 22.3, 55.4, 72.1, 18.9, 38.5],
    }
)

# Plot: reads only df and the constants above
W, H = 3200, 1800
x_max = df[REVENUE].max() * 1.12
y_max = df[MARKET_CAP].max() * 1.08

p = figure(
    width=W,
    height=H,
    title="scatter-annotated · python · bokeh · anyplot.ai",
    x_axis_label=REVENUE,
    y_axis_label=MARKET_CAP,
    x_range=Range1d(0, x_max),
    y_range=Range1d(0, y_max),
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Label placement: the data sits on a rising diagonal, so labels alternate
# between the lower-right and upper-left side of their point, ordered by x.
# Points never move; only the labels do, joined to their point by a leader line.
order = np.argsort(np.argsort(df[REVENUE].to_numpy()))
right_side = order % 2 == 0
dx = np.where(right_side, 1, -1) * x_max * 0.012
dy = np.where(right_side, -1, 1) * y_max * 0.035
labels = df.assign(lx=df[REVENUE] + dx, ly=df[MARKET_CAP] + dy)

# Leader lines first, so markers and text sit on top of them
p.segment(
    x0=REVENUE,
    y0=MARKET_CAP,
    x1="lx",
    y1="ly",
    source=ColumnDataSource(labels),
    line_color=INK_SOFT,
    line_width=2,
    line_alpha=0.45,
)

# Translucent markers at their exact data values
p.scatter(
    x=REVENUE,
    y=MARKET_CAP,
    source=ColumnDataSource(df),
    size=34,
    color=IMPRINT_PALETTE[0],
    alpha=0.7,
    line_color=PAGE_BG,
    line_width=3,
)

# Text labels: one LabelSet per side so the text grows away from its point
for align, rows in ((("left", "top"), labels[right_side]), (("right", "bottom"), labels[~right_side])):
    p.add_layout(
        LabelSet(
            x="lx",
            y="ly",
            text=COMPANY,
            source=ColumnDataSource(rows),
            text_font_size="28pt",
            text_color=INK,
            text_align=align[0],
            text_baseline=align[1],
        )
    )

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None  # L-shaped frame: only the left and bottom axis lines remain
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Save HTML, then screenshot it with headless Chrome
output_file(f"plot-{THEME}.html")
save(p)

opts = Options()
opts.binary_location = "/usr/bin/chromium"
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
