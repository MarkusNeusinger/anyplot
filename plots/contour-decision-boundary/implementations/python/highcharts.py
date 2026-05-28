""" anyplot.ai
contour-decision-boundary: Decision Boundary Classifier Visualization
Library: highcharts unknown | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-16
"""

import json
import os
import tempfile
import time
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from sklearn.datasets import make_moons
from sklearn.neighbors import KNeighborsClassifier


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
BRAND = "#009E73"  # Position 1 - always first series
SERIES_2 = "#C475FD"

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

# Load Highcharts JS from npm
HC_NPM = Path("/tmp/hc-tmp/node_modules/highcharts")
highcharts_js = (HC_NPM / "highcharts.js").read_text(encoding="utf-8")
heatmap_js = (HC_NPM / "modules/heatmap.js").read_text(encoding="utf-8")

# Build complete options as dict
options_dict = {
    "chart": {
        "width": 4800,
        "height": 2700,
        "backgroundColor": PAGE_BG,
        "marginBottom": 320,
        "marginLeft": 260,
        "marginRight": 440,
        "marginTop": 200,
        "spacingBottom": 40,
    },
    "title": {
        "text": "contour-decision-boundary · highcharts · anyplot.ai",
        "style": {"fontSize": "28px", "fontWeight": "normal", "color": INK},
    },
    "subtitle": {"text": "KNN Classifier Decision Boundary", "style": {"fontSize": "22px", "color": INK_SOFT}},
    "xAxis": {
        "min": x_min,
        "max": x_max,
        "title": {"text": "Feature X1", "style": {"fontSize": "22px", "color": INK}, "margin": 30, "enabled": True},
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}, "format": "{value:.1f}"},
        "tickInterval": 0.5,
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "gridLineColor": GRID,
        "offset": 0,
    },
    "yAxis": {
        "min": y_min,
        "max": y_max,
        "title": {"text": "Feature X2", "style": {"fontSize": "22px", "color": INK}, "margin": 40, "enabled": True},
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}, "format": "{value:.1f}"},
        "tickInterval": 0.5,
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "gridLineColor": GRID,
    },
    "colorAxis": {
        "min": 0,
        "max": 1,
        "stops": [[0, "#440154"], [0.5, "#21908C"], [1, "#FDE725"]],
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}, "format": "{value:.1f}"},
    },
    "legend": {
        "enabled": True,
        "align": "right",
        "verticalAlign": "top",
        "layout": "vertical",
        "itemStyle": {"fontSize": "16px", "color": INK_SOFT},
        "symbolRadius": 8,
        "symbolHeight": 20,
        "symbolWidth": 20,
        "itemMarginBottom": 20,
        "x": -50,
        "y": 60,
        "padding": 15,
        "backgroundColor": PAGE_BG,
        "borderWidth": 1,
        "borderColor": INK_SOFT,
        "title": {"text": "Training Data", "style": {"fontSize": "18px", "color": INK}},
    },
    "plotOptions": {
        "heatmap": {"borderWidth": 0, "colsize": x_step, "rowsize": y_step},
        "scatter": {
            "marker": {"radius": 8, "lineWidth": 2, "lineColor": PAGE_BG},
            "states": {"hover": {"enabled": True}},
        },
    },
    "tooltip": {"enabled": True, "style": {"fontSize": "16px", "color": INK}},
    "series": [
        {"type": "heatmap", "name": "Decision Region", "data": heatmap_data, "showInLegend": False},
        {
            "type": "scatter",
            "name": "Class 0",
            "data": class_0_points,
            "color": BRAND,
            "marker": {"symbol": "circle", "fillColor": BRAND},
            "showInLegend": True,
        },
        {
            "type": "scatter",
            "name": "Class 1",
            "data": class_1_points,
            "color": SERIES_2,
            "marker": {"symbol": "diamond", "fillColor": SERIES_2},
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

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
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
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
