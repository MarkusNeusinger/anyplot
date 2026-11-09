""" anyplot.ai
funnel-basic: Basic Funnel Chart
Library: bokeh 3.10.1 | Python 3.14.10
Quality: 88/100 | Updated: 2026-11-09
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: one position per stage, in process order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
STAGE = "Stage"  # role: stage
VALUE = "Visitors"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("funnel.csv")
df = pd.DataFrame(
    {
        STAGE: ["Awareness", "Interest", "Consideration", "Intent", "Purchase"],
        VALUE: [1000, 600, 400, 200, 100],
    }
)

# Plot: reads only df and the constants above
W, H = 3200, 1800
n_stages = len(df)
values = df[VALUE].astype(float).to_numpy()

# Each segment's top width is its value relative to the first stage; it narrows to the next stage's width,
# the last one to half its own. The widest segment spans one unit either side of the centre line.
share = values / values[0]
scale = 1 / np.nanmax(share)
half_top = share * scale
half_bottom = np.append(half_top[1:], half_top[-1] * 0.5)
y_top = n_stages - np.arange(n_stages)
y_bottom = y_top - 1
half_mid = (half_top + half_bottom) / 2
gap = 0.04 * np.nanmax(half_top)

# One palette position per stage; with more stages than positions, all segments take the brand color
by_stage = n_stages <= len(IMPRINT_PALETTE)
segments = df.copy()
segments["share"] = share
segments["color"] = [IMPRINT_PALETTE[i] if by_stage else IMPRINT_PALETTE[0] for i in range(n_stages)]
segments["xs"] = list(np.column_stack([-half_top, half_top, half_bottom, -half_bottom]))
segments["ys"] = list(np.column_stack([y_top, y_top, y_bottom, y_bottom]))
segments["y_mid"] = y_top - 0.5
segments["name_x"] = -half_mid - gap
segments["value_x"] = half_mid + gap
segments["value_text"] = [
    f"{value:,.0f}  ({part:.0%})" if np.isfinite(value) else "n/a" for value, part in zip(values, share, strict=True)
]
source = ColumnDataSource(segments)

title = "funnel-basic · python · bokeh · anyplot.ai"
reach = 1.6 * np.nanmax(half_top)  # room beside the widest segment for its name and value
p = figure(
    width=W,
    height=H,
    title=title,
    x_range=Range1d(-reach, reach),
    y_range=Range1d(-0.05 * n_stages, n_stages + 0.02 * n_stages),
    toolbar_location=None,
    min_border_left=60,
    min_border_right=60,
    min_border_top=110,
    min_border_bottom=60,
)

# Segments, separated by page-colored seams; stage names to the left, values to the right
seg_renderer = p.patches(
    xs="xs", ys="ys", source=source, fill_color="color", line_color=PAGE_BG, line_width=8, line_join="round"
)
p.text(
    x="name_x",
    y="y_mid",
    text=STAGE,
    source=source,
    text_align="right",
    text_baseline="middle",
    text_font_size="40pt",
    text_font_style="bold",
    text_color=INK,
)
p.text(
    x="value_x",
    y="y_mid",
    text="value_text",
    source=source,
    text_align="left",
    text_baseline="middle",
    text_font_size="38pt",
    text_color=INK_SOFT,
)

p.add_tools(
    HoverTool(
        renderers=[seg_renderer],
        tooltips=[(STAGE, f"@{{{STAGE}}}"), (VALUE, f"@{{{VALUE}}}{{0,0}}"), ("Share of first stage", "@share{0%}")],
    )
)

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.title.align = "center"
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = PAGE_BG  # covers the page-white seam at the frame's edge
p.outline_line_width = 2
p.axis.visible = False
p.grid.visible = False

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
