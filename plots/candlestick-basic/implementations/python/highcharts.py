""" anyplot.ai
candlestick-basic: Basic Candlestick Chart
Library: highcharts unknown | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-30
"""

import json
import os
import tempfile
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.spline import SplineSeries
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens — Imprint palette + theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Semantic exception: finance up=green / down=red per Imprint palette
BULL_COLOR = "#009E73"  # Imprint position 1 — bullish / gain
BEAR_COLOR = "#AE3030"  # Imprint position 5 — bearish / loss (semantic anchor)
SMA_COLOR = "#4467A3"  # Imprint position 3 — moving average overlay

# Data — 30 trading days of simulated stock prices
np.random.seed(42)
start_price = 150.0
n_days = 30

opens = [start_price]
highs = []
lows = []
closes = []

for i in range(n_days):
    open_price = opens[i] if i == 0 else closes[i - 1] + np.random.randn() * 0.5
    if i > 0:
        opens.append(open_price)

    daily_range = abs(np.random.randn() * 2) + 1
    direction = np.random.choice([-1, 1], p=[0.45, 0.55])

    close_price = open_price + direction * np.random.rand() * daily_range
    high_price = max(open_price, close_price) + abs(np.random.randn() * 0.5)
    low_price = min(open_price, close_price) - abs(np.random.randn() * 0.5)

    highs.append(round(high_price, 2))
    lows.append(round(low_price, 2))
    closes.append(round(close_price, 2))

opens = [round(o, 2) for o in opens]

# Trading dates — skip weekends
start_date = datetime(2024, 10, 1)
dates = []
current_date = start_date
while len(dates) < n_days:
    if current_date.weekday() < 5:
        dates.append(current_date)
    current_date += timedelta(days=1)

# Format as [timestamp_ms, open, high, low, close]
ohlc_data = []
timestamps = []
for i in range(n_days):
    ts = int(dates[i].timestamp() * 1000)
    timestamps.append(ts)
    ohlc_data.append([ts, opens[i], highs[i], lows[i], closes[i]])

# 5-day simple moving average
sma_period = 5
sma_data = []
for i in range(n_days):
    if i >= sma_period - 1:
        avg = np.mean(closes[i - sma_period + 1 : i + 1])
        sma_data.append([timestamps[i], round(float(avg), 2)])

# Trough plotBand for analytical focus
min_close_idx = int(np.argmin(closes))
trough_price = closes[min_close_idx]

# Title fontsize: 75 chars > 67 baseline → round(66 × 67/75) = 59px (floor 44px)
title = "Stock Price Movement · candlestick-basic · python · highcharts · anyplot.ai"
title_fontsize = f"{max(44, round(66 * 67 / len(title)))}px"

# Build chart using highcharts_core Python API
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "marginBottom": 160,
    "marginLeft": 220,
    "marginRight": 80,
    "marginTop": 140,
    "style": {"fontFamily": "'Segoe UI', Arial, sans-serif"},
}

chart.options.title = {"text": title, "style": {"fontSize": title_fontsize, "fontWeight": "600", "color": INK}, "y": 55}

chart.options.x_axis = {
    "type": "datetime",
    "title": {"text": "Date", "style": {"fontSize": "56px", "color": INK}, "margin": 20},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}, "format": "{value:%b %d}", "step": 2, "y": 36},
    "gridLineWidth": 0,
    "lineWidth": 1,
    "lineColor": INK_SOFT,
    "tickWidth": 0,
}

chart.options.y_axis = {
    "title": {"text": "Price (USD)", "style": {"fontSize": "56px", "color": INK}, "margin": 20},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}, "format": "${value:.0f}", "x": -12},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "gridLineDashStyle": "Dot",
    "lineWidth": 0,
    "tickWidth": 0,
    "tickInterval": 2,
    "plotBands": [
        {
            "from": trough_price - 0.4,
            "to": trough_price + 0.4,
            "color": "rgba(174,48,48,0.07)",
            "label": {
                "text": f"Trough → ${trough_price:.2f}",
                "align": "right",
                "x": -12,
                "style": {"fontSize": "32px", "color": BEAR_COLOR, "fontStyle": "italic"},
            },
        }
    ],
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "horizontal",
    "x": -50,
    "y": 50,
    "floating": True,
    "itemStyle": {"fontSize": "36px", "fontWeight": "400", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "symbolWidth": 36,
    "symbolRadius": 0,
}

chart.options.tooltip = {
    "split": False,
    "shared": True,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "style": {"fontSize": "32px", "color": INK},
    "headerFormat": "<b>{point.x:%b %d, %Y}</b><br/>",
}

# SMA overlay via SplineSeries — native highcharts_core Python API
sma_series = SplineSeries()
sma_series.name = "5-day SMA"
sma_series.data = sma_data
sma_series.color = SMA_COLOR
chart.options.series = [sma_series]

# Serialize base options via Python API, then inject Highstock-specific options
opts = chart.options.to_dict()

# Subtitle: not natively captured by highcharts_core.to_dict() for Highstock
opts["subtitle"] = {
    "text": "30 trading days with 5-day moving average — Oct–Nov 2024",
    "style": {"fontSize": "36px", "color": INK_SOFT, "fontWeight": "300"},
    "y": 105,
}

# plotOptions.candlestick: not in highcharts_core (Highstock-only series type)
opts["plotOptions"] = {
    "candlestick": {
        "color": BEAR_COLOR,
        "upColor": BULL_COLOR,
        "lineColor": BEAR_COLOR,
        "upLineColor": BULL_COLOR,
        "lineWidth": 3,
        "pointWidth": 55,
        "tooltip": {
            "pointFormat": (
                "Open: ${point.open:.2f}<br/>"
                "High: ${point.high:.2f}<br/>"
                "Low: ${point.low:.2f}<br/>"
                "Close: ${point.close:.2f}"
            )
        },
    },
    "spline": {
        "lineWidth": 4,
        "marker": {"enabled": False},
        "dashStyle": "ShortDash",
        "tooltip": {"pointFormat": "SMA(5): <b>${point.y:.2f}</b>"},
    },
}

# Prepend candlestick OHLC series; SMA spline already in opts from Python API
opts["series"] = [{"type": "candlestick", "name": "OHLC", "data": ohlc_data, "zIndex": 1}] + opts.get("series", [])

# Highstock navigator/range-selector are not needed for a static 30-day view
opts["rangeSelector"] = {"enabled": False}
opts["navigator"] = {"enabled": False}
opts["scrollbar"] = {"enabled": False}
opts["credits"] = {"enabled": False}

opts_json = json.dumps(opts)
js_str = (
    f"document.addEventListener('DOMContentLoaded', function() {{\n"
    f"  Highcharts.stockChart('container', {opts_json});\n"
    f"}});"
)

# Download Highstock JS (candlestick is a Highstock-only series type)
highstock_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highstock.js"
with urllib.request.urlopen(highstock_url, timeout=30) as response:
    highstock_js = response.read().decode("utf-8")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highstock_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{js_str}</script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Selenium screenshot — CDP override forces exact 3200×1800 viewport
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=3200,1800")

driver = webdriver.Chrome(options=chrome_options)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# PIL normalization — guarantees exact 3200×1800 if CDP rounding drifts
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.size != (3200, 1800):
    norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    norm.paste(img, ((3200 - img.size[0]) // 2, (1800 - img.size[1]) // 2))
    norm.save(f"plot-{THEME}.png")
