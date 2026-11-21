"""anyplot.ai
area-stacked-percent: 100% Stacked Area Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-12
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
YEAR = "Year"  # role: time
PRODUCT = "Product"  # role: category
SALES = "Sales (units)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("sales.csv")
np.random.seed(42)
_years = np.arange(2015, 2025)
_start = {"Product A": 35, "Product B": 28, "Product C": 22, "Product D": 15}
_step = {"Product A": 2.5, "Product B": 2.0, "Product C": 1.8, "Product D": 1.5}
_rows = []
for _name in _start:
    _values = np.maximum(_start[_name] + np.cumsum(np.random.randn(len(_years)) * _step[_name]), 3)
    _rows.append(pd.DataFrame({YEAR: _years, PRODUCT: _name, SALES: _values}))
df = pd.concat(_rows, ignore_index=True)

# Plot: reads only df and the constants above
table = df.pivot_table(index=YEAR, columns=PRODUCT, values=SALES, sort=False)
share = table.div(table.sum(axis=1), axis=0) * 100
upper = share.cumsum(axis=1)
lower = upper - share
years = [int(y) for y in table.index]

p = figure(
    width=3200,
    height=1800,
    title="area-stacked-percent · python · bokeh · anyplot.ai",
    x_axis_label=YEAR,
    y_axis_label="Share of total sales (%)",
    x_range=Range1d(min(years), max(years)),
    y_range=Range1d(0, 100),
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=60,
)

for i, name in enumerate(table.columns):
    source = ColumnDataSource({YEAR: years, "lower": lower[name].to_numpy(), "upper": upper[name].to_numpy()})
    p.varea(
        x=YEAR,
        y1="lower",
        y2="upper",
        source=source,
        fill_color=IMPRINT_PALETTE[i],
        fill_alpha=0.9,
        legend_label=str(name),
    )
    p.line(x=YEAR, y="upper", source=source, line_color=PAGE_BG, line_width=3)

# Style
p.title.text_font_size = "50pt"
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"

p.xgrid.grid_line_alpha = 0.0
p.ygrid.grid_line_alpha = 0.0
p.xaxis.ticker = years
p.yaxis.ticker = [0, 20, 40, 60, 80, 100]

legend = p.legend[0]
p.add_layout(legend, "right")
legend.title = PRODUCT
legend.title_text_font_size = "30pt"
legend.label_text_font_size = "30pt"
legend.glyph_height = 40
legend.glyph_width = 40
legend.spacing = 14
legend.padding = 20
legend.background_fill_color = ELEVATED_BG
legend.border_line_color = INK_SOFT
legend.label_text_color = INK_SOFT
legend.title_text_color = INK
# Stack order top-down in the legend matches the stack
legend.items.reverse()

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

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome via Selenium
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
