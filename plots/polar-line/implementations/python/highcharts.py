""" pyplots.ai
polar-line: Polar Line Plot
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Monthly temperature pattern (cyclical, degrees around year)
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
# Simulating monthly average temperatures for two cities
city_a = [2, 4, 9, 14, 19, 23, 26, 25, 20, 14, 8, 3]  # Continental climate
city_b = [8, 9, 11, 13, 16, 19, 21, 21, 19, 15, 11, 9]  # Oceanic climate

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for polar line
chart.options.chart = {"polar": True, "width": 3600, "height": 3600, "backgroundColor": "#ffffff", "spacingBottom": 120}

# Title
chart.options.title = {
    "text": "polar-line · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

chart.options.subtitle = {"text": "Monthly Average Temperature Patterns", "style": {"fontSize": "32px"}}

# X-axis (angular axis - categories)
chart.options.x_axis = {
    "categories": months,
    "tickmarkPlacement": "on",
    "lineWidth": 0,
    "labels": {"style": {"fontSize": "28px"}},
}

# Y-axis (radial axis)
chart.options.y_axis = {
    "gridLineInterpolation": "polygon",
    "lineWidth": 0,
    "min": 0,
    "max": 30,
    "title": {"text": "Temperature (°C)", "style": {"fontSize": "24px"}},
    "labels": {"style": {"fontSize": "20px"}},
}

# Plot options for line series
chart.options.plot_options = {"series": {"lineWidth": 5, "marker": {"enabled": True, "radius": 10}}}

# Legend
chart.options.legend = {
    "enabled": True,
    "align": "center",
    "verticalAlign": "bottom",
    "layout": "horizontal",
    "itemStyle": {"fontSize": "32px"},
    "symbolRadius": 6,
    "itemMarginTop": 20,
}

# Add series data
chart.options.series = [
    {"type": "line", "name": "Continental City", "data": city_a, "color": "#306998", "marker": {"symbol": "circle"}},
    {"type": "line", "name": "Oceanic City", "data": city_b, "color": "#FFD43B", "marker": {"symbol": "diamond"}},
]

# Download Highcharts JS and Highcharts More for polar charts
highcharts_url = "https://code.highcharts.com/highcharts.js"
highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

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
<body style="margin:0; background-color: #ffffff;">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
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
chrome_options.add_argument("--window-size=3600,3800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
# Take screenshot of the container element for exact dimensions
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

Path(temp_path).unlink()
