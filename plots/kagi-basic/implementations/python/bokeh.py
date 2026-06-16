""" anyplot.ai
kagi-basic: Basic Kagi Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-17
"""

import os
import sys
import time
from pathlib import Path


# Remove script directory from sys.path to avoid shadowing bokeh package
script_dir = os.path.dirname(os.path.abspath(__file__))
while script_dir in sys.path:
    sys.path.remove(script_dir)
if "" in sys.path:
    sys.path.remove("")
if "." in sys.path:
    sys.path.remove(".")

import numpy as np  # noqa: E402
from bokeh.io import output_file, save  # noqa: E402
from bokeh.models import ColumnDataSource, Legend, LegendItem  # noqa: E402
from bokeh.plotting import figure  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
YANG_COLOR = "#009E73"  # First series - bluish green
YIN_COLOR = "#AE3030"  # imprint red — bearish

# Data generation
np.random.seed(42)
n_days = 250

# Simulate a stock price with trends
base_price = 100.0
returns = np.random.normal(0.001, 0.02, n_days)
# Add some trending periods
returns[20:60] += 0.003  # Uptrend
returns[80:120] -= 0.004  # Downtrend
returns[150:200] += 0.002  # Uptrend
prices = base_price * np.cumprod(1 + returns)

# Kagi chart algorithm
reversal_pct = 0.04  # 4% reversal threshold

current_price = prices[0]
direction = 1  # 1 for up, -1 for down
is_yang = True  # Start as yang (thick)
line_index = 0
last_high = prices[0]
last_low = prices[0]

# Store kagi line segments: (x1, y1, x2, y2, is_yang)
segments = []

for i in range(1, len(prices)):
    price = prices[i]
    reversal_amount = current_price * reversal_pct

    if direction == 1:  # Currently going up
        if price > current_price:
            # Continue upward - extend vertical line
            if price > last_high:
                is_yang = True  # Becomes yang when exceeds previous high
            last_high = max(last_high, price)
            segments.append((line_index, current_price, line_index, price, is_yang))
            current_price = price
        elif current_price - price >= reversal_amount:
            # Reversal down - draw horizontal shoulder
            segments.append((line_index, current_price, line_index + 1, current_price, is_yang))
            line_index += 1
            direction = -1
            if price < last_low:
                is_yang = False  # Becomes yin when falls below previous low
            last_low = min(last_low, price)
            segments.append((line_index, current_price, line_index, price, is_yang))
            current_price = price
    else:  # Currently going down
        if price < current_price:
            # Continue downward - extend vertical line
            if price < last_low:
                is_yang = False  # Becomes yin when falls below previous low
            last_low = min(last_low, price)
            segments.append((line_index, current_price, line_index, price, is_yang))
            current_price = price
        elif price - current_price >= reversal_amount:
            # Reversal up - draw horizontal waist
            segments.append((line_index, current_price, line_index + 1, current_price, is_yang))
            line_index += 1
            direction = 1
            if price > last_high:
                is_yang = True  # Becomes yang when exceeds previous high
            last_high = max(last_high, price)
            segments.append((line_index, current_price, line_index, price, is_yang))
            current_price = price

# Prepare data for ColumnDataSource - separate yang and yin
xs_yang, ys_yang = [], []
xs_yin, ys_yin = [], []

for seg in segments:
    x1, y1, x2, y2, yang = seg
    if yang:
        xs_yang.append([x1, x2])
        ys_yang.append([y1, y2])
    else:
        xs_yin.append([x1, x2])
        ys_yin.append([y1, y2])

source_yang = ColumnDataSource(data={"xs": xs_yang, "ys": ys_yang})
source_yin = ColumnDataSource(data={"xs": xs_yin, "ys": ys_yin})

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="kagi-basic · bokeh · anyplot.ai",
    x_axis_label="Line Index",
    y_axis_label="Price ($)",
)

# Plot kagi lines - yang (thick) and yin (thin) with ColumnDataSource
yang_renderer = p.multi_line(xs="xs", ys="ys", source=source_yang, line_color=YANG_COLOR, line_width=8)
yin_renderer = p.multi_line(xs="xs", ys="ys", source=source_yin, line_color=YIN_COLOR, line_width=3)

# Styling - scaled for 4800x2700 canvas
p.title.text_font_size = "28pt"
p.title.text_color = INK

p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK

p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# Grid styling - subtle, solid lines
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

# Background
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Add legend with larger, more prominent text
legend = Legend(
    items=[
        LegendItem(label="Yang (Uptrend)", renderers=[yang_renderer]),
        LegendItem(label="Yin (Downtrend)", renderers=[yin_renderer]),
    ],
    location="top_left",
    label_text_font_size="20pt",
)

p.add_layout(legend)
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 0.9
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome via Selenium
W, H = 4800, 2700
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
time.sleep(3)  # Let Bokeh's JS render
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
