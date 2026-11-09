""" anyplot.ai
scatter-categorical: Categorical Scatter Plot
Library: bokeh 3.10.1 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-09
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

# Imprint palette: one position per category, in the order the categories appear
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SPEND = "Marketing Spend ($K)"  # role: x
ENGAGEMENT = "Customer Engagement Score (0–100)"  # role: y
PRODUCT = "Product"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("campaigns.csv")
np.random.seed(42)
n_per_group = 50
clusters = {  # per product: mean and spread of spend, then of engagement
    "Sparkling Water": (25, 5, 30, 6),
    "Cold Brew Coffee": (50, 7, 70, 8),
    "Energy Drink": (75, 6, 50, 7),
}
frames = []
for product, (x_mean, x_sd, y_mean, y_sd) in clusters.items():
    spend = np.random.normal(x_mean, x_sd, n_per_group)
    engagement = np.random.normal(y_mean, y_sd, n_per_group)
    frames.append(pd.DataFrame({SPEND: spend, ENGAGEMENT: engagement, PRODUCT: product}))
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
W, H = 3200, 1800
title = "scatter-categorical · python · bokeh · anyplot.ai"
p = figure(
    width=W,
    height=H,
    title=title,
    x_axis_label=SPEND,
    y_axis_label=ENGAGEMENT,
    toolbar_location=None,
    tooltips=[(PRODUCT, f"@{{{PRODUCT}}}"), (SPEND, f"@{{{SPEND}}}{{0.1}}"), (ENGAGEMENT, f"@{{{ENGAGEMENT}}}{{0.1}}")],
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=60,
)

# One renderer per category, colored by its palette position, translucent with a page-colored outline
for i, (product, rows) in enumerate(df.groupby(PRODUCT, sort=False)):
    p.scatter(
        x=SPEND,
        y=ENGAGEMENT,
        source=ColumnDataSource(rows),
        size=24,
        fill_color=IMPRINT_PALETTE[i],
        fill_alpha=0.8,
        line_color=PAGE_BG,
        line_width=2,
        legend_label=str(product),
    )

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = PAGE_BG  # covers the page-white seam at the frame's edge
p.outline_line_width = 2

p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.axis.axis_label_text_color = INK
p.axis.axis_label_text_font_style = "normal"
p.axis.major_label_text_color = INK_SOFT
p.axis.axis_line_color = INK_SOFT
p.axis.axis_line_width = 2
p.axis.major_tick_line_color = INK_SOFT
p.axis.major_tick_line_width = 2
p.axis.minor_tick_line_color = None
p.axis.axis_label_standoff = 24

p.grid.grid_line_color = INK
p.grid.grid_line_alpha = 0.15
p.grid.grid_line_width = 1.5

p.legend.title = PRODUCT
p.legend.location = "top_right"
p.legend.title_text_font_size = "34pt"
p.legend.title_text_color = INK
p.legend.title_text_font_style = "bold"
p.legend.label_text_font_size = "34pt"
p.legend.label_text_color = INK_SOFT
p.legend.glyph_width = 60  # bokeh draws a legend marker at 0.4 of the glyph box: 24 px, the marks' size
p.legend.glyph_height = 60
p.legend.spacing = 14
p.legend.padding = 28
p.legend.margin = 30
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 1
p.legend.border_line_color = INK_SOFT
p.legend.border_line_alpha = 0.4

# Save: the interactive HTML, then a headless-Chrome screenshot of it at the exact canvas size
output_file(f"plot-{THEME}.html", title=title)
save(p)

opts = Options()
for arg in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", f"--window-size={W},{H}"):
    opts.add_argument(arg)
opts.add_argument("--hide-scrollbars")
driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.execute_script("document.body.style.background = arguments[0]", PAGE_BG)  # no white hairline at the edges
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
