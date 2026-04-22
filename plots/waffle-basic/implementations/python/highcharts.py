""" pyplots.ai
waffle-basic: Basic Waffle Chart
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-24
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


# Data - Market share distribution (sums to 100%)
categories = ["Product A", "Product B", "Product C", "Product D"]
values = [42, 28, 18, 12]  # Percentages that sum to 100

# Colors - Python Blue and Yellow first, then colorblind-safe additions
colors = ["#306998", "#FFD43B", "#4DAF4A", "#E377C2"]

# Create 10x10 grid (100 squares, each = 1%)
grid_size = 10
total_squares = grid_size * grid_size

# Build the grid data - fill squares by category
grid = np.zeros(total_squares, dtype=int)
start_idx = 0
for i, val in enumerate(values):
    grid[start_idx : start_idx + val] = i
    start_idx += val

# Reshape to 10x10 grid
grid = grid.reshape((grid_size, grid_size))

# Build scatter data grouped by category
scatter_data = {i: [] for i in range(len(categories))}
for row in range(grid_size):
    for col in range(grid_size):
        category_idx = int(grid[row, col])
        scatter_data[category_idx].append({"x": col, "y": row})

# Create chart with container
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart settings - square plot area for waffle grid
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginRight": 550,  # Space for legend
    "marginLeft": 600,  # Center the square grid
    "marginTop": 150,
    "marginBottom": 150,
    "plotBackgroundColor": "#ffffff",
}

# Title
chart.options.title = {
    "text": "waffle-basic \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# X-axis - hidden but defines grid
chart.options.x_axis = {"min": -0.5, "max": grid_size - 0.5, "visible": False, "gridLineWidth": 0}

# Y-axis - hidden but defines grid
chart.options.y_axis = {"min": -0.5, "max": grid_size - 0.5, "visible": False, "gridLineWidth": 0}

# Legend
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "middle",
    "layout": "vertical",
    "itemStyle": {"fontSize": "32px"},
    "symbolRadius": 8,
    "symbolWidth": 50,
    "symbolHeight": 50,
    "itemMarginBottom": 25,
}

# Tooltip
chart.options.tooltip = {"enabled": False}

# Create scatter series for each category with square markers
for i, cat in enumerate(categories):
    series = ScatterSeries()
    series.data = scatter_data[i]
    series.name = f"{cat} ({values[i]}%)"
    series.color = colors[i]
    series.marker = {
        "symbol": "square",
        "radius": 95,  # Large square markers for waffle effect
        "lineWidth": 4,
        "lineColor": "#ffffff",
    }
    chart.add_series(series)

# Plot options
chart.options.plot_options = {"scatter": {"marker": {"states": {"hover": {"enabled": False}}}}}

# Download Highcharts JS (scatter doesn't need extra modules)
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
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

# Write temp HTML
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save plot.html for interactive version
Path("plot.html").write_text(html_content, encoding="utf-8")

# Take screenshot with headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
