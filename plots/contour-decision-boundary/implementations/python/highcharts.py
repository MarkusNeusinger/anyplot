""" pyplots.ai
contour-decision-boundary: Decision Boundary Classifier Visualization
Library: highcharts unknown | Python 3.13.11
Quality: 90/100 | Created: 2025-12-31
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from sklearn.datasets import make_moons
from sklearn.neighbors import KNeighborsClassifier


# Data: Generate moon-shaped classification dataset
np.random.seed(42)
X, y = make_moons(n_samples=150, noise=0.25, random_state=42)

# Train a KNN classifier
classifier = KNeighborsClassifier(n_neighbors=15)
classifier.fit(X, y)

# Create mesh grid for decision boundary
x_min, x_max = X[:, 0].min() - 0.5, X[:, 0].max() + 0.5
y_min, y_max = X[:, 1].min() - 0.5, X[:, 1].max() + 0.5
resolution = 80

xx, yy = np.meshgrid(np.linspace(x_min, x_max, resolution), np.linspace(y_min, y_max, resolution))

# Predict class probabilities on mesh grid
mesh_points = np.c_[xx.ravel(), yy.ravel()]
Z_proba = classifier.predict_proba(mesh_points)[:, 1]
Z = Z_proba.reshape(xx.shape)

# Prepare heatmap data with actual coordinate values [x, y, value]
heatmap_data = []
x_step = (x_max - x_min) / resolution
y_step = (y_max - y_min) / resolution
for i in range(resolution):
    for j in range(resolution):
        x_val = round(xx[i, j], 4)
        y_val = round(yy[i, j], 4)
        heatmap_data.append([x_val, y_val, round(Z[i, j], 3)])

# Prepare scatter data for training points
class_0_points = [[round(float(X[i, 0]), 4), round(float(X[i, 1]), 4)] for i in range(len(y)) if y[i] == 0]
class_1_points = [[round(float(X[i, 0]), 4), round(float(X[i, 1]), 4)] for i in range(len(y)) if y[i] == 1]

# Download Highcharts JS and heatmap module
highcharts_url = "https://code.highcharts.com/highcharts.js"
heatmap_url = "https://code.highcharts.com/modules/heatmap.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(heatmap_url, timeout=30) as response:
    heatmap_js = response.read().decode("utf-8")

# Build complete options as dict
options_dict = {
    "chart": {
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "marginBottom": 320,
        "marginLeft": 260,
        "marginRight": 440,
        "marginTop": 200,
        "spacingBottom": 40,
    },
    "title": {
        "text": "contour-decision-boundary · highcharts · pyplots.ai",
        "style": {"fontSize": "56px", "fontWeight": "bold"},
    },
    "subtitle": {"text": "KNN Classifier Decision Boundary on Moon-shaped Data", "style": {"fontSize": "38px"}},
    "xAxis": {
        "min": x_min,
        "max": x_max,
        "title": {
            "text": "Feature X1",
            "style": {"fontSize": "46px", "fontWeight": "bold"},
            "margin": 30,
            "enabled": True,
        },
        "labels": {"style": {"fontSize": "34px"}, "format": "{value:.1f}"},
        "tickInterval": 0.5,
        "gridLineWidth": 1,
        "gridLineColor": "#cccccc",
        "offset": 0,
    },
    "yAxis": {
        "min": y_min,
        "max": y_max,
        "title": {
            "text": "Feature X2",
            "style": {"fontSize": "46px", "fontWeight": "bold"},
            "margin": 40,
            "enabled": True,
        },
        "labels": {"style": {"fontSize": "34px"}, "format": "{value:.1f}"},
        "tickInterval": 0.5,
        "gridLineWidth": 1,
        "gridLineColor": "#cccccc",
    },
    "colorAxis": {
        "min": 0,
        "max": 1,
        "stops": [[0, "#306998"], [0.5, "#E8E8E8"], [1, "#FFD43B"]],
        "labels": {"style": {"fontSize": "34px"}, "format": "{value:.1f}"},
    },
    "legend": {
        "enabled": True,
        "align": "right",
        "verticalAlign": "top",
        "layout": "vertical",
        "itemStyle": {"fontSize": "38px", "fontWeight": "normal"},
        "symbolRadius": 16,
        "symbolHeight": 40,
        "symbolWidth": 40,
        "itemMarginBottom": 40,
        "x": -50,
        "y": 120,
        "width": 380,
        "padding": 25,
        "backgroundColor": "rgba(255, 255, 255, 0.95)",
        "borderWidth": 2,
        "borderColor": "#999999",
        "title": {"text": "Training Data", "style": {"fontSize": "40px", "fontWeight": "bold"}},
    },
    "plotOptions": {
        "heatmap": {"borderWidth": 0, "colsize": x_step, "rowsize": y_step, "nullColor": "#E8E8E8"},
        "scatter": {
            "marker": {"radius": 22, "lineWidth": 5, "lineColor": "#222222"},
            "states": {"hover": {"enabled": True, "lineWidth": 0}},
        },
    },
    "tooltip": {"enabled": True, "style": {"fontSize": "24px"}},
    "series": [
        {"type": "heatmap", "name": "Decision Region", "data": heatmap_data, "showInLegend": False},
        {
            "type": "scatter",
            "name": "Class 0 (Moon A)",
            "data": class_0_points,
            "color": "#306998",
            "marker": {"symbol": "circle", "fillColor": "#306998"},
            "showInLegend": True,
        },
        {
            "type": "scatter",
            "name": "Class 1 (Moon B)",
            "data": class_1_points,
            "color": "#FFD43B",
            "marker": {"symbol": "diamond", "fillColor": "#FFD43B"},
            "showInLegend": True,
        },
    ],
}

# Generate JavaScript from options dict
options_js = json.dumps(options_dict)
chart_js = f"Highcharts.chart('container', {options_js});"

# HTML content with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="margin:0; padding:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{chart_js}</script>
</body>
</html>"""

# Save HTML for debugging
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

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
