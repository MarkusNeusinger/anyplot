""" pyplots.ai
dendrogram-basic: Basic Dendrogram
Library: highcharts 1.10.3 | Python 3.14.3
Quality: 87/100 | Created: 2026-04-05
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from scipy.cluster.hierarchy import dendrogram, linkage
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Iris flower measurements (4 features for 15 samples)
np.random.seed(42)

samples_per_species = 5
labels = []
data = []

# Setosa: shorter petals, wider sepals
for i in range(samples_per_species):
    labels.append(f"Setosa-{i + 1}")
    data.append(
        [
            5.0 + np.random.randn() * 0.3,
            3.4 + np.random.randn() * 0.3,
            1.5 + np.random.randn() * 0.2,
            0.3 + np.random.randn() * 0.1,
        ]
    )

# Versicolor: medium measurements
for i in range(samples_per_species):
    labels.append(f"Versicolor-{i + 1}")
    data.append(
        [
            5.9 + np.random.randn() * 0.4,
            2.8 + np.random.randn() * 0.3,
            4.3 + np.random.randn() * 0.4,
            1.3 + np.random.randn() * 0.2,
        ]
    )

# Virginica: longer petals and sepals
for i in range(samples_per_species):
    labels.append(f"Virginica-{i + 1}")
    data.append(
        [
            6.6 + np.random.randn() * 0.5,
            3.0 + np.random.randn() * 0.3,
            5.5 + np.random.randn() * 0.5,
            2.0 + np.random.randn() * 0.3,
        ]
    )

data = np.array(data)

# Compute linkage matrix using Ward's method
linkage_matrix = linkage(data, method="ward")

# Get dendrogram structure with color threshold to show clusters
dend = dendrogram(linkage_matrix, labels=labels, no_plot=True, color_threshold=0.7 * max(linkage_matrix[:, 2]))

# Extract coordinates
icoord = dend["icoord"]
dcoord = dend["dcoord"]
ivl = dend["ivl"]
color_list = dend["color_list"]

# Map scipy default colors to a cohesive palette anchored on Python Blue
color_map = {
    "C0": "#306998",  # Python Blue - primary cluster
    "C1": "#E07A3A",  # Warm orange - secondary cluster
    "C2": "#5BA05B",  # Muted green - tertiary cluster
    "C3": "#8B6EB8",  # Soft purple
    "C4": "#C75A5A",  # Muted red
    "b": "#306998",  # Default blue mapped to Python Blue
}

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 280,
    "spacingTop": 30,
    "spacingLeft": 80,
    "spacingRight": 80,
}

# Title
chart.options.title = {
    "text": "Iris Species Clustering \u00b7 dendrogram-basic \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "44px", "fontWeight": "600", "color": "#2c3e50"},
    "margin": 40,
}

# X-axis with sample labels
x_positions = [(i * 10) + 5 for i in range(len(ivl))]
chart.options.x_axis = {
    "title": {"text": "Sample", "style": {"fontSize": "32px", "color": "#555"}},
    "tickPositions": x_positions,
    "labels": {"style": {"fontSize": "26px", "color": "#444"}, "rotation": 45},
    "min": 0,
    "max": len(ivl) * 10,
    "gridLineWidth": 0,
    "lineWidth": 2,
    "lineColor": "#cccccc",
    "tickWidth": 0,
}

# Y-axis for distance
chart.options.y_axis = {
    "title": {"text": "Distance (Ward)", "style": {"fontSize": "32px", "color": "#555"}},
    "labels": {"style": {"fontSize": "24px", "color": "#444"}},
    "gridLineColor": "rgba(0,0,0,0.08)",
    "gridLineWidth": 1,
    "lineWidth": 2,
    "lineColor": "#cccccc",
    "min": 0,
    "tickInterval": 1,
}

# Hide legend
chart.options.legend = {"enabled": False}

# Plot options
chart.options.plot_options = {
    "line": {"lineWidth": 4, "marker": {"enabled": False}, "states": {"hover": {"enabled": False}}}
}

# Add each dendrogram branch as a colored series
for xs, ys, color_key in zip(icoord, dcoord, color_list, strict=True):
    series = LineSeries()
    series.data = [[xs[j], ys[j]] for j in range(4)]
    series.color = color_map.get(color_key, "#306998")
    series.line_width = 4
    series.marker = {"enabled": False}
    series.enable_mouse_tracking = False
    chart.add_series(series)

# Download Highcharts JS for inline embedding
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate JavaScript literal
html_str = chart.to_js_literal()

# Create formatter function for x-axis labels
labels_js = str(ivl).replace("'", '"')
formatter_js = f"""function() {{
    var labels = {labels_js};
    var idx = Math.round((this.value - 5) / 10);
    return (idx >= 0 && idx < labels.length) ? labels[idx] : '';
}}"""

# Inject formatter into xAxis labels configuration
html_str = html_str.replace("rotation: 45,", "rotation: 45,\nformatter: " + formatter_js + ",", 1)

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

# Save HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via headless Chrome
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
