""" pyplots.ai
box-horizontal: Horizontal Box Plot
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.boxplot import BoxPlotSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Response times by service type (realistic scenario)
np.random.seed(42)

categories = ["API Gateway", "Database Query", "File Upload", "Authentication", "Payment Processing"]

# Generate data with different distributions for each service
# Each category needs: [low, q1, median, q3, high]
data = []
for cat in categories:
    if cat == "API Gateway":
        values = np.random.normal(50, 15, 200)  # Fast, consistent
    elif cat == "Database Query":
        values = np.random.normal(120, 40, 200)  # Moderate with variation
    elif cat == "File Upload":
        values = np.random.normal(250, 80, 200)  # Slow, high variance
    elif cat == "Authentication":
        values = np.random.normal(30, 8, 200)  # Very fast
    else:  # Payment Processing
        values = np.random.normal(180, 50, 200)  # Moderate-slow

    # Ensure positive values
    values = np.maximum(values, 5)

    # Calculate quartiles
    q1, median, q3 = np.percentile(values, [25, 50, 75])
    iqr = q3 - q1
    low = max(values.min(), q1 - 1.5 * iqr)
    high = min(values.max(), q3 + 1.5 * iqr)

    # Data as list format for Highcharts boxplot: [low, q1, median, q3, high]
    data.append([round(low, 1), round(q1, 1), round(median, 1), round(q3, 1), round(high, 1)])

# Create chart with container specified
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration - use full 4800x2700 with proper margins
chart.options.chart = {
    "type": "boxplot",
    "inverted": True,  # This makes it horizontal
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginLeft": 450,  # Extra space for category labels and axis title
    "marginBottom": 220,  # Extra space for value axis labels and title
    "marginTop": 180,
    "marginRight": 120,
}

# Title
chart.options.title = {
    "text": "box-horizontal · highcharts · pyplots.ai",
    "style": {"fontSize": "64px", "fontWeight": "bold"},
    "y": 60,
}

# Subtitle for context
chart.options.subtitle = {
    "text": "Response Time Distribution by Service Type",
    "style": {"fontSize": "42px", "color": "#666666"},
    "y": 120,
}

# X-axis (categories - shown on left due to inverted)
chart.options.x_axis = {
    "categories": categories,
    "title": {"text": "Service Type", "style": {"fontSize": "42px"}, "margin": 20},
    "labels": {"style": {"fontSize": "36px"}, "x": -10},
    "lineWidth": 2,
    "lineColor": "#333333",
}

# Y-axis (values - shown on bottom due to inverted)
chart.options.y_axis = {
    "title": {"text": "Response Time (ms)", "style": {"fontSize": "42px"}, "margin": 20},
    "labels": {"style": {"fontSize": "32px"}, "y": 30},
    "gridLineColor": "#e0e0e0",
    "gridLineWidth": 1,
    "min": 0,
    "lineWidth": 2,
    "lineColor": "#333333",
}

# Legend
chart.options.legend = {"enabled": False}

# Plot options for boxplot styling
chart.options.plot_options = {
    "boxplot": {
        "fillColor": "rgba(48, 105, 152, 0.7)",  # Python Blue with transparency
        "color": "#306998",  # Box outline color
        "lineWidth": 4,
        "medianColor": "#FFD43B",  # Python Yellow for median
        "medianWidth": 8,
        "stemColor": "#306998",
        "stemWidth": 4,
        "whiskerColor": "#306998",
        "whiskerLength": "40%",
        "whiskerWidth": 4,
        "pointWidth": 80,
    }
}

# Create box plot series
series = BoxPlotSeries()
series.name = "Response Time"
series.data = data

chart.add_series(series)

# Download Highcharts JS files (required for headless Chrome)
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# BoxPlot requires highcharts-more.js
highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Generate HTML with INLINE scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; padding:0; overflow:hidden;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")
chrome_options.add_argument("--force-device-scale-factor=1")

driver = webdriver.Chrome(options=chrome_options)
driver.set_window_size(4800, 2700)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file

print("Generated plot.png and plot.html")
