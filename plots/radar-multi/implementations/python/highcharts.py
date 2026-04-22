""" pyplots.ai
radar-multi: Multi-Series Radar Chart
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
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


# Data - Product comparison across key attributes (4 products, 6 attributes)
categories = ["Price", "Quality", "Durability", "Support", "Features", "Ease of Use"]

# Product A: Premium option - high quality but expensive
product_a = [35, 95, 90, 85, 80, 70]
# Product B: Budget option - low price but basic
product_b = [95, 55, 50, 60, 45, 85]
# Product C: Balanced option - moderate across all
product_c = [65, 75, 70, 75, 70, 75]
# Product D: Feature-rich but complex
product_d = [50, 80, 75, 70, 95, 45]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for polar/radar - using square format for symmetric visualization
chart.options.chart = {"polar": True, "width": 3600, "height": 3600, "backgroundColor": "#ffffff"}

# Title
chart.options.title = {
    "text": "Product Comparison · radar-multi · highcharts · pyplots.ai",
    "style": {"fontSize": "64px", "fontWeight": "bold"},
}

# X-axis (categories around the radar)
chart.options.x_axis = {
    "categories": categories,
    "tickmarkPlacement": "on",
    "lineWidth": 0,
    "labels": {"style": {"fontSize": "40px"}, "distance": 30},
}

# Y-axis (radial axis)
chart.options.y_axis = {
    "gridLineInterpolation": "polygon",
    "lineWidth": 0,
    "min": 0,
    "max": 100,
    "tickInterval": 20,
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 2,
    "gridLineColor": "rgba(0, 0, 0, 0.15)",
}

# Pane settings for radar
chart.options.pane = {"size": "70%"}

# Plot options for area series on polar chart
chart.options.plot_options = {
    "series": {"pointPlacement": "on"},
    "area": {"fillOpacity": 0.25, "lineWidth": 4, "marker": {"enabled": True, "radius": 10}},
}

# Legend configuration
chart.options.legend = {
    "enabled": True,
    "align": "center",
    "verticalAlign": "bottom",
    "layout": "horizontal",
    "itemStyle": {"fontSize": "36px"},
    "symbolWidth": 40,
    "symbolHeight": 20,
}

# Credits
chart.options.credits = {"enabled": False}

# Colorblind-safe color palette
colors = ["#306998", "#FFD43B", "#9467BD", "#17BECF"]

# Add series for Product A (Python Blue)
series1 = AreaSeries()
series1.data = product_a
series1.name = "Product A (Premium)"
series1.color = colors[0]
series1.fill_opacity = 0.2
chart.add_series(series1)

# Add series for Product B (Python Yellow)
series2 = AreaSeries()
series2.data = product_b
series2.name = "Product B (Budget)"
series2.color = colors[1]
series2.fill_opacity = 0.2
chart.add_series(series2)

# Add series for Product C (Purple)
series3 = AreaSeries()
series3.data = product_c
series3.name = "Product C (Balanced)"
series3.color = colors[2]
series3.fill_opacity = 0.2
chart.add_series(series3)

# Add series for Product D (Cyan)
series4 = AreaSeries()
series4.data = product_d
series4.name = "Product D (Feature-Rich)"
series4.color = colors[3]
series4.fill_opacity = 0.2
chart.add_series(series4)

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
chrome_options.add_argument("--window-size=4000,4000")

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
