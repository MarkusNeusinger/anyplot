""" pyplots.ai
drawdown-basic: Drawdown Chart
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Generate simulated stock price data
np.random.seed(42)
n_days = 500
dates = pd.date_range("2022-01-01", periods=n_days, freq="B")

# Simulate price with drift and volatility (geometric Brownian motion-like)
returns = np.random.normal(0.0003, 0.015, n_days)
prices = 100 * np.cumprod(1 + returns)

# Calculate drawdown
running_max = np.maximum.accumulate(prices)
drawdown = (prices - running_max) / running_max * 100  # Percentage drawdown (negative values)

# Find maximum drawdown
max_dd_idx = np.argmin(drawdown)
max_dd_value = drawdown[max_dd_idx]
max_dd_date = dates[max_dd_idx]

# Find recovery point (if any)
recovery_indices = np.where(drawdown[max_dd_idx:] == 0)[0]
if len(recovery_indices) > 0:
    recovery_idx = max_dd_idx + recovery_indices[0]
    recovery_date = dates[recovery_idx]
    recovery_days = (recovery_date - max_dd_date).days
else:
    recovery_days = None

# Prepare data for Highcharts (timestamp in ms, value)
data_points = [[int(d.timestamp() * 1000), round(float(dd), 2)] for d, dd in zip(dates, drawdown, strict=True)]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "area",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "spacingTop": 60,
    "spacingBottom": 100,
    "spacingLeft": 80,
    "spacingRight": 80,
}

# Title with stats
max_dd_str = f"Max Drawdown: {max_dd_value:.1f}%"
if recovery_days:
    stats_str = f"{max_dd_str} | Recovery: {recovery_days} days"
else:
    stats_str = f"{max_dd_str} | Not Recovered"

chart.options.title = {
    "text": "drawdown-basic \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "56px", "fontWeight": "bold"},
    "margin": 40,
}

chart.options.subtitle = {"text": stats_str, "style": {"fontSize": "36px", "color": "#666666"}}

# X-axis (datetime)
chart.options.x_axis = {
    "type": "datetime",
    "title": {"text": "Date", "style": {"fontSize": "36px"}, "margin": 25},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
    "tickInterval": 90 * 24 * 3600 * 1000,  # Quarterly ticks
    "dateTimeLabelFormats": {"month": "%b %Y"},
}

# Y-axis (percentage)
chart.options.y_axis = {
    "title": {"text": "Drawdown (%)", "style": {"fontSize": "36px"}, "margin": 25},
    "labels": {"style": {"fontSize": "28px"}, "format": "{value}%"},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
    "max": 5,
    "plotLines": [
        {
            "value": 0,
            "color": "#306998",
            "width": 4,
            "zIndex": 5,
            "label": {
                "text": "Peak (0%)",
                "style": {"fontSize": "24px", "color": "#306998", "fontWeight": "bold"},
                "align": "right",
                "x": -10,
            },
        }
    ],
}

# Legend
chart.options.legend = {"enabled": True, "itemStyle": {"fontSize": "32px"}, "margin": 30}

# Tooltip
chart.options.tooltip = {"xDateFormat": "%A, %b %d, %Y", "valueSuffix": "%", "style": {"fontSize": "28px"}}

# Plot options - area fills from line to threshold (0)
chart.options.plot_options = {"area": {"lineWidth": 4, "marker": {"enabled": False}, "threshold": 0}}

# Credits
chart.options.credits = {"enabled": False}

# Build series data directly with fill configuration
chart.options.series = [
    {
        "name": "Drawdown",
        "type": "area",
        "data": data_points,
        "color": "#DC2626",
        "fillColor": {
            "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
            "stops": [[0, "rgba(220, 38, 38, 0.1)"], [1, "rgba(220, 38, 38, 0.5)"]],
        },
        "lineColor": "#DC2626",
        "lineWidth": 4,
        "threshold": 0,
        "negativeFillColor": {
            "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
            "stops": [[0, "rgba(220, 38, 38, 0.1)"], [1, "rgba(220, 38, 38, 0.5)"]],
        },
    }
]

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

# Save HTML version with CDN for interactive use
with open("plot.html", "w", encoding="utf-8") as f:
    cdn_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 600px;"></div>
    <script>{html_str}</script>
</body>
</html>"""
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
