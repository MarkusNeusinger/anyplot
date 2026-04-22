""" pyplots.ai
line-multi: Multi-Line Comparison Plot
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-24
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


# Data - Monthly sales for 4 product lines over 12 months
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Electronics - steady growth with seasonal dip
electronics = [120, 135, 142, 138, 155, 165, 158, 172, 185, 210, 245, 280]

# Clothing - seasonal pattern with summer and winter peaks
clothing = [95, 88, 82, 78, 92, 115, 125, 118, 95, 88, 110, 145]

# Home & Garden - spring/summer peak
home_garden = [65, 72, 95, 125, 145, 155, 148, 135, 110, 85, 70, 68]

# Sports Equipment - gradual increase
sports = [45, 48, 55, 68, 85, 92, 105, 98, 88, 75, 65, 58]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for 4800x2700 px
chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "style": {"fontFamily": "Arial, sans-serif"},
    "spacingBottom": 100,
    "spacingTop": 50,
}

# Title
chart.options.title = {
    "text": "line-multi · highcharts · pyplots.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold"},
}

# Subtitle
chart.options.subtitle = {"text": "Monthly Sales by Product Category (thousands USD)", "style": {"fontSize": "48px"}}

# X-axis configuration
chart.options.x_axis = {
    "categories": months,
    "title": {"text": "Month", "style": {"fontSize": "48px"}},
    "labels": {"style": {"fontSize": "36px"}},
    "lineWidth": 2,
    "tickWidth": 2,
}

# Y-axis configuration
chart.options.y_axis = {
    "title": {"text": "Sales (thousands USD)", "style": {"fontSize": "48px"}},
    "labels": {"style": {"fontSize": "36px"}},
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "min": 0,
}

# Legend configuration - position at top right
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "42px"},
    "layout": "vertical",
    "align": "right",
    "verticalAlign": "top",
    "x": -50,
    "y": 150,
    "borderWidth": 1,
    "borderColor": "#e0e0e0",
    "backgroundColor": "#ffffff",
    "padding": 20,
    "itemMarginTop": 10,
    "itemMarginBottom": 10,
}

# Plot options for line styling
chart.options.plot_options = {
    "line": {"lineWidth": 6, "marker": {"enabled": True, "radius": 12, "lineWidth": 3, "lineColor": "#ffffff"}}
}

# Colorblind-safe colors
colors = ["#306998", "#FFD43B", "#9467BD", "#17BECF"]

# Add series - Electronics
series1 = LineSeries()
series1.name = "Electronics"
series1.data = electronics
series1.color = colors[0]
series1.marker = {"symbol": "circle"}
chart.add_series(series1)

# Add series - Clothing
series2 = LineSeries()
series2.name = "Clothing"
series2.data = clothing
series2.color = colors[1]
series2.marker = {"symbol": "square"}
chart.add_series(series2)

# Add series - Home & Garden
series3 = LineSeries()
series3.name = "Home & Garden"
series3.data = home_garden
series3.color = colors[2]
series3.marker = {"symbol": "triangle"}
chart.add_series(series3)

# Add series - Sports Equipment
series4 = LineSeries()
series4.name = "Sports Equipment"
series4.data = sports
series4.color = colors[3]
series4.marker = {"symbol": "diamond"}
chart.add_series(series4)

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

# Save HTML version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Create PNG via headless Chrome
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
driver.set_window_size(4800, 2700)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
