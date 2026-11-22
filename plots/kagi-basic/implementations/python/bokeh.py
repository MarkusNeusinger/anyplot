"""anyplot.ai
kagi-basic: Basic Kagi Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Legend, LegendItem
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
YANG_COLOR = IMPRINT_PALETTE[0]  # thick, bullish
YIN_COLOR = IMPRINT_PALETTE[4]  # thin, bearish (semantic red)

# Constants
REVERSAL_PCT = 0.04  # a Kagi line turns only after a 4% move against its direction

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Close price ($)"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 250
returns = np.random.normal(0.001, 0.02, n_days)
returns[20:60] += 0.003  # uptrend
returns[80:120] -= 0.004  # downtrend
returns[150:200] += 0.002  # uptrend
df = pd.DataFrame({DATE: pd.date_range("2024-01-01", periods=n_days, freq="B"), CLOSE: 100.0 * np.cumprod(1 + returns)})

# Plot: reads only df and the constants above
prices = df[CLOSE].dropna().to_numpy()

# Kagi construction: (x1, y1, x2, y2, is_yang) per segment
current_price = prices[0]
direction = 1
is_yang = True
line_index = 0
last_high = prices[0]
last_low = prices[0]
segments = []

for price in prices[1:]:
    reversal_amount = current_price * REVERSAL_PCT
    if direction == 1:
        if price > current_price:
            if price > last_high:
                is_yang = True
            last_high = max(last_high, price)
            segments.append((line_index, current_price, line_index, price, is_yang))
            current_price = price
        elif current_price - price >= reversal_amount:
            segments.append((line_index, current_price, line_index + 1, current_price, is_yang))
            line_index += 1
            direction = -1
            if price < last_low:
                is_yang = False
            last_low = min(last_low, price)
            segments.append((line_index, current_price, line_index, price, is_yang))
            current_price = price
    else:
        if price < current_price:
            if price < last_low:
                is_yang = False
            last_low = min(last_low, price)
            segments.append((line_index, current_price, line_index, price, is_yang))
            current_price = price
        elif price - current_price >= reversal_amount:
            segments.append((line_index, current_price, line_index + 1, current_price, is_yang))
            line_index += 1
            direction = 1
            if price > last_high:
                is_yang = True
            last_high = max(last_high, price)
            segments.append((line_index, current_price, line_index, price, is_yang))
            current_price = price

yang = [s for s in segments if s[4]]
yin = [s for s in segments if not s[4]]
source_yang = ColumnDataSource(data={"xs": [[s[0], s[2]] for s in yang], "ys": [[s[1], s[3]] for s in yang]})
source_yin = ColumnDataSource(data={"xs": [[s[0], s[2]] for s in yin], "ys": [[s[1], s[3]] for s in yin]})

title = "kagi-basic · python · bokeh · anyplot.ai"
p = figure(
    width=3200,
    height=1800,
    title=title,
    x_axis_label="Line index",
    y_axis_label=CLOSE,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

yang_renderer = p.multi_line(xs="xs", ys="ys", source=source_yang, line_color=YANG_COLOR, line_width=10)
yin_renderer = p.multi_line(xs="xs", ys="ys", source=source_yin, line_color=YIN_COLOR, line_width=4)

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
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

legend = Legend(
    items=[
        LegendItem(label="Yang (thick, uptrend)", renderers=[yang_renderer]),
        LegendItem(label="Yin (thin, downtrend)", renderers=[yin_renderer]),
    ],
    location="top_left",
    label_text_font_size="34pt",
)
p.add_layout(legend)
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 0.9
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT

# Save HTML + PNG via headless Chrome
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
