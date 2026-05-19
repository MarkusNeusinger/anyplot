"""anyplot.ai
indicator-sma: Simple Moving Average (SMA) Indicator Chart
Library: highcharts | Python 3.13
Quality: 91/100 | Created: 2026-01-11
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito colors (canonical order)
CLOSE_COLOR = "#009E73"  # position 1 — brand green — close price
SMA20_COLOR = "#D55E00"  # position 2 — vermillion — SMA 20
SMA50_COLOR = "#0072B2"  # position 3 — blue — SMA 50
SMA200_COLOR = "#CC79A7"  # position 4 — reddish purple — SMA 200

# Data: stock price with mean-reverting (Ornstein-Uhlenbeck) dynamics
np.random.seed(42)
n_days = 365
dates = pd.date_range(start="2024-01-02", periods=n_days, freq="B")

# Ornstein-Uhlenbeck mean-reverting process (differentiates from linear-trend peers)
theta = 0.008  # mean-reversion speed
mu = 175.0  # long-term mean
sigma = 0.015  # volatility
price = 150.0
prices = [price]
for _ in range(n_days - 1):
    drift = theta * (mu - prices[-1])
    noise = np.random.normal(0, sigma * prices[-1])
    prices.append(max(prices[-1] + drift + noise, 50.0))

close_prices = np.array(prices)

df = pd.DataFrame({"date": dates, "close": close_prices})
df["sma_20"] = df["close"].rolling(window=20).mean()
df["sma_50"] = df["close"].rolling(window=50).mean()
df["sma_200"] = df["close"].rolling(window=200).mean()

# Convert dates to milliseconds for Highcharts datetime axis
timestamps = [int(d.timestamp() * 1000) for d in df["date"]]

close_data = [[t, round(v, 2)] for t, v in zip(timestamps, df["close"], strict=True)]
sma20_data = [[t, round(v, 2)] for t, v in zip(timestamps, df["sma_20"], strict=True) if not np.isnan(v)]
sma50_data = [[t, round(v, 2)] for t, v in zip(timestamps, df["sma_50"], strict=True) if not np.isnan(v)]
sma200_data = [[t, round(v, 2)] for t, v in zip(timestamps, df["sma_200"], strict=True) if not np.isnan(v)]

# Chart options
chart_options = {
    "chart": {
        "type": "line",
        "width": 4800,
        "height": 2700,
        "backgroundColor": PAGE_BG,
        "marginBottom": 200,
        "marginLeft": 220,
        "marginRight": 100,
        "marginTop": 180,
        "style": {"fontFamily": "Arial, sans-serif"},
    },
    "title": {
        "text": "indicator-sma · python · highcharts · anyplot.ai",
        "style": {"fontSize": "64px", "fontWeight": "bold", "color": INK},
        "y": 70,
    },
    "subtitle": {
        "text": "Stock Price with 20, 50, and 200-day Simple Moving Averages",
        "style": {"fontSize": "36px", "color": INK_SOFT},
        "y": 130,
    },
    "xAxis": {
        "type": "datetime",
        "title": {"text": "Date", "style": {"fontSize": "40px", "color": INK}, "margin": 25},
        "labels": {"style": {"fontSize": "28px", "color": INK_SOFT}, "format": "{value:%b %Y}", "y": 35},
        "gridLineWidth": 1,
        "gridLineColor": GRID,
        "lineWidth": 2,
        "lineColor": INK_SOFT,
        "tickWidth": 2,
        "tickColor": INK_SOFT,
        "tickLength": 12,
    },
    "yAxis": {
        "title": {"text": "Price (USD)", "style": {"fontSize": "40px", "color": INK}, "margin": 25},
        "labels": {"style": {"fontSize": "28px", "color": INK_SOFT}, "format": "${value:.0f}", "x": -15},
        "gridLineWidth": 1,
        "gridLineColor": GRID,
        "lineWidth": 2,
        "lineColor": INK_SOFT,
    },
    "legend": {
        "enabled": True,
        "align": "right",
        "verticalAlign": "top",
        "layout": "vertical",
        "x": -60,
        "y": 120,
        "itemStyle": {"fontSize": "28px", "color": INK_SOFT},
        "itemMarginBottom": 15,
        "symbolWidth": 40,
        "symbolHeight": 18,
        "backgroundColor": ELEVATED_BG,
    },
    "tooltip": {
        "shared": True,
        "valueDecimals": 2,
        "valuePrefix": "$",
        "headerFormat": '<span style="font-size: 22px">{point.key:%b %d, %Y}</span><br/>',
        "style": {"fontSize": "22px"},
    },
    "plotOptions": {"line": {"lineWidth": 4, "marker": {"enabled": False}}, "series": {"animation": False}},
    "credits": {"enabled": False},
    "series": [
        {"name": "Close Price", "data": close_data, "color": CLOSE_COLOR, "lineWidth": 5, "zIndex": 4},
        {"name": "SMA 20", "data": sma20_data, "color": SMA20_COLOR, "lineWidth": 3, "dashStyle": "Solid", "zIndex": 3},
        {
            "name": "SMA 50",
            "data": sma50_data,
            "color": SMA50_COLOR,
            "lineWidth": 3,
            "dashStyle": "ShortDash",
            "zIndex": 2,
        },
        {
            "name": "SMA 200",
            "data": sma200_data,
            "color": SMA200_COLOR,
            "lineWidth": 3,
            "dashStyle": "LongDash",
            "zIndex": 1,
        },
    ],
}

# Download Highcharts JS from jsdelivr (inline embed required for headless Chrome)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@12/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=60) as response:
    highcharts_js = response.read().decode("utf-8")

chart_options_json = json.dumps(chart_options)

# Inline HTML for headless screenshot
inline_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background-color: {PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        Highcharts.chart('container', {chart_options_json});
    </script>
</body>
</html>"""

# CDN HTML for interactive artifact
cdn_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0; background-color: {PAGE_BG};">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>
        Highcharts.chart('container', {chart_options_json});
    </script>
</body>
</html>"""

# Save CDN HTML artifact for interactive viewing
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(cdn_html)

# Write temp inline HTML and screenshot for PNG artifact
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(inline_html)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
