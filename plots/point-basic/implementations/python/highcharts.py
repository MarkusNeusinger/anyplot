""" pyplots.ai
point-basic: Point Estimate Plot
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
from highcharts_core.options.series.bar import ColumnRangeSeries
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Performance metrics by department with confidence intervals
np.random.seed(42)
categories = ["Marketing", "Engineering", "Sales", "Operations", "Finance", "HR", "Research", "Customer Support"]
estimates = np.array([72, 85, 68, 79, 74, 66, 88, 71])
# Generate asymmetric confidence intervals
lower_errors = np.random.uniform(3, 8, len(categories))
upper_errors = np.random.uniform(3, 8, len(categories))
lower = estimates - lower_errors
upper = estimates + upper_errors

# Create chart with container (CRITICAL for rendering)
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginLeft": 280,
    "marginBottom": 250,
    "marginRight": 100,
    "marginTop": 150,
    "inverted": True,  # Horizontal orientation for reading category labels
}

# Title
chart.options.title = {
    "text": "point-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle
chart.options.subtitle = {
    "text": "Department Performance Scores with 95% Confidence Intervals",
    "style": {"fontSize": "32px"},
}

# X-axis (categories - appears on left due to inverted)
chart.options.x_axis = {
    "categories": list(categories),
    "title": {"text": "Department", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
    "lineWidth": 2,
    "lineColor": "#333333",
}

# Y-axis (values - appears on bottom due to inverted)
chart.options.y_axis = {
    "title": {"text": "Performance Score", "style": {"fontSize": "36px"}, "margin": 20},
    "labels": {"style": {"fontSize": "24px"}},
    "min": 50,
    "max": 100,
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "plotLines": [{"value": 75, "color": "#666666", "width": 3, "dashStyle": "Dash", "zIndex": 5}],
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "28px"},
    "layout": "horizontal",
    "align": "center",
    "verticalAlign": "bottom",
    "y": 20,
}

# Error bar series (confidence intervals) using columnrange
error_data = []
for i in range(len(categories)):
    error_data.append({"x": i, "low": float(lower[i]), "high": float(upper[i])})

error_series = ColumnRangeSeries()
error_series.name = "95% CI"
error_series.data = error_data
error_series.color = "#306998"
error_series.border_width = 0
error_series.point_width = 8

chart.add_series(error_series)

# Point estimate series (scatter points)
point_data = []
for i in range(len(categories)):
    point_data.append({"x": i, "y": float(estimates[i])})

point_series = ScatterSeries()
point_series.name = "Point Estimate"
point_series.data = point_data
point_series.color = "#FFD43B"
point_series.marker = {"radius": 16, "symbol": "circle", "lineWidth": 3, "lineColor": "#306998", "fillColor": "#FFD43B"}

chart.add_series(point_series)

# Plot options
chart.options.plot_options = {
    "series": {"animation": False},
    "scatter": {"marker": {"radius": 16, "states": {"hover": {"enabled": False}}}},
    "columnrange": {"groupPadding": 0, "pointPadding": 0},
}

# Credits
chart.options.credits = {"enabled": False}

# Download Highcharts JS (required for headless Chrome)
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Download highcharts-more.js for columnrange
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
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file

# Save HTML for interactive version (use CDN links for the HTML file)
html_interactive = f"""<!DOCTYPE html>
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

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_interactive)
