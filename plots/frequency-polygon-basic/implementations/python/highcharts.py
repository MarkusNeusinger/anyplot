""" pyplots.ai
frequency-polygon-basic: Frequency Polygon for Distribution Comparison
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
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


# Data - Test scores for three different classes
np.random.seed(42)
# Class A: Normal distribution, average performance
class_a = np.random.normal(loc=72, scale=12, size=200)
# Class B: Higher average, tighter spread
class_b = np.random.normal(loc=80, scale=8, size=200)
# Class C: Bimodal - mix of high and low performers
class_c = np.concatenate([np.random.normal(loc=55, scale=8, size=100), np.random.normal(loc=85, scale=6, size=100)])

# Clip to valid score range
class_a = np.clip(class_a, 0, 100)
class_b = np.clip(class_b, 0, 100)
class_c = np.clip(class_c, 0, 100)

# Calculate histogram bin edges (same bins for all groups)
bins = np.linspace(0, 100, 21)  # 20 bins
bin_centers = (bins[:-1] + bins[1:]) / 2

# Calculate frequency (count) for each class
freq_a, _ = np.histogram(class_a, bins=bins)
freq_b, _ = np.histogram(class_b, bins=bins)
freq_c, _ = np.histogram(class_c, bins=bins)

# Extend lines to zero at both ends to close the polygon shape
extended_centers = np.concatenate([[bins[0]], bin_centers, [bins[-1]]])
freq_a_extended = np.concatenate([[0], freq_a, [0]])
freq_b_extended = np.concatenate([[0], freq_b, [0]])
freq_c_extended = np.concatenate([[0], freq_c, [0]])

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "areaspline",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 300,
    "marginLeft": 220,
    "marginRight": 180,
    "marginTop": 150,
}

# Title
chart.options.title = {
    "text": "frequency-polygon-basic \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# X-axis (score ranges)
chart.options.x_axis = {
    "title": {"text": "Test Score", "style": {"fontSize": "36px"}, "margin": 30},
    "labels": {"style": {"fontSize": "28px"}, "y": 35},
    "tickInterval": 10,
    "min": 0,
    "max": 100,
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
}

# Y-axis (frequency)
chart.options.y_axis = {
    "title": {"text": "Number of Students", "style": {"fontSize": "36px"}, "margin": 20},
    "labels": {"style": {"fontSize": "28px"}},
    "min": 0,
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "28px"},
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 80,
}

# Plot options for area spline (frequency polygon)
chart.options.plot_options = {
    "areaspline": {"fillOpacity": 0.2, "lineWidth": 5, "marker": {"enabled": True, "radius": 8, "symbol": "circle"}}
}

# Create series for each class
series_a = AreaSeries()
series_a.name = "Class A (Avg: 72)"
series_a.data = [[float(x), int(y)] for x, y in zip(extended_centers, freq_a_extended, strict=True)]
series_a.color = "#306998"  # Python Blue
series_a.marker = {"fillColor": "#306998", "lineWidth": 2, "lineColor": "#ffffff"}

series_b = AreaSeries()
series_b.name = "Class B (Avg: 80)"
series_b.data = [[float(x), int(y)] for x, y in zip(extended_centers, freq_b_extended, strict=True)]
series_b.color = "#FFD43B"  # Python Yellow
series_b.marker = {"fillColor": "#FFD43B", "lineWidth": 2, "lineColor": "#ffffff"}

series_c = AreaSeries()
series_c.name = "Class C (Bimodal)"
series_c.data = [[float(x), int(y)] for x, y in zip(extended_centers, freq_c_extended, strict=True)]
series_c.color = "#9467BD"  # Purple
series_c.marker = {"fillColor": "#9467BD", "lineWidth": 2, "lineColor": "#ffffff"}

# Add series to chart
chart.add_series(series_a)
chart.add_series(series_b)
chart.add_series(series_c)

# Credits
chart.options.credits = {"enabled": False}

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

# Also save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    # Use CDN for the standalone HTML file (works in browsers)
    interactive_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>frequency-polygon-basic - highcharts - pyplots.ai</title>
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(interactive_html)
