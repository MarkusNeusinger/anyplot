""" pyplots.ai
line-filled: Filled Line Plot
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
from highcharts_core.options.series.area import AreaSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Monthly website traffic over a year
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
# Simulating website traffic with seasonal trends (higher in summer)
base_traffic = 50000
seasonal = np.sin(np.linspace(0, 2 * np.pi, 12)) * 15000
noise = np.random.normal(0, 3000, 12)
traffic = base_traffic + seasonal + noise + np.linspace(0, 10000, 12)  # Growth trend
traffic = np.maximum(traffic, 0).astype(int)

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "area",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 220,
    "marginLeft": 150,
    "spacingTop": 40,
}

# Title
chart.options.title = {
    "text": "line-filled · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle
chart.options.subtitle = {"text": "Monthly Website Traffic", "style": {"fontSize": "32px"}}

# X-axis configuration
chart.options.x_axis = {
    "categories": months,
    "title": {"text": "Month", "style": {"fontSize": "32px"}, "margin": 20},
    "labels": {"style": {"fontSize": "28px"}},
    "lineWidth": 2,
    "tickWidth": 2,
}

# Y-axis configuration
chart.options.y_axis = {
    "title": {"text": "Page Views", "style": {"fontSize": "32px"}},
    "labels": {"style": {"fontSize": "24px"}},
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "min": 0,
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "28px"},
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 100,
}

# Plot options
chart.options.plot_options = {
    "area": {
        "fillOpacity": 0.4,
        "lineWidth": 4,
        "marker": {"enabled": True, "radius": 8, "lineWidth": 2, "lineColor": "#ffffff"},
        "states": {"hover": {"lineWidth": 5}},
    }
}

# Create series
series = AreaSeries()
series.name = "Website Traffic"
series.data = [int(v) for v in traffic]
series.color = "#306998"
series.fill_color = {
    "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
    "stops": [[0, "rgba(48, 105, 152, 0.5)"], [1, "rgba(48, 105, 152, 0.1)"]],
}

chart.add_series(series)

# Download Highcharts JS
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

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)
