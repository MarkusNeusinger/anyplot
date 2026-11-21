""" anyplot.ai
line-styled: Styled Line Plot
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-21
"""

import calendar
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
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

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants: the four standard line styles, one per series in order (solid, dashed, dotted, dash-dot)
LINE_STYLES = ["solid", [20, 10], [4, 8], [20, 8, 4, 8]]

# Columns
MONTH = "Month"  # role: x
SERIES = ["CPU Usage", "Memory Usage", "Disk I/O", "Network Traffic"]  # role: y_

# Data: replace this block with your own table, for example df = pd.read_csv("metrics.csv")
np.random.seed(42)
months = np.arange(1, 13)
base = np.array([65, 68, 72, 75, 78, 82, 85, 84, 80, 77, 74, 70])
df = pd.DataFrame(
    {
        MONTH: months,
        SERIES[0]: base + np.random.randn(12) * 3,
        SERIES[1]: base * 0.85 + np.random.randn(12) * 4 + 10,
        SERIES[2]: base * 0.7 + np.random.randn(12) * 5 + 20,
        SERIES[3]: base * 1.1 + np.random.randn(12) * 2 - 5,
    }
)

# Plot
W, H = 3200, 1800
source = ColumnDataSource(df)
title = "line-styled · python · bokeh · anyplot.ai"

p = figure(
    width=W,
    height=H,
    title=title,
    x_axis_label=MONTH,
    y_axis_label="Utilization (%)",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

legend_items = []
for i, name in enumerate(SERIES):
    line = p.line(
        x=MONTH,
        y=name,
        source=source,
        line_width=6,
        color=IMPRINT_PALETTE[i],
        line_dash=LINE_STYLES[i % len(LINE_STYLES)],
    )
    dots = p.scatter(x=MONTH, y=name, source=source, size=18, color=IMPRINT_PALETTE[i], alpha=0.9)
    legend_items.append((name, [line, dots]))

legend = Legend(items=legend_items, location="top_left")
legend.label_text_font_size = "30pt"
legend.label_text_color = INK_SOFT
legend.glyph_height = 40
legend.glyph_width = 140
legend.spacing = 12
legend.padding = 20
legend.background_fill_alpha = 0.95
legend.background_fill_color = ELEVATED_BG
legend.border_line_color = INK_SOFT
legend.border_line_width = 2
p.add_layout(legend, "center")

# Chrome
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.title.align = "center"
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

p.grid.grid_line_color = INK
p.grid.grid_line_alpha = 0.10

ticks = [int(m) for m in df[MONTH].dropna()]
p.xaxis.ticker = ticks
p.xaxis.major_label_overrides = {t: calendar.month_abbr[(t - 1) % 12 + 1] for t in ticks}

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.major_tick_line_width = 2
p.yaxis.major_tick_line_width = 2

# Save HTML, then screenshot with headless Chrome
output_file(f"plot-{THEME}.html")
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
