""" pyplots.ai
indicator-sma: Simple Moving Average (SMA) Indicator Chart
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Generate sample stock data (365 trading days)
np.random.seed(42)
n_days = 365
dates = pd.date_range(start="2024-01-02", periods=n_days, freq="B")  # Business days

# Generate realistic stock price movement using random walk
returns = np.random.normal(0.0005, 0.015, n_days)  # Daily returns
price_start = 150.0
close_prices = price_start * np.cumprod(1 + returns)

# Add some trend and volatility patterns
trend = np.linspace(0, 20, n_days)
close_prices = close_prices + trend

# Create DataFrame
df = pd.DataFrame({"date": dates, "close": close_prices})

# Calculate SMAs
df["sma_20"] = df["close"].rolling(window=20).mean()
df["sma_50"] = df["close"].rolling(window=50).mean()
df["sma_200"] = df["close"].rolling(window=200).mean()

# Convert dates to timestamps for Highcharts (milliseconds since epoch)
timestamps = [int(d.timestamp() * 1000) for d in df["date"]]

# Prepare data series (as [timestamp, value] pairs, handling NaN for initial periods)
close_data = [[t, round(v, 2)] for t, v in zip(timestamps, df["close"], strict=True)]
sma20_data = [[t, round(v, 2)] for t, v in zip(timestamps, df["sma_20"], strict=True) if not np.isnan(v)]
sma50_data = [[t, round(v, 2)] for t, v in zip(timestamps, df["sma_50"], strict=True) if not np.isnan(v)]
sma200_data = [[t, round(v, 2)] for t, v in zip(timestamps, df["sma_200"], strict=True) if not np.isnan(v)]

# Colors (colorblind-safe palette)
colors = {
    "close": "#306998",  # Python Blue - price line
    "sma20": "#FFD43B",  # Python Yellow - short-term
    "sma50": "#17BECF",  # Cyan - medium-term
    "sma200": "#9467BD",  # Purple - long-term
}

# Chart options for Highcharts
chart_options = {
    "chart": {
        "type": "line",
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "marginBottom": 200,
        "marginLeft": 220,
        "marginRight": 100,
        "marginTop": 180,
        "style": {"fontFamily": "Arial, sans-serif"},
    },
    "title": {
        "text": "indicator-sma · highcharts · pyplots.ai",
        "style": {"fontSize": "64px", "fontWeight": "bold", "color": "#333333"},
        "y": 70,
    },
    "subtitle": {
        "text": "Stock Price with 20, 50, and 200-day Simple Moving Averages",
        "style": {"fontSize": "36px", "color": "#666666"},
        "y": 130,
    },
    "xAxis": {
        "type": "datetime",
        "title": {"text": "Date", "style": {"fontSize": "40px", "color": "#333333"}, "margin": 25},
        "labels": {"style": {"fontSize": "28px", "color": "#333333"}, "format": "{value:%b %Y}", "y": 35},
        "gridLineWidth": 1,
        "gridLineColor": "rgba(0, 0, 0, 0.1)",
        "lineWidth": 2,
        "lineColor": "#333333",
        "tickWidth": 2,
        "tickColor": "#333333",
        "tickLength": 12,
    },
    "yAxis": {
        "title": {"text": "Price (USD)", "style": {"fontSize": "40px", "color": "#333333"}, "margin": 25},
        "labels": {"style": {"fontSize": "28px", "color": "#333333"}, "format": "${value:.0f}", "x": -15},
        "gridLineWidth": 1,
        "gridLineColor": "rgba(0, 0, 0, 0.1)",
        "lineWidth": 2,
        "lineColor": "#333333",
    },
    "legend": {
        "enabled": True,
        "align": "right",
        "verticalAlign": "top",
        "layout": "vertical",
        "x": -60,
        "y": 120,
        "itemStyle": {"fontSize": "28px", "color": "#333333"},
        "itemMarginBottom": 15,
        "symbolWidth": 40,
        "symbolHeight": 18,
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
        {"name": "Close Price", "data": close_data, "color": colors["close"], "lineWidth": 5, "zIndex": 4},
        {
            "name": "SMA 20",
            "data": sma20_data,
            "color": colors["sma20"],
            "lineWidth": 3,
            "dashStyle": "Solid",
            "zIndex": 3,
        },
        {
            "name": "SMA 50",
            "data": sma50_data,
            "color": colors["sma50"],
            "lineWidth": 3,
            "dashStyle": "ShortDash",
            "zIndex": 2,
        },
        {
            "name": "SMA 200",
            "data": sma200_data,
            "color": colors["sma200"],
            "lineWidth": 3,
            "dashStyle": "LongDash",
            "zIndex": 1,
        },
    ],
}

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate chart options JSON
chart_options_json = json.dumps(chart_options)

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background-color: #ffffff;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            Highcharts.chart('container', {chart_options_json});
        }});
    </script>
</body>
</html>"""

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save the HTML for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
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
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
