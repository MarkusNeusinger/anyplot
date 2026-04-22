""" pyplots.ai
indicator-rsi: RSI Technical Indicator Chart
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2026-01-07
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


# Data - Generate synthetic stock prices and calculate RSI
np.random.seed(42)
n_periods = 120
dates = pd.date_range("2024-01-01", periods=n_periods, freq="D")

# Generate realistic price movements
price_changes = np.random.normal(0, 2, n_periods)
price_changes[20:35] = np.random.normal(1.5, 1.5, 15)  # Uptrend (will create overbought)
price_changes[50:65] = np.random.normal(-1.5, 1.5, 15)  # Downtrend (will create oversold)
price_changes[85:95] = np.random.normal(1.2, 1.2, 10)  # Another uptrend
prices = 100 + np.cumsum(price_changes)

# Calculate RSI (14-period)
delta = pd.Series(prices).diff()
gain = delta.where(delta > 0, 0)
loss = (-delta).where(delta < 0, 0)

avg_gain = gain.rolling(window=14, min_periods=14).mean()
avg_loss = loss.rolling(window=14, min_periods=14).mean()

rs = avg_gain / avg_loss
rsi = 100 - (100 / (1 + rs))
rsi = rsi.fillna(50)

# Prepare data for Highcharts (timestamps in milliseconds)
timestamps = [int(d.timestamp() * 1000) for d in dates]
rsi_data = list(zip(timestamps, rsi.tolist(), strict=True))

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart settings
chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "spacingTop": 60,
    "spacingBottom": 100,
    "spacingLeft": 80,
    "spacingRight": 120,
}

# Title
chart.options.title = {
    "text": "indicator-rsi · highcharts · pyplots.ai",
    "style": {"fontSize": "56px", "fontWeight": "bold"},
    "margin": 40,
}

chart.options.subtitle = {
    "text": "Relative Strength Index (14-period) · Synthetic Stock Data",
    "style": {"fontSize": "36px", "color": "#666666"},
}

# X-axis (datetime)
chart.options.x_axis = {
    "type": "datetime",
    "title": {"text": "Date", "style": {"fontSize": "36px"}, "margin": 25},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
    "tickInterval": 14 * 24 * 3600 * 1000,  # 2-week ticks
    "dateTimeLabelFormats": {"day": "%b %d"},
}

# Y-axis (0-100 fixed with plot lines and bands)
chart.options.y_axis = {
    "title": {"text": "RSI Value", "style": {"fontSize": "36px"}, "margin": 25},
    "labels": {"style": {"fontSize": "28px"}},
    "min": 0,
    "max": 100,
    "tickInterval": 10,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
    "plotLines": [
        {
            "value": 70,
            "color": "#D97706",
            "width": 4,
            "dashStyle": "Dash",
            "zIndex": 5,
            "label": {
                "text": "Overbought (70)",
                "align": "left",
                "style": {"fontSize": "28px", "color": "#D97706", "fontWeight": "bold"},
                "x": 10,
            },
        },
        {
            "value": 30,
            "color": "#2563EB",
            "width": 4,
            "dashStyle": "Dash",
            "zIndex": 5,
            "label": {
                "text": "Oversold (30)",
                "align": "left",
                "style": {"fontSize": "28px", "color": "#2563EB", "fontWeight": "bold"},
                "x": 10,
            },
        },
        {
            "value": 50,
            "color": "#6B7280",
            "width": 3,
            "dashStyle": "Dot",
            "zIndex": 5,
            "label": {
                "text": "Centerline (50)",
                "align": "left",
                "style": {"fontSize": "24px", "color": "#6B7280"},
                "x": 10,
            },
        },
    ],
    "plotBands": [
        {
            "from": 70,
            "to": 100,
            "color": "rgba(217, 119, 6, 0.15)",
            "label": {
                "text": "Overbought Zone",
                "style": {"fontSize": "24px", "color": "#B45309"},
                "align": "right",
                "x": -20,
                "y": 30,
            },
        },
        {
            "from": 0,
            "to": 30,
            "color": "rgba(37, 99, 235, 0.15)",
            "label": {
                "text": "Oversold Zone",
                "style": {"fontSize": "24px", "color": "#1D4ED8"},
                "align": "right",
                "x": -20,
                "y": -10,
            },
        },
    ],
}

# Legend
chart.options.legend = {"enabled": True, "itemStyle": {"fontSize": "32px"}, "margin": 30}

# Tooltip
chart.options.tooltip = {
    "xDateFormat": "%B %d, %Y",
    "valueSuffix": "",
    "style": {"fontSize": "28px"},
    "valueDecimals": 1,
}

# Plot options
chart.options.plot_options = {
    "line": {"lineWidth": 5, "marker": {"enabled": False}, "states": {"hover": {"lineWidth": 6}}}
}

# RSI Series
series = LineSeries()
series.name = "RSI (14)"
series.data = rsi_data
series.color = "#306998"

chart.add_series(series)

# Disable credits
chart.options.credits = {"enabled": False}

# Export to PNG via Selenium
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

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

# Save HTML version for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    cdn_html = (
        """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 600px;"></div>
    <script>"""
        + html_str
        + """</script>
</body>
</html>"""
    )
    f.write(cdn_html)

# Take screenshot with headless Chrome
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
