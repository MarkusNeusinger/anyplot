""" pyplots.ai
indicator-ema: Exponential Moving Average (EMA) Indicator Chart
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Generate realistic stock price data
np.random.seed(42)
n_days = 120

# Start with a base price and generate realistic daily returns
base_price = 150.0
daily_returns = np.random.normal(0.001, 0.02, n_days)  # Small positive drift with volatility

# Generate price series with cumulative returns
prices = [base_price]
for ret in daily_returns[1:]:
    prices.append(prices[-1] * (1 + ret))
prices = np.array(prices)

# Create date range (trading days)
dates = pd.date_range(start="2024-06-01", periods=n_days, freq="B")


# Calculate EMAs
def calc_ema(prices, span):
    """Calculate exponential moving average."""
    ema = np.zeros(len(prices))
    multiplier = 2 / (span + 1)
    ema[0] = prices[0]
    for i in range(1, len(prices)):
        ema[i] = prices[i] * multiplier + ema[i - 1] * (1 - multiplier)
    return ema


ema_12 = calc_ema(prices, 12)
ema_26 = calc_ema(prices, 26)

# Convert dates to timestamps for Highcharts
timestamps = [int(d.timestamp() * 1000) for d in dates]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "spacingTop": 60,
    "spacingBottom": 100,
    "spacingLeft": 80,
    "spacingRight": 80,
}

# Title
chart.options.title = {
    "text": "indicator-ema · highcharts · pyplots.ai",
    "style": {"fontSize": "56px", "fontWeight": "bold"},
    "margin": 40,
}

# Subtitle
chart.options.subtitle = {
    "text": "Stock Price with 12-day and 26-day EMAs",
    "style": {"fontSize": "36px", "color": "#666666"},
}

# X-axis configuration (datetime)
chart.options.x_axis = {
    "type": "datetime",
    "title": {"text": "Date", "style": {"fontSize": "36px"}, "margin": 25},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
    "tickInterval": 30 * 24 * 3600 * 1000,  # Monthly ticks
    "dateTimeLabelFormats": {"month": "%b %Y"},
}

# Y-axis configuration
chart.options.y_axis = {
    "title": {"text": "Price (USD)", "style": {"fontSize": "36px"}, "margin": 25},
    "labels": {"style": {"fontSize": "28px"}, "format": "${value:.0f}"},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
}

# Legend
chart.options.legend = {"enabled": True, "itemStyle": {"fontSize": "32px"}, "margin": 30}

# Tooltip
chart.options.tooltip = {
    "shared": True,
    "crosshairs": True,
    "style": {"fontSize": "28px"},
    "valueDecimals": 2,
    "valuePrefix": "$",
    "xDateFormat": "%b %d, %Y",
}

# Plot options
chart.options.plot_options = {
    "line": {"lineWidth": 5, "marker": {"enabled": False}, "states": {"hover": {"lineWidth": 6}}}
}

# Price series (prominent)
price_series = LineSeries()
price_series.name = "Close Price"
price_series.data = [[t, round(p, 2)] for t, p in zip(timestamps, prices, strict=True)]
price_series.color = "#306998"  # Python Blue
price_series.line_width = 5
price_series.z_index = 3
chart.add_series(price_series)

# EMA 12 series
ema12_series = LineSeries()
ema12_series.name = "EMA 12"
ema12_series.data = [[t, round(e, 2)] for t, e in zip(timestamps, ema_12, strict=True)]
ema12_series.color = "#FFD43B"  # Python Yellow
ema12_series.line_width = 3
ema12_series.dash_style = "Solid"
ema12_series.z_index = 2
chart.add_series(ema12_series)

# EMA 26 series
ema26_series = LineSeries()
ema26_series.name = "EMA 26"
ema26_series.data = [[t, round(e, 2)] for t, e in zip(timestamps, ema_26, strict=True)]
ema26_series.color = "#9467BD"  # Purple
ema26_series.line_width = 3
ema26_series.dash_style = "ShortDash"
ema26_series.z_index = 1
chart.add_series(ema26_series)

# Download Highcharts JS for inline embedding
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=5000,3000")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

# Screenshot the chart container element for exact dimensions
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()

# Save HTML for interactive version (using CDN for portability)
interactive_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>indicator-ema · highcharts · pyplots.ai</title>
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(interactive_html)
