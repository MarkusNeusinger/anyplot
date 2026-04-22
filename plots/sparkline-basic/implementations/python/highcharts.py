""" pyplots.ai
sparkline-basic: Basic Sparkline
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


# Data - simulate daily sales trend over 60 days with realistic patterns
np.random.seed(42)
base = 100
trend = np.linspace(0, 20, 60)  # Gradual upward trend
seasonal = 10 * np.sin(np.linspace(0, 4 * np.pi, 60))  # Cyclical pattern
noise = np.random.randn(60) * 5  # Random variation
values = base + trend + seasonal + noise

# Create chart - sparklines are minimal with no chrome
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart settings - standard pyplots size with sparkline aesthetic
chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "margin": [150, 200, 150, 200],  # Larger left/right margins for marker visibility at edges
    "spacing": [0, 0, 0, 0],
}

# Title with pyplots format
chart.options.title = {
    "text": "sparkline-basic · highcharts · pyplots.ai",
    "align": "center",
    "style": {"fontSize": "72px", "fontWeight": "bold"},
    "y": 80,
}

# Hide axes - sparklines have no axes
# Use minPadding/maxPadding to ensure markers at edges are visible
chart.options.x_axis = {
    "visible": False,
    "lineWidth": 0,
    "tickWidth": 0,
    "labels": {"enabled": False},
    "minPadding": 0.02,  # Add 2% padding on left
    "maxPadding": 0.02,  # Add 2% padding on right
}
chart.options.y_axis = {"visible": False, "gridLineWidth": 0, "labels": {"enabled": False}}

# Hide legend
chart.options.legend = {"enabled": False}

# Series data - the sparkline itself
series = LineSeries()
series.data = values.tolist()
series.name = "Trend"
series.color = "#306998"  # Python Blue
series.line_width = 10

# Disable markers on main line
series.marker = {"enabled": False, "radius": 0}

chart.add_series(series)

# Add min point marker - colorblind-safe orange instead of red
min_idx = int(np.argmin(values))
min_series = ScatterSeries()
min_series.data = [[min_idx, float(values[min_idx])]]
min_series.name = "Min"
min_series.color = "#D35400"  # Colorblind-safe orange for minimum
min_series.marker = {"enabled": True, "radius": 32, "symbol": "circle"}
chart.add_series(min_series)

# Add max point marker - colorblind-safe teal instead of green
max_idx = int(np.argmax(values))
max_series = ScatterSeries()
max_series.data = [[max_idx, float(values[max_idx])]]
max_series.name = "Max"
max_series.color = "#17BECF"  # Colorblind-safe teal for maximum
max_series.marker = {"enabled": True, "radius": 32, "symbol": "circle"}
chart.add_series(max_series)

# Add first point marker (reference)
first_series = ScatterSeries()
first_series.data = [[0, float(values[0])]]
first_series.name = "Start"
first_series.color = "#6B7280"  # Gray for start
first_series.marker = {"enabled": True, "radius": 28, "symbol": "circle"}
chart.add_series(first_series)


# Plot options for clean rendering
chart.options.plot_options = {
    "series": {"animation": False, "enableMouseTracking": False},
    "line": {"marker": {"enabled": False}},
}

# Download Highcharts JS for headless rendering
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
<body style="margin:0; background-color: #ffffff;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save interactive HTML version
html_interactive = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0; background-color: #ffffff;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_interactive)

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")
chrome_options.add_argument("--hide-scrollbars")

driver = webdriver.Chrome(options=chrome_options)
driver.set_window_size(4800, 2700)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
