""" pyplots.ai
elbow-curve: Elbow Curve for K-Means Clustering
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
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


# Data - simulate elbow curve from K-means clustering
np.random.seed(42)
k_values = list(range(1, 13))

# Simulate realistic inertia values (decreasing with diminishing returns)
# Using exponential decay with noise for realism
base_inertia = 15000
inertia = []
for k in k_values:
    # Exponential decay with elbow around k=4
    decay = base_inertia * np.exp(-0.4 * (k - 1))
    noise = np.random.uniform(-200, 200)
    inertia.append(max(500, decay + noise))

# Optimal elbow point at k=4
optimal_k = 4
optimal_inertia = inertia[optimal_k - 1]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 250,
    "marginLeft": 250,
    "marginTop": 120,
    "marginRight": 100,
}

# Title
chart.options.title = {
    "text": "elbow-curve \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# X-axis configuration
chart.options.x_axis = {
    "title": {"text": "Number of Clusters (k)", "style": {"fontSize": "42px"}, "margin": 30},
    "labels": {"style": {"fontSize": "32px"}, "y": 40},
    "categories": [str(k) for k in k_values],
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "gridLineDashStyle": "Dash",
    "tickInterval": 1,
}

# Y-axis configuration
chart.options.y_axis = {
    "title": {"text": "Inertia (Within-cluster Sum of Squares)", "style": {"fontSize": "42px"}, "margin": 40},
    "labels": {"style": {"fontSize": "32px"}, "x": -15},
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "gridLineDashStyle": "Dash",
    "min": 0,
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "32px"},
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -80,
    "y": 80,
}

# Plot options
chart.options.plot_options = {
    "line": {"lineWidth": 5, "marker": {"enabled": True, "radius": 14, "symbol": "circle"}},
    "scatter": {"marker": {"radius": 20, "symbol": "diamond"}},
}

# Main elbow curve line series
line_series = LineSeries()
line_series.name = "Inertia"
line_series.data = [[i, round(v, 1)] for i, v in enumerate(inertia)]
line_series.color = "#306998"
line_series.marker = {"fillColor": "#306998", "lineWidth": 3, "lineColor": "#ffffff"}
chart.add_series(line_series)

# Optimal point marker
optimal_series = ScatterSeries()
optimal_series.name = f"Optimal k = {optimal_k}"
optimal_series.data = [[optimal_k - 1, round(optimal_inertia, 1)]]
optimal_series.color = "#FFD43B"
optimal_series.marker = {
    "radius": 24,
    "symbol": "diamond",
    "fillColor": "#FFD43B",
    "lineWidth": 4,
    "lineColor": "#306998",
}
chart.add_series(optimal_series)

# Add annotation for elbow point
chart.options.annotations = [
    {
        "labels": [
            {
                "point": {"x": optimal_k - 1, "y": optimal_inertia, "xAxis": 0, "yAxis": 0},
                "text": f"Elbow Point (k={optimal_k})",
                "style": {"fontSize": "32px", "fontWeight": "bold"},
                "backgroundColor": "rgba(255, 212, 59, 0.9)",
                "borderColor": "#306998",
                "borderWidth": 3,
                "borderRadius": 8,
                "padding": 15,
                "y": -60,
            }
        ]
    }
]

# Tooltip
chart.options.tooltip = {
    "style": {"fontSize": "24px"},
    "headerFormat": "<b>k = {point.key}</b><br/>",
    "pointFormat": "Inertia: {point.y:.1f}",
}

# Download Highcharts JS (required for headless Chrome)
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Download annotations module for elbow point label
annotations_url = "https://code.highcharts.com/modules/annotations.js"
with urllib.request.urlopen(annotations_url, timeout=30) as response:
    annotations_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{annotations_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
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
chrome_options.add_argument("--window-size=4800,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

# Also save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

Path(temp_path).unlink()
