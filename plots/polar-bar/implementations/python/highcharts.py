""" pyplots.ai
polar-bar: Polar Bar Chart (Wind Rose)
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


# Data - Wind direction frequency by speed category
np.random.seed(42)

# 8 compass directions
directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

# Wind speed categories (frequency counts for each direction)
# Simulating realistic wind patterns - prevailing westerlies
calm = [3, 2, 2, 1, 2, 3, 5, 4]
light = [8, 5, 6, 3, 4, 7, 12, 10]  # 1-10 mph
moderate = [5, 3, 4, 2, 3, 8, 15, 8]  # 10-20 mph
strong = [2, 1, 2, 1, 1, 4, 8, 5]  # 20+ mph

# Download Highcharts JS modules
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "polar": True,
    "type": "column",
    "width": 3600,
    "height": 3800,
    "backgroundColor": "#ffffff",
    "marginBottom": 250,  # space for legend
}

# Title
chart.options.title = {
    "text": "polar-bar · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

chart.options.subtitle = {"text": "Wind Speed Distribution by Direction", "style": {"fontSize": "32px"}}

# Pane configuration for polar chart
chart.options.pane = {
    "size": "60%",
    "startAngle": 0,
    "endAngle": 360,
    "center": ["40%", "50%"],  # move chart left to make room for legend on right
}

# X axis (angular - directions)
chart.options.x_axis = {
    "categories": directions,
    "tickmarkPlacement": "on",
    "lineWidth": 0,
    "labels": {"style": {"fontSize": "36px", "fontWeight": "bold"}, "distance": 25},
}

# Y axis (radial - frequency)
chart.options.y_axis = {
    "min": 0,
    "endOnTick": False,
    "showLastLabel": True,
    "title": {"text": "Frequency (%)", "style": {"fontSize": "28px"}},
    "labels": {"style": {"fontSize": "24px"}},
    "reversedStacks": False,
    "gridLineColor": "#cccccc",
    "gridLineWidth": 1,
}

# Legend
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "middle",
    "layout": "vertical",
    "itemStyle": {"fontSize": "32px"},
    "symbolRadius": 0,
    "symbolHeight": 28,
    "symbolWidth": 40,
    "itemMarginBottom": 20,
    "x": -50,
}

# Plot options for stacked column
chart.options.plot_options = {
    "series": {"stacking": "normal", "shadow": False, "groupPadding": 0, "pointPlacement": "on"},
    "column": {"pointPadding": 0, "groupPadding": 0, "borderWidth": 2, "borderColor": "#ffffff"},
}

# Colors - colorblind safe palette
colors = ["#306998", "#FFD43B", "#9467BD", "#17BECF"]

# Add series (stacked from bottom to top)
series_data = [
    {"name": "Calm (<1 mph)", "data": calm, "color": colors[0]},
    {"name": "Light (1-10 mph)", "data": light, "color": colors[1]},
    {"name": "Moderate (10-20 mph)", "data": moderate, "color": colors[2]},
    {"name": "Strong (>20 mph)", "data": strong, "color": colors[3]},
]

chart.options.series = series_data

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; background:#ffffff;">
    <div id="container" style="width: 3600px; height: 3800px;"></div>
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
chrome_options.add_argument("--window-size=3600,3800")  # extra height for legend

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()

# Also save HTML for interactive version
html_export = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>polar-bar · highcharts · pyplots.ai</title>
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/highcharts-more.js"></script>
</head>
<body style="margin:0; background:#ffffff;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_export)
