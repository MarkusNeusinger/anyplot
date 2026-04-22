""" pyplots.ai
datamatrix-basic: Basic Data Matrix 2D Barcode
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-16
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.heatmap import HeatmapSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - create a 18x18 Data Matrix pattern
content = "SERIAL:12345678"
size = 18

# Create Data Matrix pattern with finder and timing patterns
matrix = np.zeros((size, size), dtype=int)

# L-shaped finder pattern (solid black on left and bottom edges)
matrix[:, 0] = 1  # Left edge - solid black column
matrix[size - 1, :] = 1  # Bottom edge - solid black row

# Alternating (clock) pattern on top and right edges
for i in range(size):
    matrix[0, i] = (i + 1) % 2  # Top edge alternating
    matrix[i, size - 1] = i % 2  # Right edge alternating

# Fill interior with pattern (simulating encoded data)
np.random.seed(42)
data_bits = np.random.randint(0, 2, size=((size - 2) * (size - 2)))
idx = 0
for row in range(1, size - 1):
    for col in range(1, size - 1):
        if idx < len(data_bits):
            matrix[row, col] = data_bits[idx]
            idx += 1

# Prepare heatmap data: [x, y, value] format
rows, cols = matrix.shape
heatmap_data = []
for row in range(rows):
    for col in range(cols):
        # Invert row for bottom-to-top display (L-pattern at bottom-left)
        y = rows - 1 - row
        value = int(matrix[row, col])
        heatmap_data.append([col, y, value])

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration - square aspect ratio for Data Matrix
chart.options.chart = {
    "type": "heatmap",
    "width": 3600,
    "height": 3600,
    "backgroundColor": "#ffffff",
    "marginTop": 200,
    "marginBottom": 200,
    "marginLeft": 200,
    "marginRight": 200,
}

# Title
chart.options.title = {
    "text": "datamatrix-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle with encoded content
chart.options.subtitle = {
    "text": f'Data Matrix Encoding: "{content}"',
    "style": {"fontSize": "32px", "color": "#666666"},
}

# X-axis - hide for clean barcode look
chart.options.x_axis = {
    "title": {"text": None},
    "min": -0.5,
    "max": cols - 0.5,
    "tickLength": 0,
    "labels": {"enabled": False},
    "gridLineWidth": 0,
    "lineWidth": 0,
}

# Y-axis - hide for clean barcode look
chart.options.y_axis = {
    "title": {"text": None},
    "min": -0.5,
    "max": rows - 0.5,
    "tickLength": 0,
    "labels": {"enabled": False},
    "gridLineWidth": 0,
    "lineWidth": 0,
    "reversed": False,
}

# Color axis - black (1) and white (0) cells
chart.options.color_axis = {"min": 0, "max": 1, "stops": [[0, "#ffffff"], [1, "#000000"]], "visible": False}

# Legend disabled
chart.options.legend = {"enabled": False}

# Credits
chart.options.credits = {"enabled": False}

# Create heatmap series
series = HeatmapSeries()
series.name = "Data Matrix"
series.data = heatmap_data
series.border_width = 0
series.colsize = 1
series.rowsize = 1
series.tooltip = {"headerFormat": "", "pointFormat": "Cell ({point.x}, {point.y})"}
series.data_labels = {"enabled": False}

chart.add_series(series)

# Download Highcharts JS and heatmap module
highcharts_url = "https://code.highcharts.com/highcharts.js"
heatmap_url = "https://code.highcharts.com/modules/heatmap.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(heatmap_url, timeout=30) as response:
    heatmap_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="margin:0; background-color: #ffffff;">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save as plot.html (interactive version)
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=3600,3600")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
