"""anyplot.ai
histogram-stacked: Stacked Histogram
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-12
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

# Imprint palette: one position per group, in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
BIN_COUNT = 15  # the same bin edges are shared by every group

# Columns: set these to your table's column names
SCORE = "Test score (points)"  # role: values
GROUP = "Study group"  # role: group

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
rng = np.random.default_rng(42)
group_sizes = {"Group A": (75, 8, 150), "Group B": (82, 10, 120), "Group C": (65, 12, 100)}
df = pd.concat(
    [
        pd.DataFrame({SCORE: np.clip(rng.normal(mean, sd, n), 0, 100), GROUP: name})
        for name, (mean, sd, n) in group_sizes.items()
    ],
    ignore_index=True,
)

# Plot
groups = list(df[GROUP].unique())
edges = np.histogram_bin_edges(df[SCORE].dropna(), bins=BIN_COUNT)
counts = pd.DataFrame({g: np.histogram(df.loc[df[GROUP] == g, SCORE].dropna(), bins=edges)[0] for g in groups})
# Largest group at the bottom, the same order in every bin
order = list(counts.sum().sort_values(ascending=False, kind="stable").index)
stacked = counts[order].cumsum(axis=1)

title = "histogram-stacked · python · bokeh · anyplot.ai"
title_pt = round(50 * (67 / len(title) if len(title) > 67 else 1.0))

p = figure(
    width=3200,
    height=1800,
    title=title,
    x_axis_label=SCORE,
    y_axis_label="Frequency (count)",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

previous = None
for g in order:
    top = stacked[g].to_numpy()
    bottom = np.zeros_like(top) if previous is None else stacked[previous].to_numpy()
    source = ColumnDataSource({"left": edges[:-1], "right": edges[1:], "top": top, "bottom": bottom})
    p.quad(
        left="left",
        right="right",
        top="top",
        bottom="bottom",
        source=source,
        fill_color=IMPRINT_PALETTE[groups.index(g)],
        line_color=PAGE_BG,
        line_width=2,
        legend_label=str(g),
    )
    previous = g

p.y_range.start = 0
p.y_range.end = float(stacked.iloc[:, -1].max()) * 1.15

# Text sizing for the 3200x1800 canvas
p.title.text_font_size = f"{title_pt}pt"
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"

# Theme-adaptive chrome
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

# Legend
p.legend.title = GROUP
p.legend.title_text_color = INK
p.legend.title_text_font_size = "34pt"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT
p.legend.label_text_font_size = "34pt"
p.legend.location = "top_left"

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with Selenium
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
