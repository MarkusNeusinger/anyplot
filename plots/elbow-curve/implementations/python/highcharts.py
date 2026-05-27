""" anyplot.ai
elbow-curve: Elbow Curve for K-Means Clustering
Library: highcharts unknown | Python 3.13.13
Quality: 95/100 | Updated: 2026-05-10
"""

import os
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


# Theme-adaptive chrome tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

BRAND = "#009E73"  # Okabe-Ito position 1
SECONDARY = "#C475FD"  # Okabe-Ito position 2

# Data - simulate elbow curve from K-means clustering
np.random.seed(42)
k_values = list(range(1, 13))

# Simulate realistic inertia values (decreasing with diminishing returns)
base_inertia = 15000
inertia = []
for k in k_values:
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
    "backgroundColor": PAGE_BG,
    "marginBottom": 250,
    "marginLeft": 250,
    "marginTop": 120,
    "marginRight": 100,
    "style": {"color": INK},
}

# Title
chart.options.title = {
    "text": "elbow-curve · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK},
}

# X-axis configuration
chart.options.x_axis = {
    "title": {"text": "Number of Clusters (k)", "style": {"fontSize": "22px", "color": INK}, "margin": 30},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}, "y": 40},
    "categories": [str(k) for k in k_values],
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "tickInterval": 1,
}

# Y-axis configuration
chart.options.y_axis = {
    "title": {
        "text": "Inertia (Within-cluster Sum of Squares)",
        "style": {"fontSize": "22px", "color": INK},
        "margin": 40,
    },
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}, "x": -15},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "min": 0,
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -80,
    "y": 80,
}

# Plot options
chart.options.plot_options = {
    "line": {"lineWidth": 3, "marker": {"enabled": True, "radius": 8}},
    "scatter": {"marker": {"radius": 8}},
}

# Main elbow curve line series
line_series = LineSeries()
line_series.name = "Inertia"
line_series.data = [[i, round(v, 1)] for i, v in enumerate(inertia)]
line_series.color = BRAND
line_series.marker = {"fillColor": BRAND, "lineWidth": 2, "lineColor": PAGE_BG}
chart.add_series(line_series)

# Optimal point marker
optimal_series = ScatterSeries()
optimal_series.name = f"Optimal k = {optimal_k}"
optimal_series.data = [[optimal_k - 1, round(optimal_inertia, 1)]]
optimal_series.color = SECONDARY
optimal_series.marker = {"radius": 10, "fillColor": SECONDARY, "lineWidth": 2, "lineColor": PAGE_BG}
chart.add_series(optimal_series)

# Add annotation for elbow point
chart.options.annotations = [
    {
        "labels": [
            {
                "point": {"x": optimal_k - 1, "y": optimal_inertia, "xAxis": 0, "yAxis": 0},
                "text": f"Elbow Point (k={optimal_k})",
                "style": {"fontSize": "18px", "color": INK},
                "backgroundColor": ELEVATED_BG,
                "borderColor": INK_SOFT,
                "borderWidth": 1,
                "borderRadius": 8,
                "padding": 15,
                "y": -60,
            }
        ]
    }
]

# Tooltip
chart.options.tooltip = {
    "style": {"fontSize": "18px", "color": INK},
    "headerFormat": "<b>k = {point.key}</b><br/>",
    "pointFormat": "Inertia: {point.y:.1f}",
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
}

# Download Highcharts JS from jsDelivr CDN
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js"
req = urllib.request.Request(
    highcharts_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Download annotations module
annotations_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/modules/annotations.js"
req = urllib.request.Request(
    annotations_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
)
with urllib.request.urlopen(req, timeout=30) as response:
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
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML artifact
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
