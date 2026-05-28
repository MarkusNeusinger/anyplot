""" anyplot.ai
biplot-pca: PCA Biplot with Scores and Loading Vectors
Library: highcharts unknown | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-17
"""

import os
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


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"  # Okabe-Ito position 1
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]  # Positions 1-3 for species

# Data - Iris dataset for PCA
np.random.seed(42)
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

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart settings with theme-aware colors
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 250,
    "marginLeft": 180,
    "marginRight": 200,
}

# Title
chart.options.title = {
    "text": "biplot-pca · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "medium", "color": INK},
}

# Axes with variance explained
chart.options.x_axis = {
    "title": {"text": f"PC1 ({variance_explained[0]:.1f}%)", "style": {"fontSize": "22px", "color": INK}, "margin": 20},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineWidth": 1,
    "gridLineColor": RULE,
    "plotLines": [{"value": 0, "color": INK_SOFT, "width": 2, "zIndex": 3}],
    "tickInterval": 0.5,
}

chart.options.y_axis = {
    "title": {"text": f"PC2 ({variance_explained[1]:.1f}%)", "style": {"fontSize": "22px", "color": INK}, "margin": 20},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineWidth": 1,
    "gridLineColor": RULE,
    "plotLines": [{"value": 0, "color": INK_SOFT, "width": 2, "zIndex": 3}],
}

# Legend
chart.options.legend = {
    "enabled": True,
    "layout": "vertical",
    "align": "right",
    "verticalAlign": "middle",
    "itemStyle": {"fontSize": "16px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "symbolRadius": 8,
    "itemMarginTop": 10,
}

# Add series for each species (observation scores)
for i, species in enumerate(target_names):
    mask = y == i
    series = ScatterSeries()
    series.name = species.capitalize()
    series.data = [{"x": float(scores[j, 0]), "y": float(scores[j, 1])} for j in range(len(y)) if mask[j]]
    series.color = IMPRINT[i]
    series.marker = {"radius": 8}
    chart.add_series(series)

# Plot options for all series
chart.options.plot_options = {
    "scatter": {
        "marker": {"radius": 8, "states": {"hover": {"radiusPlus": 2}}},
        "tooltip": {"headerFormat": "", "pointFormat": "<b>{series.name}</b>: ({point.x:.2f}, {point.y:.2f})"},
    },
    "series": {"animation": False},
}

# Set colors for chart-level consistency
chart.options.colors = IMPRINT

# Download Highcharts JS with retries and fallback CDN URLs
cdn_urls = [
    "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.min.js",
    "https://unpkg.com/highcharts@11/highcharts.js",
    "https://code.highcharts.com/highcharts.js",
]

highcharts_js = None
for url in cdn_urls:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"})
    max_retries = 2
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                highcharts_js = response.read().decode("utf-8")
                break
        except (urllib.error.URLError, urllib.error.HTTPError):
            if attempt < max_retries - 1:
                time.sleep(1)
    if highcharts_js:
        break

if not highcharts_js:
    raise RuntimeError("Could not download Highcharts from any CDN")

# Generate JS literal
html_str = chart.to_js_literal()

# Create custom arrow drawing using SVG renderer after chart loads
# Arrow color is theme-aware INK_SOFT for subtle appearance
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

# Arrow color uses theme-aware INK value for better contrast
arrow_color = INK if THEME == "light" else ELEVATED_BG
arrow_js += f"""    ];

    loadings.forEach(function(loading) {{
        var x0 = xAxis.toPixels(0);
        var y0 = yAxis.toPixels(0);
        var x1 = xAxis.toPixels(loading.x);
        var y1 = yAxis.toPixels(loading.y);

        // Draw arrow line
        renderer.path(['M', x0, y0, 'L', x1, y1])
            .attr({{
                stroke: '{arrow_color}',
                'stroke-width': 4,
                zIndex: 10
            }})
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
            .attr({{
                stroke: '{arrow_color}',
                'stroke-width': 4,
                zIndex: 10
            }})
            .add();

        // Add label with offset
        var labelX = x1 + 15 * Math.cos(angle);
        var labelY = y1 + 15 * Math.sin(angle);
        renderer.text(loading.name, labelX, labelY)
            .attr({{
                zIndex: 11
            }})
            .css({{
                fontSize: '18px',
                fontWeight: 'bold',
                color: '{arrow_color}'
            }})
            .add();
    }});
}});
"""

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{arrow_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save interactive HTML with theme-suffixed filename
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot for PNG
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
