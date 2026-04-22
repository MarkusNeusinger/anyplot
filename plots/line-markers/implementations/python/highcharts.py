""" pyplots.ai
line-markers: Line Plot with Markers
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Monthly temperature readings at a weather station
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Temperature data for two locations (realistic seasonal patterns)
base_temp_1 = np.array([2, 4, 8, 12, 17, 21, 24, 23, 19, 13, 7, 3])
base_temp_2 = np.array([5, 7, 11, 15, 20, 24, 27, 26, 22, 16, 10, 6])

# Add slight variation
temp_station_a = base_temp_1 + np.random.uniform(-1, 1, 12)
temp_station_b = base_temp_2 + np.random.uniform(-1, 1, 12)

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 250,
    "marginLeft": 180,
    "spacingBottom": 50,
}

# Title
chart.options.title = {
    "text": "line-markers · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle
chart.options.subtitle = {"text": "Monthly Temperature Readings at Two Weather Stations", "style": {"fontSize": "32px"}}

# X-axis
chart.options.x_axis = {
    "categories": months,
    "title": {"text": "Month", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Temperature (°C)", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "32px"},
    "symbolRadius": 8,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 100,
}

# Plot options for line with markers
chart.options.plot_options = {
    "line": {"lineWidth": 5, "marker": {"enabled": True, "radius": 12, "lineWidth": 3, "lineColor": "#ffffff"}}
}

# Series 1 - Station A (Python Blue)
series_a = LineSeries()
series_a.name = "Station A (Coastal)"
series_a.data = [round(float(t), 1) for t in temp_station_a]
series_a.color = "#306998"
series_a.marker = {"symbol": "circle", "fillColor": "#306998", "radius": 14}

# Series 2 - Station B (Python Yellow)
series_b = LineSeries()
series_b.name = "Station B (Inland)"
series_b.data = [round(float(t), 1) for t in temp_station_b]
series_b.color = "#FFD43B"
series_b.marker = {"symbol": "diamond", "fillColor": "#FFD43B", "radius": 14}

chart.add_series(series_a)
chart.add_series(series_b)

# Download Highcharts JS
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
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()

# Also save interactive HTML version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)
