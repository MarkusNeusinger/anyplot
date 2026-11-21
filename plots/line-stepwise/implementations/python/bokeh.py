"""anyplot.ai
line-stepwise: Step Line Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-11-21
"""

import os
import time
from pathlib import Path

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

# Imprint palette: a single series uses the first position
BRAND = "#009E73"

# Columns: set these to your table's column names
HOUR = "Hour of day"  # role: x
CPU = "CPU usage (%)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("cpu.csv")
df = pd.DataFrame(
    {
        HOUR: list(range(24)),
        CPU: [35, 42, 55, 72, 85, 92, 88, 70, 55, 40, 32, 28, 35, 52, 78, 88, 95, 90, 75, 60, 48, 42, 32, 25],
    }
)

# Plot: reads only df and the constants above
source = ColumnDataSource(df)

p = figure(
    width=3200,
    height=1800,
    title="line-stepwise · python · bokeh · anyplot.ai",
    x_axis_label=HOUR,
    y_axis_label=CPU,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# 'after' alignment: each value is held flat until the next x, then jumps
p.step(x=HOUR, y=CPU, source=source, mode="after", line_width=5, line_color=BRAND)

# Markers sit on the data points, small enough that the flat segments still read as lines
points = p.scatter(x=HOUR, y=CPU, source=source, size=14, color=BRAND, line_color=PAGE_BG, line_width=2)

# Hover on the data points (HTML artifact only)
p.add_tools(HoverTool(renderers=[points], tooltips=[(HOUR, f"@{{{HOUR}}}"), (CPU, f"@{{{CPU}}}{{0.0}}")]))

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

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

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

p.y_range = Range1d(0, df[CPU].max() * 1.1)

# Save HTML
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
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
