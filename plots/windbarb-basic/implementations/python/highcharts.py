""" pyplots.ai
windbarb-basic: Wind Barb Plot for Meteorological Data
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Surface wind observations from weather stations
np.random.seed(42)

# Create 20 weather station observations along a transect
n_stations = 20

# Generate u and v wind components (m/s) - simulating a weather pattern
# Varying wind speeds and directions to show different barb notations
u = 8 + 6 * np.sin(np.linspace(0, 2 * np.pi, n_stations)) + np.random.randn(n_stations) * 2
v = 4 + 4 * np.cos(np.linspace(0, 1.5 * np.pi, n_stations)) + np.random.randn(n_stations) * 2

# Convert u, v to speed (knots) and direction (degrees)
# Wind direction: 0° = North, 90° = East, 180° = South, 270° = West
# Direction FROM which wind blows (meteorological convention)
speed_ms = np.sqrt(u**2 + v**2)
speed_knots = speed_ms * 1.94384  # Convert m/s to knots
direction = (270 - np.degrees(np.arctan2(v, u))) % 360  # Meteorological direction

# Prepare data with y-coordinate for positioning
# Windbarb data format: {x, y, value, direction} where y is the position on the y-axis
data_points = []
for i in range(n_stations):
    # Use wind speed as y-position so barbs are plotted at their speed level
    data_points.append(
        {
            "x": i,
            "y": round(float(speed_knots[i]), 1),
            "value": round(float(speed_knots[i]), 1),
            "direction": round(float(direction[i]), 0),
        }
    )

# Chart configuration
chart_config = {
    "chart": {
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "marginBottom": 350,
        "marginLeft": 280,
        "marginRight": 150,
        "marginTop": 200,
    },
    "title": {"text": "windbarb-basic · highcharts · pyplots.ai", "style": {"fontSize": "72px", "fontWeight": "bold"}},
    "subtitle": {
        "text": "Surface Wind Observations from Weather Station Network",
        "style": {"fontSize": "44px", "color": "#666666"},
    },
    "xAxis": {
        "title": {"text": "Weather Station Index", "style": {"fontSize": "48px"}, "margin": 30},
        "labels": {"style": {"fontSize": "40px"}},
        "lineWidth": 4,
        "tickWidth": 4,
        "tickInterval": 2,
    },
    "yAxis": {
        "title": {"text": "Wind Speed (knots)", "style": {"fontSize": "48px"}},
        "labels": {"style": {"fontSize": "40px"}},
        "min": 0,
        "max": 40,
        "tickInterval": 5,
        "gridLineWidth": 2,
        "gridLineColor": "#e0e0e0",
    },
    "legend": {
        "enabled": True,
        "itemStyle": {"fontSize": "40px"},
        "verticalAlign": "bottom",
        "align": "center",
        "y": -100,
    },
    "tooltip": {
        "style": {"fontSize": "32px"},
        "headerFormat": "<b>Station {point.x}</b><br/>",
        "pointFormat": "Wind: {point.value} knots from {point.direction}°<br/>{point.beaufort}",
    },
    "plotOptions": {"windbarb": {"vectorLength": 80, "lineWidth": 6, "yOffset": 0}},
    "series": [
        {
            "type": "windbarb",
            "name": "Surface Wind",
            "data": data_points,
            "color": "#306998",
            "lineWidth": 6,
            "vectorLength": 80,
        }
    ],
    "credits": {"enabled": False},
}

# Download Highcharts JS and required modules
# Windbarb requires: highcharts-more + datagrouping module for approximations
highcharts_url = "https://code.highcharts.com/highcharts.js"
highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
datagrouping_url = "https://code.highcharts.com/modules/datagrouping.js"
windbarb_url = "https://code.highcharts.com/modules/windbarb.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

with urllib.request.urlopen(datagrouping_url, timeout=30) as response:
    datagrouping_js = response.read().decode("utf-8")

with urllib.request.urlopen(windbarb_url, timeout=30) as response:
    windbarb_js = response.read().decode("utf-8")

# Generate HTML with inline scripts (load order matters!)
chart_json = json.dumps(chart_config)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
    <script>{datagrouping_js}</script>
    <script>{windbarb_js}</script>
</head>
<body style="margin:0; padding:0; background:#ffffff;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        Highcharts.chart('container', {chart_json});
    </script>
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
chrome_options.add_argument("--window-size=4900,2800")
chrome_options.add_argument("--force-device-scale-factor=1")

driver = webdriver.Chrome(options=chrome_options)
driver.set_window_size(4900, 2800)
driver.get(f"file://{temp_path}")
time.sleep(5)

# Take screenshot of the container element to get exact 4800x2700
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

# Ensure exact dimensions
img = Image.open("plot.png")
if img.size != (4800, 2700):
    img = img.resize((4800, 2700), Image.LANCZOS)
    img.save("plot.png")

Path(temp_path).unlink()

# Also save as HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    # For HTML output, use CDN links for smaller file size
    # Windbarb requires: highcharts-more.js + datagrouping.js before windbarb.js
    html_interactive = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>windbarb-basic · highcharts · pyplots.ai</title>
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/highcharts-more.js"></script>
    <script src="https://code.highcharts.com/modules/datagrouping.js"></script>
    <script src="https://code.highcharts.com/modules/windbarb.js"></script>
</head>
<body style="margin:0; padding:20px; background:#ffffff;">
    <div id="container" style="width: 100%; height: 90vh; min-height: 600px;"></div>
    <script>
        Highcharts.chart('container', {chart_json});
    </script>
</body>
</html>"""
    f.write(html_interactive)
