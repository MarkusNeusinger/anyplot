"""anyplot.ai
heatmap-correlation: Correlation Matrix Heatmap
Library: highcharts | Python 3.13
Quality: pending | Created: 2025-12-26
"""

import os
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


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

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
    "backgroundColor": PAGE_BG,
    "marginTop": 180,
    "marginBottom": 300,
    "marginLeft": 280,
    "marginRight": 220,
}

# Title
chart.options.title = {
    "text": "heatmap-correlation · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK},
}

# X-axis
chart.options.x_axis = {
    "categories": variables,
    "title": None,
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}, "rotation": 315},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
}

# Y-axis
chart.options.y_axis = {
    "categories": reversed_vars,
    "title": None,
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "reversed": False,
}

# Color axis - using colorblind-friendly blue-white-orange diverging palette
chart.options.color_axis = {
    "min": -1,
    "max": 1,
    "stops": [
        [0, "#306998"],  # Blue for negative correlations
        [0.5, PAGE_BG],  # White/dark for zero (adaptive)
        [1, "#E07020"],  # Orange for positive correlations
    ],
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "tickInterval": 0.5,
    "title": {"text": "Correlation", "style": {"fontSize": "18px", "color": INK}},
}

# Legend
chart.options.legend = {
    "align": "right",
    "layout": "vertical",
    "verticalAlign": "middle",
    "symbolHeight": 600,
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}

# Tooltip
chart.options.tooltip = {
    "formatter": """function() {
        var xCat = this.series.xAxis.categories[this.point.x];
        var yCat = this.series.yAxis.categories[this.point.y];
        return '<b>' + yCat + ' vs ' + xCat + '</b><br>Correlation: <b>' +
               Highcharts.numberFormat(this.point.value, 2) + '</b>';
    }""",
    "style": {"fontSize": "16px", "color": INK},
}

# Create and add series
series = HeatmapSeries()
series.name = "Correlation"
series.data = heatmap_data
series.border_width = 1
series.border_color = PAGE_BG
series.data_labels = {
    "enabled": True,
    "formatter": """function() {
        return Highcharts.numberFormat(this.point.value, 2);
    }""",
    "style": {"fontSize": "18px", "fontWeight": "bold", "color": INK, "textOutline": f"1px {PAGE_BG}"},
}

chart.add_series(series)

# Download Highcharts JS and Heatmap module from jsDelivr CDN
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js"
req = urllib.request.Request(
    highcharts_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

heatmap_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/modules/heatmap.js"
req = urllib.request.Request(
    heatmap_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
)
with urllib.request.urlopen(req, timeout=30) as response:
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
<body style="margin:0; background-color: {PAGE_BG};">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save the HTML file for interactive viewing
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
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
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
