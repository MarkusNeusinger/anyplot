"""anyplot.ai
arc-basic: Basic Arc Diagram
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-30
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, LabelSet, Legend, LegendItem, Range1d, Title
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (Imprint palette — theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential ramp for marks (arcs are lines on the page), low -> high
SEQ_MARKS = (
    [(0.0, "#009E73"), (0.338, "#4467A3"), (1.0, "#002850")]
    if THEME == "light"
    else [(0.0, "#007755"), (0.32, "#009E73"), (1.0, "#CDD9FF")]
)

# Constants
ARC_RATIO = 0.5  # arc height per unit of distance between the two nodes

# Columns: set these to your table's column names
SOURCE = "Speaker"  # role: edges
TARGET = "Responder"  # role: extra
WEIGHT = "Shared scenes"  # role: weights

# Data: replace this block with your own edge list, for example df = pd.read_csv("edges.csv")
# Character interactions in one chapter of a story; nodes follow the order of first appearance.
df = pd.DataFrame(
    {
        SOURCE: ["Alice", "Alice", "Bob", "Carol", "Alice", "David", "Eve", "Alice", "Bob", "Carol", "Frank", "Bob"],
        TARGET: ["Bob", "Carol", "David", "Eve", "Frank", "Grace", "Henry", "Henry", "Eve", "Grace", "Henry", "Carol"],
        WEIGHT: [3, 2, 1, 2, 1, 2, 1, 3, 2, 1, 2, 1],
    }
)

# Plot: reads only df and the constants above
nodes = list(pd.unique(df[[SOURCE, TARGET]].to_numpy().ravel()))
position = {name: float(i) for i, name in enumerate(nodes)}

arcs = pd.DataFrame(
    {
        SOURCE: df[SOURCE],
        TARGET: df[TARGET],
        WEIGHT: df[WEIGHT],
        "x0": df[SOURCE].map(position),
        "x1": df[TARGET].map(position),
    }
)
arcs["y0"] = 0.0
arcs["y1"] = 0.0
arcs["cx0"] = arcs["x0"] + (arcs["x1"] - arcs["x0"]) / 3
arcs["cx1"] = arcs["x0"] + 2 * (arcs["x1"] - arcs["x0"]) / 3
arcs["cy"] = (arcs["x1"] - arcs["x0"]).abs() * ARC_RATIO
peak = arcs["cy"].max() * 0.75  # a cubic bezier with both controls at height h peaks at 0.75 h

w_min, w_max = df[WEIGHT].min(), df[WEIGHT].max()
stop_pos = [s[0] for s in SEQ_MARKS]
stop_rgb = list(zip(*[[int(s[1][k : k + 2], 16) for k in (1, 3, 5)] for s in SEQ_MARKS], strict=True))

p = figure(
    width=3200,
    height=1800,
    title="arc-basic · python · bokeh · anyplot.ai",
    x_range=Range1d(-0.6, len(nodes) - 0.4),
    y_range=Range1d(-0.5, peak * 1.1),
    toolbar_location=None,
    min_border_bottom=60,
    min_border_left=60,
    min_border_top=40,
    min_border_right=60,
)

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.add_layout(
    Title(text="Character interaction frequency · Chapter 1", text_font_size="30pt", text_color=INK_SOFT), "above"
)

# Arcs: one renderer per weight level, ordered levels run along the sequential ramp
legend_items = []
for level, rows in arcs.groupby(WEIGHT):
    share = (level - w_min) / (w_max - w_min) if w_max > w_min else 0.0
    # on dark, start the ramp at its brand-green stop so the lightest level stays visible on the page
    t = share if THEME == "light" else stop_pos[1] + (1 - stop_pos[1]) * share
    color = "#" + "".join(f"{round(np.interp(t, stop_pos, channel)):02X}" for channel in stop_rgb)
    renderer = p.bezier(
        x0="x0",
        y0="y0",
        x1="x1",
        y1="y1",
        cx0="cx0",
        cy0="cy",
        cx1="cx1",
        cy1="cy",
        source=ColumnDataSource(rows),
        line_width=4 + 8 * level / w_max,
        line_color=color,
        line_alpha=0.55 + 0.3 * level / w_max,
    )
    legend_items.append(LegendItem(label=str(level), renderers=[renderer]))
    p.add_tools(
        HoverTool(
            renderers=[renderer],
            tooltips=[("Connection", f"@{{{SOURCE}}} ↔ @{{{TARGET}}}"), (WEIGHT, f"@{{{WEIGHT}}}")],
            line_policy="interp",
        )
    )

# Nodes on the baseline, labels below
node_source = ColumnDataSource({"x": list(position.values()), "y": [0.0] * len(nodes), "name": nodes})
p.scatter(x="x", y="y", source=node_source, size=44, fill_color=IMPRINT_PALETTE[0], line_color=PAGE_BG, line_width=4)
p.add_layout(
    LabelSet(
        x="x",
        y="y",
        text="name",
        source=node_source,
        y_offset=-40,
        text_font_size="34pt",
        text_align="center",
        text_baseline="top",
        text_color=INK,
    )
)

legend = Legend(
    items=legend_items,
    title=WEIGHT,
    location="top_right",
    title_text_font_size="34pt",
    title_text_color=INK,
    label_text_font_size="34pt",
    label_text_color=INK_SOFT,
    border_line_color=INK_SOFT,
    border_line_alpha=0.5,
    background_fill_color=ELEVATED_BG,
    glyph_width=70,
    glyph_height=40,
    label_standoff=16,
    spacing=12,
    padding=20,
)
p.add_layout(legend)

# Save interactive HTML (catalog artifact)
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome via Selenium (export_png uses snap chromedriver which fails)
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
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_script(
    "document.documentElement.style.background = arguments[0]; document.body.style.background = arguments[0];", PAGE_BG
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
