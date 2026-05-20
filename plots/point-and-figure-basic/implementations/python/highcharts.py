"""anyplot.ai
point-and-figure-basic: Point and Figure Chart
Library: highcharts | Python 3.13
Quality: 91/100 | Updated: 2026-05-20
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

BULL = "#009E73"  # Okabe-Ito position 1 — X (Rising, bullish)
BEAR = "#D55E00"  # Okabe-Ito position 2 — O (Falling, bearish)

# Data - Generate realistic stock price with multiple market phases
np.random.seed(42)
n_days = 300
base_price = 100

returns = np.zeros(n_days)
returns[:80] = np.random.normal(0.003, 0.015, 80)  # Uptrend
returns[80:140] = np.random.normal(-0.004, 0.018, 60)  # Downtrend
returns[140:200] = np.random.normal(0.0, 0.012, 60)  # Consolidation
returns[200:260] = np.random.normal(0.005, 0.015, 60)  # Strong uptrend
returns[260:] = np.random.normal(-0.003, 0.016, 40)  # Correction

prices = base_price * np.cumprod(1 + returns)

# P&F parameters
box_size = 2.0  # Each box represents $2
reversal = 3  # 3-box reversal required to start new column

# Build P&F columns — list of dicts with direction and set of box indices
columns = []
current_col = None
last_box = int(np.floor(prices[0] / box_size))

for price in prices:
    current_box = int(np.floor(price / box_size))

    if current_col is None:
        if current_box > last_box:
            current_col = {"direction": "X", "boxes": set(range(last_box, current_box + 1))}
            columns.append(current_col)
        elif current_box < last_box:
            current_col = {"direction": "O", "boxes": set(range(current_box, last_box + 1))}
            columns.append(current_col)
        last_box = current_box
        continue

    if current_col["direction"] == "X":
        if current_box > last_box:
            for b in range(last_box + 1, current_box + 1):
                current_col["boxes"].add(b)
            last_box = current_box
        elif current_box <= last_box - reversal:
            new_col = {"direction": "O", "boxes": set(range(current_box, last_box))}
            columns.append(new_col)
            current_col = new_col
            last_box = current_box
    else:
        if current_box < last_box:
            for b in range(current_box, last_box):
                current_col["boxes"].add(b)
            last_box = current_box
        elif current_box >= last_box + reversal:
            new_col = {"direction": "X", "boxes": set(range(last_box + 1, current_box + 1))}
            columns.append(new_col)
            current_col = new_col
            last_box = current_box

# Convert columns to scatter points
x_points = []
o_points = []

for col_idx, col in enumerate(columns):
    for box in col["boxes"]:
        point = {"x": col_idx, "y": box * box_size}
        if col["direction"] == "X":
            x_points.append(point)
        else:
            o_points.append(point)

# Price/column range for axis bounds
all_boxes = set()
for col in columns:
    all_boxes.update(col["boxes"])
min_box = min(all_boxes) if all_boxes else 40
max_box = max(all_boxes) if all_boxes else 70
max_col = len(columns) - 1 if columns else 0

# 45-degree support line: anchor at lowest O column bottom, slope = +box_size/column
support_anchor_col = None
support_anchor_price = None
for ci, col in enumerate(columns):
    if col["direction"] == "O":
        col_min_price = min(col["boxes"]) * box_size
        if support_anchor_price is None or col_min_price < support_anchor_price:
            support_anchor_price = col_min_price
            support_anchor_col = ci

# 45-degree resistance line: anchor at highest X column top, slope = -box_size/column
resist_anchor_col = None
resist_anchor_price = None
for ci, col in enumerate(columns):
    if col["direction"] == "X":
        col_max_price = max(col["boxes"]) * box_size
        if resist_anchor_price is None or col_max_price > resist_anchor_price:
            resist_anchor_price = col_max_price
            resist_anchor_col = ci

support_points = []
if support_anchor_col is not None:
    for c in range(support_anchor_col, max_col + 2):
        y = support_anchor_price + (c - support_anchor_col) * box_size
        if y <= (max_box + 2) * box_size:
            support_points.append({"x": c, "y": y})

resist_points = []
if resist_anchor_col is not None:
    for c in range(resist_anchor_col, max_col + 2):
        y = resist_anchor_price - (c - resist_anchor_col) * box_size
        if y >= (min_box - 2) * box_size:
            resist_points.append({"x": c, "y": y})

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "scatter",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "marginBottom": 160,
    "marginLeft": 200,
    "marginRight": 80,
    "marginTop": 160,
    "style": {"color": INK},
}

chart.options.title = {
    "text": "point-and-figure-basic · python · highcharts · anyplot.ai",
    "style": {"fontSize": "66px", "fontWeight": "bold", "color": INK},
}

chart.options.subtitle = {
    "text": f"Box Size: ${box_size:.0f} | {reversal}-Box Reversal | Simulated Stock",
    "style": {"fontSize": "44px", "color": INK_SOFT},
}

chart.options.x_axis = {
    "title": {"text": "Column (Reversal Number)", "style": {"fontSize": "56px", "color": INK}},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "tickInterval": 1,
    "min": -0.5,
    "max": max_col + 0.5,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

chart.options.y_axis = {
    "title": {"text": "Price ($)", "style": {"fontSize": "56px", "color": INK}},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}, "format": "${value}"},
    "tickInterval": box_size * 2,
    "min": (min_box - 2) * box_size,
    "max": (max_box + 2) * box_size,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -20,
    "y": 100,
    "itemStyle": {"fontSize": "44px", "fontWeight": "normal", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}

chart.options.tooltip = {
    "headerFormat": "<b>Column {point.x}</b><br/>",
    "pointFormat": "Price: ${point.y}",
    "style": {"fontSize": "40px"},
}

# X series (Rising) — Okabe-Ito position 1 (green)
x_series = ScatterSeries()
x_series.name = "X (Rising)"
x_series.data = x_points
x_series.color = BULL
x_series.marker = {"enabled": False}
x_series.data_labels = {
    "enabled": True,
    "format": "X",
    "style": {"fontSize": "40px", "fontWeight": "bold", "color": BULL, "textOutline": "none"},
    "align": "center",
    "verticalAlign": "middle",
    "y": 0,
}
chart.add_series(x_series)

# O series (Falling) — Okabe-Ito position 2 (vermillion)
o_series = ScatterSeries()
o_series.name = "O (Falling)"
o_series.data = o_points
o_series.color = BEAR
o_series.marker = {"enabled": False}
o_series.data_labels = {
    "enabled": True,
    "format": "O",
    "style": {"fontSize": "40px", "fontWeight": "bold", "color": BEAR, "textOutline": "none"},
    "align": "center",
    "verticalAlign": "middle",
    "y": 0,
}
chart.add_series(o_series)

# 45-degree support trend line (ascending lows)
if support_points:
    support_series = LineSeries()
    support_series.name = "Support (45°)"
    support_series.data = support_points
    support_series.color = BULL
    support_series.line_width = 4
    support_series.dash_style = "Dash"
    support_series.marker = {"enabled": False}
    chart.add_series(support_series)

# 45-degree resistance trend line (descending highs)
if resist_points:
    resist_series = LineSeries()
    resist_series.name = "Resistance (45°)"
    resist_series.data = resist_points
    resist_series.color = BEAR
    resist_series.line_width = 4
    resist_series.dash_style = "Dash"
    resist_series.marker = {"enabled": False}
    chart.add_series(resist_series)

# Download Highcharts JS for inline embedding (browser UA required to avoid 403)
_ua = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.highcharts.com/",
}
_req = urllib.request.Request("https://code.highcharts.com/highcharts.js", headers=_ua)
with urllib.request.urlopen(_req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot with Selenium
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=3200,1800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
