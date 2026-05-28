""" anyplot.ai
ohlc-bar: OHLC Bar Chart
Library: highcharts unknown | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-23
"""

import json
import os
import tempfile
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Semantic exception: finance — green=bullish/up, red=bearish/down (anyplot positions 1 and 3)
UP_COLOR = "#009E73"
DOWN_COLOR = "#AE3030"

# Data — 50 trading days of simulated stock prices
np.random.seed(42)

start_price = 150.0
n_days = 50

opens = [start_price]
highs = []
lows = []
closes = []

for i in range(n_days):
    open_price = opens[i] if i == 0 else closes[i - 1] + np.random.randn() * 0.3
    if i > 0:
        opens.append(open_price)

    daily_range = abs(np.random.randn() * 2) + 0.5
    direction = np.random.choice([-1, 1], p=[0.48, 0.52])

    close_price = open_price + direction * np.random.rand() * daily_range
    high_price = max(open_price, close_price) + abs(np.random.randn() * 0.8)
    low_price = min(open_price, close_price) - abs(np.random.randn() * 0.8)

    highs.append(round(high_price, 2))
    lows.append(round(low_price, 2))
    closes.append(round(close_price, 2))

opens = [round(o, 2) for o in opens]

# 5-day SMA for trend layer
sma_period = 5
sma_closes = []
for i in range(sma_period - 1, n_days):
    avg = sum(closes[i - sma_period + 1 : i + 1]) / sma_period
    sma_closes.append(round(avg, 2))

# Generate trading dates (skip weekends)
start_date = datetime(2024, 6, 1)
dates = []
current_date = start_date
while len(dates) < n_days:
    if current_date.weekday() < 5:
        dates.append(current_date)
    current_date += timedelta(days=1)

# Format as Highcharts timestamps: [timestamp_ms, open, high, low, close]
ohlc_data = []
for i in range(n_days):
    timestamp = int(dates[i].timestamp() * 1000)
    ohlc_data.append([timestamp, opens[i], highs[i], lows[i], closes[i]])

sma_data = []
for i in range(sma_period - 1, n_days):
    timestamp = int(dates[i].timestamp() * 1000)
    sma_data.append([timestamp, sma_closes[i - (sma_period - 1)]])

# Net-change subtitle for data storytelling
net_change = closes[-1] - opens[0]
pct_change = net_change / opens[0] * 100
sign = "+" if net_change >= 0 else ""
subtitle_text = f"Jun–Aug 2024  ·  Net change: {sign}${net_change:.2f} / {sign}{pct_change:.1f}%"

title = "ohlc-bar · python · highcharts · anyplot.ai"

chart_options = {
    "chart": {
        "type": "ohlc",
        "width": 3200,
        "height": 1800,
        "backgroundColor": PAGE_BG,
        "plotBorderWidth": 0,
        "marginBottom": 160,
        "marginLeft": 200,
        "marginRight": 80,
        "marginTop": 150,
        "style": {"fontFamily": "Arial, sans-serif", "color": INK},
    },
    "title": {"text": title, "style": {"fontSize": "66px", "fontWeight": "600", "color": INK}, "y": 55},
    "subtitle": {"text": subtitle_text, "style": {"fontSize": "36px", "color": INK_SOFT}, "y": 110},
    "xAxis": {
        "type": "datetime",
        "title": {"text": "Date", "style": {"fontSize": "56px", "color": INK}, "margin": 25},
        "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}, "format": "{value:%b %d}", "y": 40, "step": 3},
        "gridLineWidth": 1,
        "gridLineColor": GRID,
        "lineWidth": 2,
        "lineColor": INK_SOFT,
        "tickWidth": 2,
        "tickColor": INK_SOFT,
        "tickLength": 10,
    },
    "yAxis": {
        "title": {"text": "Price (USD)", "style": {"fontSize": "56px", "color": INK}, "margin": 25},
        "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}, "format": "${value:.0f}", "x": -15},
        "gridLineWidth": 1,
        "gridLineColor": GRID,
        "lineWidth": 2,
        "lineColor": INK_SOFT,
        "opposite": False,
    },
    "legend": {
        "enabled": True,
        "itemStyle": {"color": INK_SOFT, "fontSize": "36px", "fontWeight": "normal"},
        "backgroundColor": "transparent",
        "borderWidth": 0,
        "align": "right",
        "verticalAlign": "top",
        "layout": "vertical",
        "x": -80,
        "y": 160,
    },
    "tooltip": {
        "split": False,
        "style": {"fontSize": "32px"},
        "headerFormat": "<b>{point.x:%b %d, %Y}</b><br/>",
        "pointFormat": "Open: ${point.open:.2f}<br/>"
        + "High: ${point.high:.2f}<br/>"
        + "Low: ${point.low:.2f}<br/>"
        + "Close: ${point.close:.2f}",
    },
    "plotOptions": {"ohlc": {"color": DOWN_COLOR, "upColor": UP_COLOR, "lineWidth": 4}},
    "rangeSelector": {"enabled": False},
    "navigator": {"enabled": False},
    "scrollbar": {"enabled": False},
    "credits": {"enabled": False},
    "series": [
        {"type": "ohlc", "name": "Stock Price", "data": ohlc_data},
        {
            "type": "line",
            "name": "5-day SMA",
            "data": sma_data,
            "color": INK_SOFT,
            "lineWidth": 2,
            "dashStyle": "Dash",
            "enableMouseTracking": False,
            "marker": {"enabled": False},
        },
    ],
}

# Download Highstock JS (OHLC type lives in Highstock)
highstock_url = "https://cdn.jsdelivr.net/npm/highcharts/highstock.js"
req = urllib.request.Request(highstock_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as response:
    highstock_js = response.read().decode("utf-8")

chart_options_json = json.dumps(chart_options)

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highstock_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            Highcharts.stockChart('container', {chart_options_json});
        }});
    </script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

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

# Pin to exact canvas dimensions
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
