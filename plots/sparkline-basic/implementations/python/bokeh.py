"""anyplot.ai
sparkline-basic: Basic Sparkline
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 90/100 | Updated: 2026-05-02
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: position 1 is the line, position 2 marks the minimum
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DAY = "Day"  # role: extra
SESSIONS = "Sessions"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("sessions.csv")
# Daily web-traffic sessions over 60 days, with a launch bump, a mid-period
# decline and weekend dips.
np.random.seed(42)
n_points = 60
day = np.arange(n_points)
trend = 100 + 0.6 * day
launch_bump = 25 * np.exp(-((day - 12) ** 2) / 30.0)
mid_decline = -22 * np.exp(-((day - 35) ** 2) / 60.0)
weekend = np.where(day % 7 >= 5, -10.0, 0.0)
noise = np.random.randn(n_points) * 4
df = pd.DataFrame({DAY: day, SESSIONS: trend + launch_bump + mid_decline + weekend + noise})

# Plot: reads only df and the constants above
min_idx = df[SESSIONS].idxmin()
max_idx = df[SESSIONS].idxmax()
endpoints = df.iloc[[0, -1]]
extremes = df.loc[[min_idx, max_idx]].assign(color=[IMPRINT_PALETTE[1], IMPRINT_PALETTE[0]])

W, H = 3200, 1800
p = figure(
    width=W,
    height=H,
    title="sparkline-basic · python · bokeh · anyplot.ai",
    toolbar_location=None,
    min_border_left=200,
    min_border_right=200,
    min_border_top=400,
    min_border_bottom=420,
)
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_color = None
p.x_range.range_padding = 0.01
p.y_range.range_padding = 0.08

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.title.text_color = INK
p.title.text_font_size = "50pt"
p.title.align = "center"

p.line(x=DAY, y=SESSIONS, source=ColumnDataSource(df), line_width=5, color=IMPRINT_PALETTE[0])
p.scatter(x=DAY, y=SESSIONS, source=ColumnDataSource(endpoints), size=26, color=INK_SOFT)
p.scatter(
    x=DAY, y=SESSIONS, source=ColumnDataSource(extremes), size=40, color="color", line_color=PAGE_BG, line_width=4
)

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
