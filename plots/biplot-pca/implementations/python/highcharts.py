""" pyplots.ai
biplot-pca: PCA Biplot with Scores and Loading Vectors
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
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from sklearn.datasets import load_iris
from sklearn.preprocessing import StandardScaler


# Data - Iris dataset for PCA
iris = load_iris()
X = iris.data
y = iris.target
feature_names = iris.feature_names
target_names = iris.target_names

# Standardize features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# PCA computation
X_centered = X_scaled - X_scaled.mean(axis=0)
cov_matrix = np.cov(X_centered, rowvar=False)
eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)

# Sort by eigenvalue (descending)
idx = np.argsort(eigenvalues)[::-1]
eigenvalues = eigenvalues[idx]
eigenvectors = eigenvectors[:, idx]

# Project data onto first 2 PCs
scores = X_centered @ eigenvectors[:, :2]

# Loadings (correlation between original variables and PCs)
loadings = eigenvectors[:, :2]

# Variance explained
variance_explained = eigenvalues / eigenvalues.sum() * 100

# Scale loadings to match score range for visibility
score_max = np.max(np.abs(scores)) * 0.9
loading_scale = score_max / np.max(np.abs(loadings))
loadings_scaled = loadings * loading_scale

# Colors for species (colorblind-safe)
colors = ["#306998", "#FFD43B", "#9467BD"]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart settings
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 250,
    "marginLeft": 180,
    "marginRight": 200,
}

# Title
chart.options.title = {
    "text": "Iris PCA · biplot-pca · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Axes with variance explained
chart.options.x_axis = {
    "title": {"text": f"PC1 ({variance_explained[0]:.1f}%)", "style": {"fontSize": "36px"}, "margin": 20},
    "labels": {"style": {"fontSize": "24px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0,0,0,0.1)",
    "plotLines": [{"value": 0, "color": "#666666", "width": 2, "zIndex": 3}],
    "tickInterval": 0.5,
}

chart.options.y_axis = {
    "title": {"text": f"PC2 ({variance_explained[1]:.1f}%)", "style": {"fontSize": "36px"}, "margin": 20},
    "labels": {"style": {"fontSize": "24px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0,0,0,0.1)",
    "plotLines": [{"value": 0, "color": "#666666", "width": 2, "zIndex": 3}],
}

# Legend
chart.options.legend = {
    "enabled": True,
    "layout": "vertical",
    "align": "right",
    "verticalAlign": "middle",
    "itemStyle": {"fontSize": "32px"},
    "symbolRadius": 8,
    "itemMarginTop": 10,
}

# Add series for each species (observation scores)
for i, species in enumerate(target_names):
    mask = y == i
    series = ScatterSeries()
    series.name = species.capitalize()
    series.data = [{"x": float(scores[j, 0]), "y": float(scores[j, 1])} for j in range(len(y)) if mask[j]]
    series.color = colors[i]
    series.marker = {"radius": 14, "symbol": "circle"}
    chart.add_series(series)

# Plot options for all series
chart.options.plot_options = {
    "scatter": {
        "marker": {"radius": 14, "states": {"hover": {"radiusPlus": 4}}},
        "tooltip": {"headerFormat": "", "pointFormat": "<b>{series.name}</b>: ({point.x:.2f}, {point.y:.2f})"},
    },
    "series": {"animation": False},
}

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate JS literal
html_str = chart.to_js_literal()

# Create custom arrow drawing using SVG renderer after chart loads
arrow_js = """
Highcharts.addEvent(Highcharts.Chart, 'load', function() {
    var chart = this;
    var renderer = chart.renderer;
    var xAxis = chart.xAxis[0];
    var yAxis = chart.yAxis[0];

    // Loading vectors data
    var loadings = [
"""

for i, feature in enumerate(feature_names):
    clean_name = feature.replace(" (cm)", "").title()
    x_end = float(loadings_scaled[i, 0])
    y_end = float(loadings_scaled[i, 1])
    arrow_js += f'        {{name: "{clean_name}", x: {x_end}, y: {y_end}}},\n'

arrow_js += """    ];

    loadings.forEach(function(loading) {
        var x0 = xAxis.toPixels(0);
        var y0 = yAxis.toPixels(0);
        var x1 = xAxis.toPixels(loading.x);
        var y1 = yAxis.toPixels(loading.y);

        // Draw arrow line
        renderer.path(['M', x0, y0, 'L', x1, y1])
            .attr({
                stroke: '#E74C3C',
                'stroke-width': 6,
                zIndex: 10
            })
            .add();

        // Calculate arrowhead
        var angle = Math.atan2(y1 - y0, x1 - x0);
        var headLen = 25;
        var headAngle = Math.PI / 6;

        var ax1 = x1 - headLen * Math.cos(angle - headAngle);
        var ay1 = y1 - headLen * Math.sin(angle - headAngle);
        var ax2 = x1 - headLen * Math.cos(angle + headAngle);
        var ay2 = y1 - headLen * Math.sin(angle + headAngle);

        // Draw arrowhead
        renderer.path(['M', x1, y1, 'L', ax1, ay1, 'M', x1, y1, 'L', ax2, ay2])
            .attr({
                stroke: '#E74C3C',
                'stroke-width': 6,
                zIndex: 10
            })
            .add();

        // Add label with offset
        var labelX = x1 + 15 * Math.cos(angle);
        var labelY = y1 + 15 * Math.sin(angle);
        renderer.text(loading.name, labelX, labelY)
            .attr({
                zIndex: 11
            })
            .css({
                fontSize: '28px',
                fontWeight: 'bold',
                color: '#E74C3C'
            })
            .add();
    });
});
"""

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{arrow_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save interactive HTML
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
