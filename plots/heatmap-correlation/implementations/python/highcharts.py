""" pyplots.ai
heatmap-correlation: Correlation Matrix Heatmap
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
from highcharts_core.options.series.heatmap import HeatmapSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Financial metrics correlation matrix
np.random.seed(42)
variables = ["Revenue", "Profit", "Expenses", "Growth", "ROI", "Debt", "Assets"]
n_vars = len(variables)

# Create realistic correlation matrix
base_corr = np.array(
    [
        [1.00, 0.85, 0.72, 0.45, 0.68, -0.32, 0.78],  # Revenue
        [0.85, 1.00, 0.35, 0.52, 0.89, -0.45, 0.62],  # Profit
        [0.72, 0.35, 1.00, 0.15, -0.28, 0.55, 0.48],  # Expenses
        [0.45, 0.52, 0.15, 1.00, 0.72, -0.18, 0.25],  # Growth
        [0.68, 0.89, -0.28, 0.72, 1.00, -0.58, 0.42],  # ROI
        [-0.32, -0.45, 0.55, -0.18, -0.58, 1.00, -0.22],  # Debt
        [0.78, 0.62, 0.48, 0.25, 0.42, -0.22, 1.00],  # Assets
    ]
)

# Prepare data for heatmap (lower triangle only to reduce redundancy)
heatmap_data = []
for i in range(n_vars):
    for j in range(i + 1):  # Lower triangle including diagonal
        heatmap_data.append([j, n_vars - 1 - i, round(base_corr[i, j], 2)])

# Variable labels for axes (reversed for y-axis)
reversed_vars = list(reversed(variables))

# Create chart using highcharts-core Python library
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "heatmap",
    "width": 3600,
    "height": 3600,
    "backgroundColor": "#ffffff",
    "marginTop": 180,
    "marginBottom": 300,
    "marginLeft": 280,
    "marginRight": 220,
}

# Title
chart.options.title = {
    "text": "heatmap-correlation · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle
chart.options.subtitle = {
    "text": "Financial Metrics Correlation Matrix",
    "style": {"fontSize": "32px", "color": "#666666"},
}

# X-axis
chart.options.x_axis = {
    "categories": variables,
    "title": None,
    "labels": {"style": {"fontSize": "28px"}, "rotation": 315},
}

# Y-axis
chart.options.y_axis = {
    "categories": reversed_vars,
    "title": None,
    "labels": {"style": {"fontSize": "28px"}},
    "reversed": False,
}

# Color axis - using colorblind-friendly blue-white-orange diverging palette
chart.options.color_axis = {
    "min": -1,
    "max": 1,
    "stops": [
        [0, "#306998"],  # Python Blue for negative correlations
        [0.5, "#FFFFFF"],  # White for zero
        [1, "#E07020"],  # Orange for positive correlations (colorblind-friendly)
    ],
    "labels": {"style": {"fontSize": "24px"}},
    "tickInterval": 0.5,
}

# Legend
chart.options.legend = {
    "align": "right",
    "layout": "vertical",
    "verticalAlign": "middle",
    "symbolHeight": 600,
    "itemStyle": {"fontSize": "24px"},
}

# Tooltip
chart.options.tooltip = {
    "formatter": """function() {
        var xCat = this.series.xAxis.categories[this.point.x];
        var yCat = this.series.yAxis.categories[this.point.y];
        return '<b>' + yCat + ' vs ' + xCat + '</b><br>Correlation: <b>' +
               Highcharts.numberFormat(this.point.value, 2) + '</b>';
    }""",
    "style": {"fontSize": "20px"},
}

# Create and add series
series = HeatmapSeries()
series.name = "Correlation"
series.data = heatmap_data
series.border_width = 1
series.border_color = "#ffffff"
series.data_labels = {
    "enabled": True,
    "formatter": """function() {
        return Highcharts.numberFormat(this.point.value, 2);
    }""",
    "style": {"fontSize": "32px", "fontWeight": "bold", "textOutline": "2px white"},
}

chart.add_series(series)

# Download Highcharts JS and Heatmap module
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

heatmap_url = "https://code.highcharts.com/modules/heatmap.js"
with urllib.request.urlopen(heatmap_url, timeout=30) as response:
    heatmap_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="margin:0; background-color: #ffffff;">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save the HTML file for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Configure headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=3600,3600")

# Take screenshot
driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
