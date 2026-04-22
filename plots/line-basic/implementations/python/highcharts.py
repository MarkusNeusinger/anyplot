""" pyplots.ai
line-basic: Basic Line Plot
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
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


# Data - Monthly temperature readings showing seasonal pattern
np.random.seed(42)
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
# Realistic temperature pattern: cold winter, warm summer
temperatures = [5, 7, 12, 16, 21, 25, 28, 27, 22, 15, 9, 6]
# Add slight natural variation
temperatures = [t + np.random.randn() * 0.5 for t in temperatures]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart settings for 4800x2700 canvas
chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 300,
    "marginLeft": 200,
    "spacingTop": 80,
}

# Title
chart.options.title = {
    "text": "line-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold"},
}

# X-axis
chart.options.x_axis = {
    "categories": month_labels,
    "title": {"text": "Month", "style": {"fontSize": "48px"}, "margin": 30},
    "labels": {"style": {"fontSize": "36px"}, "y": 40},
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "lineWidth": 2,
    "tickWidth": 2,
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Temperature (°C)", "style": {"fontSize": "48px"}, "margin": 30},
    "labels": {"style": {"fontSize": "36px"}, "x": -10},
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "gridLineDashStyle": "Dash",
}

# Legend
chart.options.legend = {"enabled": True, "itemStyle": {"fontSize": "36px"}}

# Plot options for line styling
chart.options.plot_options = {"line": {"lineWidth": 8, "marker": {"enabled": True, "radius": 12, "symbol": "circle"}}}

# Add series
series = LineSeries()
series.data = temperatures
series.name = "Temperature"
series.color = "#306998"

chart.add_series(series)

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

# Also save HTML for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

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
