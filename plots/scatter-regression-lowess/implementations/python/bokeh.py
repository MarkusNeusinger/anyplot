"""anyplot.ai
scatter-regression-lowess: Scatter Plot with LOWESS Regression
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-14
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from statsmodels.nonparametric.smoothers_lowess import lowess


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: position 1 for the points, position 2 for the LOWESS curve
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SMOOTHING_FRAC = 0.4  # share of the points used in each local fit

# Columns: set these to your table's column names
TEMPERATURE = "Temperature (°C)"  # role: x
ACTIVITY = "Enzyme Activity (%)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("enzyme.csv")
np.random.seed(42)
n = 200
temperature = np.sort(np.linspace(10, 50, n) + np.random.normal(0, 1, n))
# Activity rises, peaks around 35°C, then falls (typical enzyme behavior)
activity = 20 + 60 * np.exp(-0.5 * ((temperature - 35) / 8) ** 2) + np.random.normal(0, 5, n)
df = pd.DataFrame({TEMPERATURE: temperature, ACTIVITY: activity})

# Plot: reads only df and the constants above
fit = lowess(df[ACTIVITY], df[TEMPERATURE], frac=SMOOTHING_FRAC)
curve = pd.DataFrame({TEMPERATURE: fit[:, 0], ACTIVITY: fit[:, 1]})

title = "LOWESS Smoothing · scatter-regression-lowess · python · bokeh · anyplot.ai"
title_pt = round(50 * min(1.0, 67 / len(title)))

p = figure(
    width=3200,
    height=1800,
    title=title,
    x_axis_label=TEMPERATURE,
    y_axis_label=ACTIVITY,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

scatter = p.scatter(
    x=TEMPERATURE,
    y=ACTIVITY,
    source=ColumnDataSource(df),
    size=13,
    color=IMPRINT_PALETTE[0],
    alpha=0.6,
    legend_label="Observations",
)
p.line(
    x=TEMPERATURE,
    y=ACTIVITY,
    source=ColumnDataSource(curve),
    line_width=7,
    color=IMPRINT_PALETTE[1],
    legend_label=f"LOWESS fit (frac = {SMOOTHING_FRAC})",
)
p.add_tools(
    HoverTool(
        tooltips=[(TEMPERATURE, f"@{{{TEMPERATURE}}}{{0.0}}"), (ACTIVITY, f"@{{{ACTIVITY}}}{{0.0}}")],
        renderers=[scatter],
    )
)

# Style
p.title.text_font_size = f"{title_pt}pt"
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
p.outline_line_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.legend.label_text_font_size = "30pt"
p.legend.label_text_color = INK_SOFT
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.location = "top_right"

# Save HTML, then screenshot it with headless Chrome
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
