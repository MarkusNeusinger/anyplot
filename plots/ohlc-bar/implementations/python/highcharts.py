""" anyplot.ai
ohlc-bar: OHLC Bar Chart
Library: highcharts unknown | Python 3.13.13
Quality: 22/100 | Updated: 2026-05-23
"""

import json
import os
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette - first series is #009E73 (brand green)
UP_COLOR = "#009E73"  # Green for up bars (close > open)
DOWN_COLOR = "#D55E00"  # Orange for down bars (close < open)

# Data - 50 trading days of simulated stock prices
np.random.seed(42)

# Start price and generate OHLC data
start_price = 150.0
n_days = 50

# Generate realistic stock movements
opens = [start_price]
highs = []
lows = []
closes = []

for i in range(n_days):
    open_price = opens[i] if i == 0 else closes[i - 1] + np.random.randn() * 0.3
    if i > 0:
        opens.append(open_price)

    # Daily volatility
    daily_range = abs(np.random.randn() * 2) + 0.5
    direction = np.random.choice([-1, 1], p=[0.48, 0.52])  # Slight bullish bias

    close_price = open_price + direction * np.random.rand() * daily_range
    high_price = max(open_price, close_price) + abs(np.random.randn() * 0.8)
    low_price = min(open_price, close_price) - abs(np.random.randn() * 0.8)

    highs.append(round(high_price, 2))
    lows.append(round(low_price, 2))
    closes.append(round(close_price, 2))

opens = [round(o, 2) for o in opens]

# Generate dates (trading days, skip weekends)
start_date = datetime(2024, 6, 1)
dates = []
current_date = start_date
while len(dates) < n_days:
    if current_date.weekday() < 5:  # Monday to Friday
        dates.append(current_date)
    current_date += timedelta(days=1)

# Format data for Highcharts: [timestamp, open, high, low, close]
ohlc_data = []
for i in range(n_days):
    timestamp = int(dates[i].timestamp() * 1000)  # JavaScript timestamp in ms
    ohlc_data.append([timestamp, opens[i], highs[i], lows[i], closes[i]])

# Chart options for Highcharts Stock OHLC chart
chart_options = {
    "chart": {
        "type": "ohlc",
        "width": 4800,
        "height": 2700,
        "backgroundColor": PAGE_BG,
        "marginBottom": 220,
        "marginLeft": 250,
        "marginRight": 80,
        "marginTop": 150,
        "style": {"fontFamily": "Arial, sans-serif", "color": INK},
    },
    "title": {
        "text": "ohlc-bar · highcharts · anyplot.ai",
        "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK},
        "y": 20,
    },
    "xAxis": {
        "type": "datetime",
        "title": {"text": "Date", "style": {"fontSize": "22px", "color": INK}, "margin": 20},
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}, "format": "{value:%b %d}", "y": 10, "step": 3},
        "gridLineWidth": 1,
        "gridLineColor": GRID,
        "lineWidth": 2,
        "lineColor": INK_SOFT,
        "tickWidth": 2,
        "tickColor": INK_SOFT,
        "tickLength": 10,
    },
    "yAxis": {
        "title": {"text": "Price (USD)", "style": {"fontSize": "22px", "color": INK}, "margin": 20},
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}, "format": "${value:.0f}", "x": -10},
        "gridLineWidth": 1,
        "gridLineColor": GRID,
        "lineWidth": 2,
        "lineColor": INK_SOFT,
        "opposite": False,
    },
    "legend": {"enabled": False},
    "tooltip": {
        "split": False,
        "style": {"fontSize": "16px", "color": INK},
        "backgroundColor": ELEVATED_BG,
        "borderColor": INK_SOFT,
        "borderWidth": 1,
        "headerFormat": "<b>{point.x:%b %d, %Y}</b><br/>",
        "pointFormat": "Open: ${point.open:.2f}<br/>"
        + "High: ${point.high:.2f}<br/>"
        + "Low: ${point.low:.2f}<br/>"
        + "Close: ${point.close:.2f}",
    },
    "plotOptions": {"ohlc": {"color": DOWN_COLOR, "upColor": UP_COLOR, "lineWidth": 3}},
    "rangeSelector": {"enabled": False},
    "navigator": {"enabled": False},
    "scrollbar": {"enabled": False},
    "credits": {"enabled": False},
    "series": [{"type": "ohlc", "name": "Stock Price", "data": ohlc_data}],
}

# Download Highcharts JS (try primary CDN, then fallback)
urls_to_try = [
    "https://code.highcharts.com/highcharts.js",
    "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.3.0/highcharts.js",
]

highstock_js = None
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})

for url in urls_to_try:
    try:
        response = session.get(url, timeout=15)
        response.raise_for_status()
        highstock_js = response.text
        break
    except Exception as e:
        print(f"Warning: Could not download from {url}: {e}")

if highstock_js is None:
    print("Warning: Could not download Highcharts JS from any CDN. Using minimal fallback.")
    highstock_js = "window.Highcharts = {};"

# Generate chart options JSON
chart_options_json = json.dumps(chart_options)

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highstock_js}</script>
</head>
<body style="margin:0; background-color: {PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            Highcharts.stockChart('container', {chart_options_json});
        }});
    </script>
</body>
</html>"""

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save the HTML artifact for the site (theme-suffixed)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with headless Chrome
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

# Clean up temp file
Path(temp_path).unlink()
