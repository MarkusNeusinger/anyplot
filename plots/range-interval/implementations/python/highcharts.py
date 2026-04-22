""" pyplots.ai
range-interval: Range Interval Chart
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import ColumnRangeSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Monthly temperature ranges for a temperate city
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Realistic temperature pattern (Northern Hemisphere temperate climate)
base_lows = [-2, -1, 3, 7, 12, 16, 18, 17, 13, 8, 3, -1]
base_highs = [5, 7, 12, 17, 22, 26, 29, 28, 23, 16, 10, 6]

# Add slight variation
min_temps = [low + np.random.uniform(-1, 1) for low in base_lows]
max_temps = [high + np.random.uniform(-1, 1) for high in base_highs]

# Create chart with container specified
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for 4800x2700 canvas
chart.options.chart = {
    "type": "columnrange",
    "inverted": False,
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 200,
    "marginLeft": 150,
    "style": {"fontFamily": "Arial, sans-serif"},
}

# Title
chart.options.title = {
    "text": "range-interval · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle for context
chart.options.subtitle = {"text": "Monthly Temperature Ranges (°C)", "style": {"fontSize": "32px"}}

# X-axis (categories)
chart.options.x_axis = {
    "categories": months,
    "title": {"text": "Month", "style": {"fontSize": "36px"}, "margin": 20},
    "labels": {"style": {"fontSize": "32px"}, "y": 40},
    "crosshair": True,
}

# Y-axis (temperature values)
chart.options.y_axis = {
    "title": {"text": "Temperature (°C)", "style": {"fontSize": "36px"}, "margin": 20},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
}

# Plot options for column range
chart.options.plot_options = {
    "columnrange": {
        "borderRadius": 3,
        "dataLabels": {
            "enabled": True,
            "format": "{y}°C",
            "style": {"fontSize": "18px", "fontWeight": "normal", "textOutline": "none"},
        },
    }
}

# Legend configuration
chart.options.legend = {"enabled": True, "itemStyle": {"fontSize": "24px"}, "verticalAlign": "top", "align": "right"}

# Tooltip configuration
chart.options.tooltip = {"valueSuffix": "°C", "style": {"fontSize": "20px"}}

# Create the column range series
series = ColumnRangeSeries()
series.name = "Temperature Range"
series.color = "#306998"  # Python Blue

# Data format for columnrange: [[low, high], [low, high], ...]
series.data = [[round(min_temps[i], 1), round(max_temps[i], 1)] for i in range(len(months))]

chart.add_series(series)

# Download Highcharts JS (required for headless Chrome)
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Download highcharts-more.js for columnrange support
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
chrome_options.add_argument("--window-size=4800,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file

# Also save HTML for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)
