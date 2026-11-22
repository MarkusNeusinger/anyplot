""" anyplot.ai
density-rug: Density Plot with Rug Marks
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-22
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure, output_file, save
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: position 1 is the single series here
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
VALUE = "Response Time (ms)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("latency.csv")
np.random.seed(42)
normal_times = np.random.normal(loc=120, scale=25, size=180)
slow_times = np.random.normal(loc=220, scale=30, size=40)
response_times = np.concatenate([normal_times, slow_times])
df = pd.DataFrame({VALUE: response_times[response_times > 0]})

# Plot: reads only df and the constants above
values = df[VALUE].dropna().to_numpy()

# Gaussian KDE with Silverman's bandwidth rule
n = len(values)
std = np.std(values)
iqr = np.percentile(values, 75) - np.percentile(values, 25)
bandwidth = 0.9 * min(std, iqr / 1.34) * n ** (-0.2)

x_range = np.linspace(values.min() - 20, values.max() + 20, 500)
density = np.zeros_like(x_range)
for xi in values:
    density += np.exp(-0.5 * ((x_range - xi) / bandwidth) ** 2)
density = density / (n * bandwidth * np.sqrt(2 * np.pi))

p = figure(
    width=3200,
    height=1800,
    title="density-rug · python · bokeh · anyplot.ai",
    x_axis_label=VALUE,
    y_axis_label="Density",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# KDE as filled area, semi-transparent so the rug and grid stay visible
kde_x = np.concatenate([[x_range[0]], x_range, [x_range[-1]]])
kde_y = np.concatenate([[0], density, [0]])
p.patch(x=kde_x, y=kde_y, fill_color=IMPRINT_PALETTE[0], fill_alpha=0.35, line_color=IMPRINT_PALETTE[0], line_width=3)

kde_source = ColumnDataSource(data={"x": x_range, "y": density})
p.line(x="x", y="y", source=kde_source, line_color=IMPRINT_PALETTE[0], line_width=5)

# Rug marks: one short tick per observation, hanging below the baseline
rug_height = density.max() * 0.03
rug_source = ColumnDataSource(data={"x": values, "y0": np.zeros(n), "y1": np.full(n, -rug_height)})
p.segment(
    x0="x", y0="y0", x1="x", y1="y1", source=rug_source, line_color=IMPRINT_PALETTE[0], line_width=3, line_alpha=0.5
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

p.xgrid.grid_line_alpha = 0.15
p.ygrid.grid_line_alpha = 0.15
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# Extend the y-axis slightly below 0 to show the rug marks
p.y_range.start = -rug_height * 1.5
p.y_range.end = density.max() * 1.1

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
time.sleep(3)  # let bokeh's JS render the canvas
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
