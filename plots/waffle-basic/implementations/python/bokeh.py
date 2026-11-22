""" anyplot.ai
waffle-basic: Basic Waffle Chart
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-22
"""

import math
import os
import time
from pathlib import Path

import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Legend, LegendItem
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
SOURCE = "Energy source"  # role: category
SHARE = "Share of mix (%)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("mix.csv")
df = pd.DataFrame({SOURCE: ["Solar", "Wind", "Hydro", "Geothermal"], SHARE: [48, 25, 18, 9]})

# Plot: reads only df and the constants above
side = math.isqrt(round(df[SHARE].sum()))  # 10 x 10 grid: each square is 1% of the whole
squares = df.loc[df.index.repeat(df[SHARE].round().astype(int))].reset_index(drop=True)
squares["col"] = squares.index % side
squares["row"] = squares.index // side  # filled row by row, from the bottom

title = "Renewable Energy Sources · waffle-basic · python · bokeh · anyplot.ai"
title_pt = round(50 * min(1.0, 67 / len(title)))

p = figure(
    width=3200,
    height=1800,
    title=title,
    match_aspect=True,
    tools="",
    toolbar_location=None,
    min_border_top=110,
    min_border_bottom=100,
    min_border_left=60,
    min_border_right=60,
)

legend_items = []
for i, name in enumerate(df[SOURCE]):
    rows = squares[squares[SOURCE] == name]
    r = p.rect(
        x="col",
        y="row",
        width=0.9,
        height=0.9,
        source=ColumnDataSource(rows),
        fill_color=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
        line_color=PAGE_BG,
        line_width=2,
    )
    legend_items.append(LegendItem(label=f"{name} ({df[SHARE].iloc[i]}%)", renderers=[r]))

p.add_tools(HoverTool(tooltips=[(SOURCE, f"@{{{SOURCE}}}"), (SHARE, f"@{{{SHARE}}}")]))

legend = Legend(items=legend_items, location="center")
legend.label_text_font_size = "34pt"
legend.label_text_color = INK
legend.glyph_height = 60
legend.glyph_width = 60
legend.spacing = 24
legend.padding = 30
legend.margin = 40
legend.background_fill_color = ELEVATED_BG
legend.border_line_color = INK_SOFT
p.add_layout(legend, "right")

# Style
p.title.text_font_size = f"{title_pt}pt"
p.title.align = "center"
p.title.text_color = INK
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_color = None
p.outline_line_alpha = 0
p.x_range.range_padding = 0.01
p.y_range.range_padding = 0.01
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG

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
