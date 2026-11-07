"""anyplot.ai
line-basic: Basic Line Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-04-29
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
BRAND = "#009E73"  # Imprint palette, position 1

# Columns: set these to your table's column names
DAY = "Day of Month"  # role: x
TEMPERATURE = "Temperature (°C)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("temperatures.csv")
np.random.seed(42)
days = np.arange(1, 32)
base_temp = 20 + 8 * np.sin(np.linspace(0, np.pi, 31))
df = pd.DataFrame({DAY: days, TEMPERATURE: base_temp + np.random.randn(31) * 2})

# Plot: reads only df and the constants above
W, H = 3200, 1800
source = ColumnDataSource(df)
p = figure(
    width=W,
    height=H,
    title="line-basic · python · bokeh · anyplot.ai",
    x_axis_label=DAY,
    y_axis_label=TEMPERATURE,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

p.line(x=DAY, y=TEMPERATURE, source=source, line_width=4, line_color=BRAND)
p.scatter(x=DAY, y=TEMPERATURE, source=source, size=12, fill_color=BRAND, line_color=PAGE_BG, line_width=2)

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_color = INK_SOFT

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2

p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10

# Save
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
