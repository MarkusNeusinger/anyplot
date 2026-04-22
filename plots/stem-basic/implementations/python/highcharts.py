""" pyplots.ai
stem-basic: Basic Stem Plot
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Discrete signal samples (simulating a damped oscillation)
np.random.seed(42)
x = np.arange(0, 30)
y = np.exp(-x / 10) * np.cos(x * 0.8) + np.random.randn(30) * 0.05

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {"width": 4800, "height": 2700, "backgroundColor": "#ffffff", "marginBottom": 150}

# Title
chart.options.title = {"text": "stem-basic · highcharts · pyplots.ai", "style": {"fontSize": "48px"}}

# X-axis configuration
chart.options.x_axis = {
    "title": {"text": "Sample Index", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0,0,0,0.1)",
    "lineWidth": 2,
    "lineColor": "#333333",
    "min": -0.5,
    "max": 29.5,
}

# Y-axis configuration
chart.options.y_axis = {
    "title": {"text": "Amplitude", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0,0,0,0.1)",
    "lineWidth": 2,
    "lineColor": "#333333",
    "plotLines": [{"value": 0, "width": 3, "color": "#333333", "zIndex": 2}],
}

# Disable legend
chart.options.legend = {"enabled": False}

# Add stems as individual line series
for xi, yi in zip(x, y, strict=True):
    stem_series = LineSeries()
    stem_series.data = [[float(xi), 0], [float(xi), float(yi)]]
    stem_series.color = "#306998"
    stem_series.line_width = 3
    stem_series.marker = {"enabled": False}
    stem_series.enable_mouse_tracking = False
    stem_series.states = {"hover": {"enabled": False}}
    chart.add_series(stem_series)

# Add markers at the top of each stem
marker_series = ScatterSeries()
marker_series.data = [[float(xi), float(yi)] for xi, yi in zip(x, y, strict=True)]
marker_series.name = "Signal"
marker_series.color = "#306998"
marker_series.marker = {"radius": 10, "lineWidth": 3, "lineColor": "#ffffff", "fillColor": "#306998"}

chart.add_series(marker_series)

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
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html, body {{ width: 4800px; height: 2700px; overflow: hidden; }}
        #container {{ width: 4800px; height: 2700px; }}
    </style>
</head>
<body>
    <div id="container"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save as plot.html for interactive version
Path("plot.html").write_text(html_content, encoding="utf-8")

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4900,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render

# Take screenshot of the container element for exact dimensions
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
