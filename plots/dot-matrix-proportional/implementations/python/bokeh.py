"""anyplot.ai
dot-matrix-proportional: Dot Matrix Chart for Proportional Counts
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-11-18
"""

import os as _os
import sys


# Prevent this file (bokeh.py) from shadowing the real bokeh package.
# When Python runs a script, it inserts the script's directory into sys.path[0].
# Since this file IS named bokeh.py, that directory entry must be removed first.
_here = _os.path.dirname(_os.path.abspath(__file__))
sys.path = [p for p in sys.path if _os.path.abspath(p) != _here]
del _here, _os

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

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
CATEGORY = "Exercise frequency"  # role: category
COUNT = "Respondents"  # role: count
TOTAL = "Population"  # role: total

# Data: replace this block with your own table, for example df = pd.read_csv("survey.csv")
df = pd.DataFrame(
    {
        CATEGORY: ["Daily", "3–5 times/week", "1–2 times/week", "Rarely / Never"],
        COUNT: [52, 74, 46, 28],
        TOTAL: [200, 200, 200, 200],
    }
)

# Plot: reads only df and the constants above
df = df.dropna(subset=[COUNT]).reset_index(drop=True)
df[COUNT] = df[COUNT].astype(int)
total = max(int(df[TOTAL].max()), int(df[COUNT].sum()))
n_cols = math.ceil(math.sqrt(2 * total))  # roughly 2:1 grid, 20 x 10 for 200
n_rows = math.ceil(total / n_cols)

# Fill left to right, top to bottom: dot k sits in column k % n_cols of row k // n_cols
dots = df.loc[df.index.repeat(df[COUNT])].reset_index(drop=True)
dots["x"] = dots.index % n_cols
dots["y"] = n_rows - 1 - dots.index // n_cols
dots["share"] = (dots[COUNT] / total * 100).round().astype(int)

W, H = 3200, 1800
title = "dot-matrix-proportional · python · bokeh · anyplot.ai"
p = figure(
    width=W,
    height=H,
    title=title,
    toolbar_location=None,
    x_range=(-0.8, n_cols - 0.2),
    y_range=(-0.8, n_rows - 0.2),
    match_aspect=True,
    min_border_top=110,
    min_border_bottom=60,
    min_border_left=60,
    min_border_right=60,
)

renderers = []
legend_items = []
for i, cat in enumerate(df[CATEGORY]):
    src = ColumnDataSource(dots[dots[CATEGORY] == cat])
    r = p.scatter(
        "x",
        "y",
        source=src,
        color=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
        size=104,
        line_color=PAGE_BG,
        line_width=2,
    )
    renderers.append(r)
    count = int(df[COUNT].iloc[i])
    share = round(count / total * 100)
    legend_items.append(LegendItem(label=f"{cat}  ({count} · {share}%)", renderers=[r]))

p.add_tools(
    HoverTool(
        renderers=renderers, tooltips=[("Category", f"@{{{CATEGORY}}}"), (COUNT, f"@{{{COUNT}}}"), ("Share", "@share%")]
    )
)

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.title.align = "center"
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None

# Legend in a right panel, outside the dot grid
legend = Legend(
    items=legend_items,
    title=f"{CATEGORY}  (n = {total})",
    title_text_font_size="34pt",
    title_text_color=INK,
    background_fill_color=ELEVATED_BG,
    border_line_color=INK_SOFT,
    label_text_color=INK,
    label_text_font_size="32pt",
    glyph_height=60,
    glyph_width=60,
    spacing=24,
    padding=30,
)
p.add_layout(legend, "right")

# Save HTML, then screenshot it with headless Chrome
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
