""" pyplots.ai
polar-basic: Basic Polar Chart
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Hourly temperature readings (24-hour cycle)
np.random.seed(42)
hours = np.arange(0, 360, 15)  # 24 data points at 15-degree intervals (360/24=15)
# Temperature pattern: cooler at night (0°/midnight), warmer during day (180°/noon)
base_temp = 15 + 10 * np.sin(np.radians(hours - 90))  # Peak at 90° (6 AM shifted to noon)
temperatures = base_temp + np.random.randn(len(hours)) * 2  # Add some noise

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for polar scatter plot
chart.options.chart = {"polar": True, "width": 4800, "height": 2700, "backgroundColor": "#ffffff"}

# Title
chart.options.title = {
    "text": "polar-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold"},
}

# Subtitle for context
chart.options.subtitle = {"text": "24-Hour Temperature Pattern", "style": {"fontSize": "48px"}}

# X-axis (angular axis - hours around the clock)
chart.options.x_axis = {
    "tickInterval": 30,  # Every 30 degrees (every 2 hours)
    "min": 0,
    "max": 360,
    "labels": {"format": "{value}°", "style": {"fontSize": "36px"}},
    "gridLineWidth": 2,
    "gridLineColor": "rgba(0, 0, 0, 0.15)",
}

# Y-axis (radial axis - temperature)
chart.options.y_axis = {
    "min": 0,
    "max": 35,
    "tickInterval": 5,
    "labels": {"format": "{value}°C", "style": {"fontSize": "32px"}},
    "gridLineWidth": 2,
    "gridLineColor": "rgba(0, 0, 0, 0.15)",
    "title": {"text": "Temperature (°C)", "style": {"fontSize": "40px"}},
}

# Pane settings for polar chart
chart.options.pane = {"size": "70%", "startAngle": 0, "endAngle": 360}

# Plot options for scatter on polar
chart.options.plot_options = {
    "scatter": {"marker": {"enabled": True, "radius": 16, "symbol": "circle"}, "lineWidth": 3},
    "series": {"animation": False},
}

# Legend
chart.options.legend = {
    "enabled": True,
    "align": "center",
    "verticalAlign": "bottom",
    "layout": "horizontal",
    "itemStyle": {"fontSize": "36px"},
}

# Credits
chart.options.credits = {"enabled": False}

# Create scatter series with polar coordinates
series = ScatterSeries()
series.data = [[float(h), float(t)] for h, t in zip(hours, temperatures, strict=True)]
series.name = "Temperature"
series.color = "rgba(48, 105, 152, 0.8)"  # Python Blue with alpha
series.marker = {"radius": 16, "symbol": "circle"}

chart.add_series(series)

# Download Highcharts JS and highcharts-more.js (required for polar charts)
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
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
time.sleep(5)  # Wait for chart to render

# Take screenshot of just the chart container element
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file

# Also save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    interactive_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/highcharts-more.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(interactive_html)
