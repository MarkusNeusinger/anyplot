"""anyplot.ai
histogram-stepwise: Step Histogram
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 96/100 | Updated: 2026-05-12
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_BINS = 34  # shared bin count for every distribution

# Columns: set these to your table's column names
SENSORS = ["Sensor A", "Sensor B"]  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("readings.csv")
rng = np.random.default_rng(42)
df = pd.DataFrame({SENSORS[0]: rng.normal(50, 12, 500), SENSORS[1]: rng.normal(65, 8, 500)})

# Plot: reads only df and the constants above
TEMPERATURE = "Temperature (°C)"
edges = np.histogram_bin_edges(df[SENSORS].to_numpy().ravel()[~np.isnan(df[SENSORS].to_numpy().ravel())], bins=N_BINS)

p = figure(
    width=3200,
    height=1800,
    title="histogram-stepwise · python · bokeh · anyplot.ai",
    x_axis_label=TEMPERATURE,
    y_axis_label="Frequency",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

top = 0
for i, sensor in enumerate(SENSORS):
    counts, _ = np.histogram(df[sensor].dropna(), bins=edges)
    top = max(top, counts.max())
    # Step outline: horizontal segment per bin, vertical segments at the shared edges
    p.line(
        np.repeat(edges, 2)[1:-1],
        np.repeat(counts, 2),
        line_width=5,
        color=IMPRINT_PALETTE[i],
        legend_label=str(sensor),
    )

p.y_range = Range1d(0, top * 1.1)

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

p.axis.axis_line_color = INK_SOFT
p.axis.major_tick_line_color = INK_SOFT
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.legend.label_text_font_size = "34pt"
p.legend.label_text_color = INK_SOFT
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.location = "top_right"
p.legend.padding = 20
p.legend.spacing = 15
p.legend.margin = 25

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
