"""anyplot.ai
ohlc-bar: OHLC Bar Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-17
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
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: up bars take brand green, down bars the matte red loss anchor
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
UP_COLOR = IMPRINT_PALETTE[0]
DOWN_COLOR = IMPRINT_PALETTE[4]

# Constants
PRICE_AXIS = "Price ($)"
TICK_WIDTH = 0.35  # open/close tick length in bar slots; below 0.5 so neighbors never touch
TARGET_DATE_LABELS = 10

# Columns: set these to your table's column names
DATE = "Date"  # role: date
OPEN = "Open"  # role: open
HIGH = "High"  # role: high
LOW = "Low"  # role: low
CLOSE = "Close"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 50
price = 150.0
rows = []
for day in pd.date_range("2025-06-01", periods=n_days, freq="B"):
    open_price = price
    close_price = open_price + np.random.randn() * 3
    volatility = abs(np.random.randn() * 2) + 1
    rows.append(
        {
            DATE: day,
            OPEN: open_price,
            HIGH: max(open_price, close_price) + volatility,
            LOW: min(open_price, close_price) - volatility,
            CLOSE: close_price,
        }
    )
    price = close_price + np.random.randn() * 0.5
df = pd.DataFrame(rows)

# Plot: reads only df and the constants above
bars = df.reset_index(drop=True)
bars["x"] = np.arange(len(bars))
bars["open_x"] = bars["x"] - TICK_WIDTH
bars["close_x"] = bars["x"] + TICK_WIDTH
bars["date_label"] = pd.to_datetime(bars[DATE]).dt.strftime("%Y-%m-%d")
is_up = bars[CLOSE] >= bars[OPEN]
price_low = bars[LOW].min()
price_high = bars[HIGH].max()
price_span = price_high - price_low

title = "ohlc-bar · python · bokeh · anyplot.ai"
p = figure(
    width=3200,
    height=1800,
    title=title,
    x_axis_label=DATE,
    y_axis_label=PRICE_AXIS,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
    y_range=Range1d(price_low - price_span * 0.05, price_high + price_span * 0.16),  # headroom for the legend
)

for label, color, mask in (("Up (close ≥ open)", UP_COLOR, is_up), ("Down (close < open)", DOWN_COLOR, ~is_up)):
    source = ColumnDataSource(bars[mask])
    range_bars = p.segment(
        x0="x", y0=LOW, x1="x", y1=HIGH, source=source, color=color, line_width=5, legend_label=label
    )
    p.segment(x0="open_x", y0=OPEN, x1="x", y1=OPEN, source=source, color=color, line_width=5, legend_label=label)
    p.segment(x0="x", y0=CLOSE, x1="close_x", y1=CLOSE, source=source, color=color, line_width=5, legend_label=label)
    p.add_tools(
        HoverTool(
            renderers=[range_bars],
            tooltips=[
                (DATE, "@date_label"),
                (OPEN, f"@{{{OPEN}}}{{0.00}}"),
                (HIGH, f"@{{{HIGH}}}{{0.00}}"),
                (LOW, f"@{{{LOW}}}{{0.00}}"),
                (CLOSE, f"@{{{CLOSE}}}{{0.00}}"),
            ],
        )
    )

# Date axis: trading-day slots without weekend gaps, labelled at an even spacing
label_step = max(1, len(bars) // TARGET_DATE_LABELS)
tick_positions = list(range(0, len(bars), label_step))
p.xaxis.ticker = tick_positions
p.xaxis.major_label_overrides = {
    i: pd.Timestamp(bars.loc[i, DATE]).strftime("%b %d") for i in tick_positions if pd.notna(bars.loc[i, DATE])
}

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_label_text_font_style = "normal"
p.yaxis.axis_label_text_font_style = "normal"
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = PAGE_BG  # None still leaves a faint frame in the PNG; the page color hides it
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.15

p.legend.location = "top_left"
p.legend.orientation = "horizontal"
p.legend.label_text_font_size = "34pt"
p.legend.label_text_color = INK_SOFT
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 0.9
p.legend.border_line_color = None
p.legend.glyph_width = 60
p.legend.spacing = 40
p.legend.padding = 20
p.legend.margin = 30

# Save
output_file(f"plot-{THEME}.html", title=title)
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
