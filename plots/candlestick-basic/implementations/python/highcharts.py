""" pyplots.ai
candlestick-basic: Basic Candlestick Chart
Library: highcharts 1.10.3 | Python 3.14.3
Quality: 90/100 | Updated: 2026-02-24
"""

import json
import tempfile
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - 30 trading days of simulated stock prices
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

# Generate dates (trading days, skip weekends)
start_date = datetime(2024, 10, 1)
dates = []
current_date = start_date
while len(dates) < n_days:
    if current_date.weekday() < 5:
        dates.append(current_date)
    current_date += timedelta(days=1)

# Format data for Highcharts: [timestamp, open, high, low, close]
ohlc_data = []
timestamps = []
for i in range(n_days):
    timestamp = int(dates[i].timestamp() * 1000)
    timestamps.append(timestamp)
    ohlc_data.append([timestamp, opens[i], highs[i], lows[i], closes[i]])

# Compute 5-day simple moving average for storytelling overlay
sma_period = 5
sma_data = []
for i in range(n_days):
    if i >= sma_period - 1:
        avg = np.mean(closes[i - sma_period + 1 : i + 1])
        sma_data.append([timestamps[i], round(float(avg), 2)])

# Find the trough point (lowest close) for visual emphasis
min_close_idx = int(np.argmin(closes))
trough_timestamp = timestamps[min_close_idx]
trough_price = closes[min_close_idx]

# Chart options
chart_options = {
    "chart": {
        "type": "candlestick",
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#FAFBFC",
        "marginBottom": 200,
        "marginLeft": 240,
        "marginRight": 100,
        "marginTop": 160,
        "style": {"fontFamily": "'Segoe UI', Arial, sans-serif"},
    },
    "title": {
        "text": "Stock Price Movement \u00b7 candlestick-basic \u00b7 highcharts \u00b7 pyplots.ai",
        "style": {"fontSize": "64px", "fontWeight": "600", "color": "#1a1a2e", "letterSpacing": "0.5px"},
        "y": 65,
    },
    "subtitle": {
        "text": "30 trading days with 5-day moving average \u2014 Oct\u2013Nov 2024",
        "style": {"fontSize": "38px", "color": "#666680", "fontWeight": "300"},
        "y": 115,
    },
    "xAxis": {
        "type": "datetime",
        "title": {"text": "Date", "style": {"fontSize": "44px", "color": "#444460", "fontWeight": "500"}, "margin": 25},
        "labels": {"style": {"fontSize": "34px", "color": "#666680"}, "format": "{value:%b %d}", "y": 40, "step": 2},
        "gridLineWidth": 0,
        "lineWidth": 0,
        "tickWidth": 0,
        "crosshair": {"width": 2, "color": "rgba(100, 100, 120, 0.3)", "dashStyle": "Dash"},
    },
    "yAxis": {
        "title": {
            "text": "Price (USD)",
            "style": {"fontSize": "44px", "color": "#444460", "fontWeight": "500"},
            "margin": 25,
        },
        "labels": {"style": {"fontSize": "34px", "color": "#666680"}, "format": "${value:.0f}", "x": -15},
        "gridLineWidth": 1,
        "gridLineColor": "rgba(100, 100, 120, 0.12)",
        "gridLineDashStyle": "Dot",
        "lineWidth": 0,
        "opposite": False,
        "tickWidth": 0,
        "tickInterval": 2,
        "plotBands": [
            {
                "from": trough_price - 0.5,
                "to": trough_price + 0.5,
                "color": "rgba(230, 126, 34, 0.08)",
                "label": {
                    "text": f"Trough: ${trough_price:.2f}",
                    "align": "right",
                    "x": -20,
                    "style": {"fontSize": "28px", "color": "#D35400", "fontStyle": "italic", "fontWeight": "500"},
                },
            }
        ],
    },
    "legend": {
        "enabled": True,
        "align": "right",
        "verticalAlign": "top",
        "layout": "horizontal",
        "x": -60,
        "y": 60,
        "floating": True,
        "itemStyle": {"fontSize": "30px", "fontWeight": "400", "color": "#444460"},
        "symbolWidth": 40,
        "symbolRadius": 0,
    },
    "tooltip": {
        "split": False,
        "style": {"fontSize": "28px"},
        "headerFormat": "<b>{point.x:%b %d, %Y}</b><br/>",
        "shared": True,
        "backgroundColor": "rgba(255, 255, 255, 0.96)",
        "borderColor": "#ccc",
        "borderRadius": 8,
        "shadow": True,
    },
    "plotOptions": {
        "candlestick": {
            "color": "#E67E22",
            "upColor": "#306998",
            "lineColor": "#D35400",
            "upLineColor": "#1A3A5C",
            "lineWidth": 4,
            "pointWidth": 70,
            "tooltip": {
                "pointFormat": "Open: ${point.open:.2f}<br/>"
                + "High: ${point.high:.2f}<br/>"
                + "Low: ${point.low:.2f}<br/>"
                + "Close: ${point.close:.2f}"
            },
        },
        "line": {"tooltip": {"pointFormat": "SMA(5): <b>${point.y:.2f}</b>"}},
    },
    "rangeSelector": {"enabled": False},
    "navigator": {"enabled": False},
    "scrollbar": {"enabled": False},
    "credits": {"enabled": False},
    "series": [
        {"type": "candlestick", "name": "OHLC", "data": ohlc_data, "zIndex": 1},
        {
            "type": "line",
            "name": "5-day SMA",
            "data": sma_data,
            "color": "#8E44AD",
            "lineWidth": 5,
            "marker": {"enabled": False},
            "dashStyle": "ShortDash",
            "zIndex": 2,
            "enableMouseTracking": True,
        },
    ],
}

# Download Highstock JS (includes candlestick support)
highstock_url = "https://code.highcharts.com/stock/highstock.js"
with urllib.request.urlopen(highstock_url, timeout=30) as response:
    highstock_js = response.read().decode("utf-8")

chart_options_json = json.dumps(chart_options)

# Render
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highstock_js}</script>
</head>
<body style="margin:0; background-color: #FAFBFC;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            Highcharts.stockChart('container', {chart_options_json});
        }});
    </script>
</body>
</html>"""

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
