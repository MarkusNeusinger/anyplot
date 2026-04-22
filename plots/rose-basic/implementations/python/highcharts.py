""" pyplots.ai
rose-basic: Basic Rose Chart
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import ColumnSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Monthly rainfall in mm (showing natural 12-month cycle)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
rainfall = [78, 52, 65, 45, 38, 25, 18, 22, 42, 68, 85, 92]

# Create chart with polar/rose configuration
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for polar column (rose chart)
chart.options.chart = {"polar": True, "type": "column", "width": 4800, "height": 2700, "backgroundColor": "#ffffff"}

# Title
chart.options.title = {
    "text": "rose-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle for context
chart.options.subtitle = {"text": "Monthly Rainfall (mm)", "style": {"fontSize": "32px"}}

# X-axis (categories around the circle)
chart.options.x_axis = {
    "categories": months,
    "tickmarkPlacement": "on",
    "lineWidth": 0,
    "labels": {"style": {"fontSize": "28px"}},
}

# Y-axis (radial - values extend from center)
chart.options.y_axis = {
    "min": 0,
    "gridLineInterpolation": "polygon",
    "lineWidth": 0,
    "labels": {"style": {"fontSize": "24px"}},
    "title": {"text": "Rainfall (mm)", "style": {"fontSize": "28px"}},
}

# Plot options for the rose/polar column
chart.options.plot_options = {
    "column": {"pointPadding": 0, "groupPadding": 0, "borderWidth": 2, "borderColor": "#ffffff"},
    "series": {"dataLabels": {"enabled": True, "format": "{y}", "style": {"fontSize": "20px", "fontWeight": "normal"}}},
}

# Pane configuration for polar chart
chart.options.pane = {"size": "85%", "startAngle": -15}

# Legend configuration
chart.options.legend = {"enabled": True, "itemStyle": {"fontSize": "28px"}}

# Create series with Python Blue color
series = ColumnSeries()
series.name = "Rainfall"
series.data = rainfall
series.color = "#306998"

chart.add_series(series)

# Download Highcharts JS and Highcharts More (for polar charts)
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
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with headless Chrome
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

# Clean up temp file
Path(temp_path).unlink()
