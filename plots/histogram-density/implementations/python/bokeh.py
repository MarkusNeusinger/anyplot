"""anyplot.ai
histogram-density: Density Histogram
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-11
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
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: histogram bars take position 1, the fitted PDF position 2
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_BINS = 30  # bins across the data range, padded by 5 units on each side

# Columns: set these to your table's column names
SCORE = "Test score"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
np.random.seed(42)
df = pd.DataFrame({SCORE: np.random.normal(loc=75, scale=12, size=500)})

# Plot: reads only df and the constants above
values = df[SCORE].dropna()
mu, sigma = values.mean(), values.std()

# Density-normalised histogram: bar areas sum to 1
bin_edges = np.linspace(values.min() - 5, values.max() + 5, N_BINS + 1)
density, edges = np.histogram(values, bins=bin_edges, density=True)
bars = ColumnDataSource(data={"left": edges[:-1], "right": edges[1:], "top": density, "bottom": np.zeros(len(density))})

# Normal PDF fitted to the sample, on the same density scale
x_pdf = np.linspace(values.min() - 10, values.max() + 10, 200)
pdf_values = np.exp(-0.5 * ((x_pdf - mu) / sigma) ** 2) / (sigma * np.sqrt(2 * np.pi))
curve = ColumnDataSource(data={"x": x_pdf, "y": pdf_values})

p = figure(
    width=3200,
    height=1800,
    title="histogram-density · python · bokeh · anyplot.ai",
    x_axis_label=SCORE,
    y_axis_label="Density (probability per unit)",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

p.quad(
    left="left",
    right="right",
    top="top",
    bottom="bottom",
    source=bars,
    fill_color=IMPRINT_PALETTE[0],
    fill_alpha=0.7,
    line_color=PAGE_BG,
    line_width=2,
    legend_label="Empirical distribution",
)
p.line(
    x="x",
    y="y",
    source=curve,
    line_color=IMPRINT_PALETTE[1],
    line_width=6,
    legend_label=f"Normal PDF (μ={mu:.1f}, σ={sigma:.1f})",
)

# Style
p.title.text_font_size = "50pt"
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT
p.title.text_color = INK
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

p.legend.label_text_font_size = "34pt"
p.legend.label_text_color = INK_SOFT
p.legend.location = "top_left"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT

p.y_range.start = 0

# Save interactive HTML
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
