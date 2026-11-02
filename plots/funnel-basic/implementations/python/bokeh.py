"""anyplot.ai
funnel-basic: Basic Funnel Chart
Library: bokeh | Python 3.14
Quality: pending | Updated: 2026-11-02
"""

import os
import time
from pathlib import Path

import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per stage in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
STAGE = "Stage"  # role: stage
VISITORS = "Visitors"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("funnel.csv")
df = pd.DataFrame(
    {STAGE: ["Awareness", "Interest", "Consideration", "Intent", "Purchase"], VISITORS: [1000, 600, 400, 200, 100]}
)

# Plot: reads only df and the constants above
n = len(df)
widths = (df[VISITORS] / df[VISITORS].iloc[0]).tolist()  # width relative to the first stage
bottoms = widths[1:] + [widths[-1] * 0.5]  # each segment tapers to the next stage; the last halves
tops_y = [n - i for i in range(n)]

source = ColumnDataSource(
    {
        "xs": [[-t / 2, t / 2, b / 2, -b / 2] for t, b in zip(widths, bottoms, strict=True)],
        "ys": [[y, y, y - 1, y - 1] for y in tops_y],
        "color": [IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i in range(n)],
        "mid_y": [y - 0.5 for y in tops_y],
        "stage": df[STAGE].tolist(),
        "value_text": [f"{v:,} ({w:.0%})" for v, w in zip(df[VISITORS], widths, strict=True)],
    }
)

title = "funnel-basic · python · bokeh · anyplot.ai"
p = figure(
    width=3200,
    height=1800,
    title=title,
    x_range=Range1d(-0.78, 0.78),
    y_range=Range1d(-0.1, n + 0.1),
    toolbar_location=None,
    min_border_top=110,
    min_border_bottom=60,
    min_border_left=60,
    min_border_right=60,
)
p.patches(xs="xs", ys="ys", source=source, fill_color="color", line_color=PAGE_BG, line_width=6)

# Stage names in the left column, values and share of the first stage in the right column
p.text(
    x=-0.76,
    y="mid_y",
    text="stage",
    source=source,
    text_font_size="38pt",
    text_font_style="bold",
    text_color=INK,
    text_align="left",
    text_baseline="middle",
)
p.text(
    x=0.76,
    y="mid_y",
    text="value_text",
    source=source,
    text_font_size="34pt",
    text_color=INK_SOFT,
    text_align="right",
    text_baseline="middle",
)

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.title.align = "center"
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
p.axis.visible = False
p.grid.visible = False

# Save
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
