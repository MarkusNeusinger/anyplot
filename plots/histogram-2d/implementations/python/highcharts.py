""" pyplots.ai
histogram-2d: 2D Histogram Heatmap
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - bivariate normal with correlation (5000 points)
np.random.seed(42)
n_points = 5000

# Create correlated bivariate data (simulating financial returns)
mean = [5, 8]  # Mean values for X (Asset A return %) and Y (Asset B return %)
cov = [[4, 2.5], [2.5, 6]]  # Covariance matrix showing positive correlation
data_points = np.random.multivariate_normal(mean, cov, n_points)
x_data = data_points[:, 0]
y_data = data_points[:, 1]

# Create 2D histogram bins
n_bins = 30
x_edges = np.linspace(x_data.min() - 0.5, x_data.max() + 0.5, n_bins + 1)
y_edges = np.linspace(y_data.min() - 0.5, y_data.max() + 0.5, n_bins + 1)

# Compute 2D histogram
hist, _, _ = np.histogram2d(x_data, y_data, bins=[x_edges, y_edges])

# Prepare heatmap data for Highcharts: [x_index, y_index, value]
heatmap_data = []
x_centers = (x_edges[:-1] + x_edges[1:]) / 2
y_centers = (y_edges[:-1] + y_edges[1:]) / 2

for i in range(n_bins):
    for j in range(n_bins):
        if hist[i, j] > 0:  # Only include non-zero bins
            heatmap_data.append([i, j, int(hist[i, j])])

# Format tick labels (show every 5th bin)
x_categories = [f"{v:.1f}" if idx % 5 == 0 else "" for idx, v in enumerate(x_centers)]
y_categories = [f"{v:.1f}" if idx % 5 == 0 else "" for idx, v in enumerate(y_centers)]

# Build chart options as dictionary
chart_options = {
    "chart": {
        "type": "heatmap",
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "marginTop": 120,
        "marginBottom": 250,
        "marginLeft": 200,
        "marginRight": 250,
    },
    "title": {"text": "histogram-2d · highcharts · pyplots.ai", "style": {"fontSize": "48px", "fontWeight": "bold"}},
    "xAxis": {
        "categories": x_categories,
        "title": {"text": "Asset A Return (%)", "style": {"fontSize": "36px"}},
        "labels": {"style": {"fontSize": "22px"}, "rotation": 0},
        "tickLength": 10,
    },
    "yAxis": {
        "categories": y_categories,
        "title": {"text": "Asset B Return (%)", "style": {"fontSize": "36px"}},
        "labels": {"style": {"fontSize": "22px"}},
        "reversed": False,
    },
    "colorAxis": {
        "min": 0,
        "max": int(hist.max()),
        "stops": [
            [0, "#440154"],  # Dark purple (viridis start)
            [0.25, "#3b528b"],  # Blue
            [0.5, "#21918c"],  # Teal
            [0.75, "#5ec962"],  # Green
            [1, "#fde725"],  # Yellow (viridis end)
        ],
        "labels": {"style": {"fontSize": "24px"}},
    },
    "legend": {
        "align": "right",
        "layout": "vertical",
        "verticalAlign": "middle",
        "symbolHeight": 500,
        "symbolWidth": 40,
        "title": {"text": "Count", "style": {"fontSize": "28px", "fontWeight": "normal"}},
        "itemStyle": {"fontSize": "24px"},
    },
    "tooltip": {
        "style": {"fontSize": "24px"},
        "formatter": None,  # Will be set via JavaScript
    },
    "credits": {"enabled": False},
    "series": [{"type": "heatmap", "name": "Density", "data": heatmap_data, "borderWidth": 0, "nullColor": "#ffffff"}],
}

# Download Highcharts JS and heatmap module
highcharts_url = "https://code.highcharts.com/highcharts.js"
heatmap_url = "https://code.highcharts.com/modules/heatmap.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(heatmap_url, timeout=30) as response:
    heatmap_js = response.read().decode("utf-8")

# Convert options to JSON (remove None for tooltip formatter)
chart_options["tooltip"] = {"style": {"fontSize": "24px"}}
options_json = json.dumps(chart_options)

# Create x and y center arrays for tooltip
x_centers_json = json.dumps([round(v, 2) for v in x_centers])
y_centers_json = json.dumps([round(v, 2) for v in y_centers])

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        var xCenters = {x_centers_json};
        var yCenters = {y_centers_json};
        var options = {options_json};
        options.tooltip.formatter = function() {{
            return 'X: ' + xCenters[this.point.x].toFixed(1) + '%<br>' +
                   'Y: ' + yCenters[this.point.y].toFixed(1) + '%<br>' +
                   'Count: <b>' + this.point.value + '</b>';
        }};
        Highcharts.chart('container', options);
    </script>
</body>
</html>"""

# Save HTML for interactive version
html_interactive = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/heatmap.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>
        var xCenters = {x_centers_json};
        var yCenters = {y_centers_json};
        var options = {options_json};
        options.chart.width = null;
        options.chart.height = null;
        options.tooltip.formatter = function() {{
            return 'X: ' + xCenters[this.point.x].toFixed(1) + '%<br>' +
                   'Y: ' + yCenters[this.point.y].toFixed(1) + '%<br>' +
                   'Count: <b>' + this.point.value + '</b>';
        }};
        Highcharts.chart('container', options);
    </script>
</body>
</html>"""

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_interactive)

# Take screenshot using headless Chrome
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
