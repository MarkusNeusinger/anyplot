"""anyplot.ai
point-and-figure-basic: Point and Figure Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-20
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import FixedTicker, Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette positions used
X_COLOR = "#009E73"  # position 1 — brand green, bullish X columns
O_COLOR = "#AE3030"  # imprint red — bearish O columns
SUPPORT_COLOR = "#4467A3"  # Imprint position 3 — blue, ascending support line
RESISTANCE_COLOR = "#BD8233"  # Imprint position 4 — ochre, descending resistance line

# Constants
BOX_SIZE = 2.0  # price per box, in dollars
REVERSAL = 3  # boxes of reverse movement that start a new column
UP, DOWN = "X", "O"  # symbols of rising and falling columns

# Columns: set these to your table's column names
DATE = "date"  # role: date
HIGH = "high"  # role: high
LOW = "low"  # role: low
CLOSE = "close"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 300
daily_returns = np.random.normal(0.0005, 0.015, n_days)

# Trending periods give the chart visible breakouts
daily_returns[50:80] += 0.003
daily_returns[100:140] -= 0.004
daily_returns[180:220] += 0.0035
daily_returns[240:280] -= 0.003

close_prices = 100 * np.cumprod(1 + daily_returns)
volatility = np.abs(np.random.normal(0, 0.01, n_days))
df = pd.DataFrame(
    {
        DATE: pd.date_range("2024-01-01", periods=n_days, freq="D"),
        HIGH: close_prices * (1 + volatility),
        LOW: close_prices * (1 - volatility),
        CLOSE: close_prices,
    }
)

# Plot
# Point and Figure algorithm: build columns of boxes from the closing prices
closes = df[CLOSE].to_numpy()
box_start = np.floor(closes[0] / BOX_SIZE) * BOX_SIZE
columns = []  # (symbol, first box, last box)
direction = None
col_start = col_end = box_start

for price in closes:
    box_price = np.floor(price / BOX_SIZE) * BOX_SIZE
    if direction is None:
        if price >= box_start + BOX_SIZE:
            direction, col_end = UP, box_price
        elif price <= box_start - BOX_SIZE:
            direction, col_end = DOWN, box_price
    elif direction == UP:
        if box_price >= col_end + BOX_SIZE:
            col_end = box_price
        elif box_price <= col_end - REVERSAL * BOX_SIZE:
            columns.append((direction, col_start, col_end))
            direction, col_start, col_end = DOWN, col_end - BOX_SIZE, box_price
    else:
        if box_price <= col_end - BOX_SIZE:
            col_end = box_price
        elif box_price >= col_end + REVERSAL * BOX_SIZE:
            columns.append((direction, col_start, col_end))
            direction, col_start, col_end = UP, col_end + BOX_SIZE, box_price
if direction is not None:
    columns.append((direction, col_start, col_end))

# One symbol per box
symbols = {UP: ([], []), DOWN: ([], [])}
for col_idx, (kind, start, end) in enumerate(columns):
    boxes = np.arange(min(start, end), max(start, end) + BOX_SIZE / 2, BOX_SIZE)
    symbols[kind][0].extend([col_idx] * len(boxes))
    symbols[kind][1].extend(boxes.tolist())

n_cols = len(columns)
all_prices = symbols[UP][1] + symbols[DOWN][1]
min_price, max_price = min(all_prices), max(all_prices)

# Grid ticks at exact box-size intervals
price_ticks = np.arange(
    np.floor(min_price / BOX_SIZE) * BOX_SIZE, np.ceil(max_price / BOX_SIZE) * BOX_SIZE + BOX_SIZE, BOX_SIZE
).tolist()

p = figure(
    width=3200,
    height=1800,
    title="point-and-figure-basic · python · bokeh · anyplot.ai",
    x_axis_label="Column (Reversal)",
    y_axis_label="Price ($)",
    toolbar_location=None,
    x_range=Range1d(-0.5, n_cols - 0.5),
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Font sizes for 3200×1800 canvas
p.title.text_font_size = "50pt"
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"

# Theme-adaptive chrome
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

# Grid at exact box-size intervals
p.ygrid.ticker = FixedTicker(ticks=price_ticks)
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

# X symbols for rising columns, O symbols for falling columns
for kind, color, label in ((UP, X_COLOR, "X — Bullish"), (DOWN, O_COLOR, "O — Bearish")):
    cols, prices = symbols[kind]
    p.text(
        x=cols,
        y=prices,
        text=[kind] * len(cols),
        text_font_size="30pt",
        text_color=color,
        text_align="center",
        text_baseline="middle",
        text_font_style="bold",
        legend_label=label,
    )

# Support trend line: 45 degrees up, one box per column
support_start = min_price - BOX_SIZE
support_end = support_start + (n_cols - 1) * BOX_SIZE
if support_end <= max_price + 2 * BOX_SIZE:
    p.line(
        x=[0, n_cols - 1],
        y=[support_start, support_end],
        line_width=4,
        line_color=SUPPORT_COLOR,
        legend_label="Support",
    )

# Resistance trend line: 45 degrees down, one box per column
resistance_start = max_price + BOX_SIZE
resistance_end = resistance_start - (n_cols - 1) * BOX_SIZE
if resistance_end >= min_price - 2 * BOX_SIZE:
    p.line(
        x=[0, n_cols - 1],
        y=[resistance_start, resistance_end],
        line_width=4,
        line_color=RESISTANCE_COLOR,
        legend_label="Resistance",
    )

# Legend
p.legend.location = "top_left"
p.legend.label_text_font_size = "34pt"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome (export_png unavailable in this env)
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
