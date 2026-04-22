""" pyplots.ai
bar-stacked-percent: 100% Stacked Bar Chart
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
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


# Data: Market share by quarter for different companies
categories = ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024", "Q1 2025"]
series_data = {
    "TechCorp": [35, 33, 30, 28, 26],
    "DataFlow": [25, 27, 28, 30, 32],
    "CloudPeak": [20, 21, 23, 24, 25],
    "NetBase": [12, 12, 12, 11, 10],
    "Others": [8, 7, 7, 7, 7],
}

# Colorblind-safe palette
colors = ["#306998", "#FFD43B", "#9467BD", "#17BECF", "#8C564B"]

# Create chart with container
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "column",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 250,
}

# Title
chart.options.title = {
    "text": "bar-stacked-percent · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle
chart.options.subtitle = {"text": "Market Share by Quarter", "style": {"fontSize": "32px"}}

# X-axis (categories)
chart.options.x_axis = {
    "categories": categories,
    "title": {"text": "Quarter", "style": {"fontSize": "36px"}, "margin": 30},
    "labels": {"style": {"fontSize": "32px"}},
}

# Y-axis (percentage)
chart.options.y_axis = {
    "min": 0,
    "max": 100,
    "title": {"text": "Market Share (%)", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}, "format": "{value}%"},
    "gridLineWidth": 1,
    "gridLineColor": "#E0E0E0",
}

# Plot options for 100% stacked column
chart.options.plot_options = {
    "column": {
        "stacking": "percent",
        "borderWidth": 1,
        "borderColor": "#ffffff",
        "dataLabels": {
            "enabled": True,
            "format": "{point.percentage:.1f}%",
            "style": {"fontSize": "20px", "fontWeight": "bold", "textOutline": "none"},
            "color": "#ffffff",
        },
    }
}

# Legend
chart.options.legend = {
    "enabled": True,
    "align": "center",
    "verticalAlign": "bottom",
    "layout": "horizontal",
    "itemStyle": {"fontSize": "32px"},
    "symbolRadius": 0,
    "symbolHeight": 24,
    "symbolWidth": 48,
    "itemDistance": 60,
    "margin": 20,
    "y": -60,
}

# Tooltip
chart.options.tooltip = {
    "pointFormat": '<span style="color:{point.color}">\u25cf</span> {series.name}: <b>{point.percentage:.1f}%</b> ({point.y})<br/>',
    "shared": False,
    "style": {"fontSize": "24px"},
}

# Add series
for i, (name, data) in enumerate(series_data.items()):
    series = ColumnSeries()
    series.name = name
    series.data = data
    series.color = colors[i % len(colors)]
    chart.add_series(series)

# Download Highcharts JS (required for headless Chrome)
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

# Also save as plot.html for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    # For HTML export, use CDN links for portability
    html_export = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(html_export)

# Setup Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2800")

# Take screenshot
driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render

# Screenshot the chart container element for exact dimensions
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
