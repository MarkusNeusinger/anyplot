""" pyplots.ai
radar-basic: Basic Radar Chart
Library: highcharts unknown | Python 3.13.11
Quality: 99/100 | Created: 2025-12-23
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Employee performance metrics comparison (two employees)
categories = ["Communication", "Technical Skills", "Teamwork", "Problem Solving", "Leadership", "Creativity"]

# Employee 1: Strong technical, moderate soft skills
employee1_values = [70, 95, 75, 90, 65, 80]
# Employee 2: Strong soft skills, moderate technical
employee2_values = [90, 70, 95, 75, 85, 70]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for polar/radar
chart.options.chart = {"polar": True, "width": 4800, "height": 2700, "backgroundColor": "#ffffff"}

# Title
chart.options.title = {
    "text": "radar-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold"},
}

# X-axis (categories around the radar)
chart.options.x_axis = {
    "categories": categories,
    "tickmarkPlacement": "on",
    "lineWidth": 0,
    "labels": {"style": {"fontSize": "40px"}},
}

# Y-axis (radial axis)
chart.options.y_axis = {
    "gridLineInterpolation": "polygon",
    "lineWidth": 0,
    "min": 0,
    "max": 100,
    "tickInterval": 20,
    "labels": {"style": {"fontSize": "32px"}},
    "gridLineWidth": 2,
    "gridLineColor": "rgba(0, 0, 0, 0.15)",
}

# Pane settings for radar
chart.options.pane = {"size": "75%"}

# Plot options for area series on polar chart
chart.options.plot_options = {
    "series": {"pointPlacement": "on"},
    "area": {"fillOpacity": 0.25, "lineWidth": 4, "marker": {"enabled": True, "radius": 12}},
}

# Legend configuration
chart.options.legend = {
    "enabled": True,
    "align": "center",
    "verticalAlign": "bottom",
    "layout": "horizontal",
    "itemStyle": {"fontSize": "36px"},
}

# Credits
chart.options.credits = {"enabled": False}

# Add series for Employee 1 (Python Blue)
series1 = AreaSeries()
series1.data = employee1_values
series1.name = "Employee A"
series1.color = "#306998"
series1.fill_opacity = 0.25
chart.add_series(series1)

# Add series for Employee 2 (Python Yellow)
series2 = AreaSeries()
series2.data = employee2_values
series2.name = "Employee B"
series2.color = "#FFD43B"
series2.fill_opacity = 0.25
chart.add_series(series2)

# Download Highcharts JS and highcharts-more.js (required for polar/radar charts)
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
