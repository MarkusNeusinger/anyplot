""" anyplot.ai
renko-basic: Basic Renko Chart
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-22
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BULLISH_COLOR = IMPRINT_PALETTE[0]  # up bricks: Imprint position 1 (green)
BEARISH_COLOR = IMPRINT_PALETTE[4]  # down bricks: Imprint red

# Constants
BRICK_SIZE = 2.0  # price move that draws one brick

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Close price ($)"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 200
df = pd.DataFrame(
    {
        DATE: pd.date_range("2024-01-01", periods=n_days, freq="D"),
        CLOSE: 100 * np.cumprod(1 + np.random.randn(n_days) * 0.02),
    }
)

# Plot: reads only df and the constants above
# Renko construction: a new brick starts where the last one ended, a reversal needs one extra brick of move
closes = df[CLOSE].dropna().to_numpy()
top = bottom = closes[0] - closes[0] % BRICK_SIZE
rows = []
for close in closes:
    while close >= top + BRICK_SIZE or close <= bottom - BRICK_SIZE:
        if close >= top + BRICK_SIZE:
            bottom, top = top, top + BRICK_SIZE
            direction = "Bullish"
        else:
            top, bottom = bottom, bottom - BRICK_SIZE
            direction = "Bearish"
        rows.append((len(rows), bottom, top, direction))
bricks = pd.DataFrame(rows, columns=["brick", "bottom", "top", "direction"])
bricks["range"] = [f"${b:.2f} - ${t:.2f}" for b, t in zip(bricks["bottom"], bricks["top"], strict=True)]

p = figure(
    width=3200,
    height=1800,
    title="renko-basic · python · bokeh · anyplot.ai",
    x_axis_label="Brick number",
    y_axis_label=CLOSE,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Theme-adaptive chrome
p.title.text_font_size = "50pt"
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
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

# One glyph layer per direction, drawn as vertical bars with a gap between columns
for direction, color in (("Bullish", BULLISH_COLOR), ("Bearish", BEARISH_COLOR)):
    group = bricks[bricks["direction"] == direction]
    if group.empty:
        continue
    renderer = p.vbar(
        x="brick",
        width=0.85,
        bottom="bottom",
        top="top",
        source=ColumnDataSource(group),
        color=color,
        line_color=color,
        line_width=1,
        legend_label=direction,
    )
    p.add_tools(
        HoverTool(
            renderers=[renderer], tooltips=[("Brick", "@brick"), ("Price range", "@range"), ("Direction", "@direction")]
        )
    )

# Legend styling
p.legend.location = "top_left"
p.legend.label_text_font_size = "34pt"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT
p.legend.glyph_height = 50
p.legend.glyph_width = 50

# Save HTML output
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
