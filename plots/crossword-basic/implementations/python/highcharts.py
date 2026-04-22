""" pyplots.ai
crossword-basic: Crossword Puzzle Grid
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-15
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


# Data - Create a 15x15 crossword grid with 180-degree rotational symmetry
np.random.seed(42)
grid_size = 15

# Generate symmetric black cell pattern (1 = black/blocked, 0 = white/entry)
grid = np.zeros((grid_size, grid_size), dtype=int)

# Define black cells for one half (will be mirrored for symmetry)
black_cells = [
    (0, 4),
    (0, 10),
    (1, 4),
    (1, 10),
    (2, 7),
    (3, 0),
    (3, 5),
    (3, 9),
    (4, 3),
    (4, 8),
    (4, 13),
    (5, 6),
    (5, 11),
    (6, 1),
    (6, 2),
    (6, 10),
    (6, 14),
    (7, 7),
]

# Place black cells with 180-degree symmetry
for r, c in black_cells:
    grid[r, c] = 1
    grid[grid_size - 1 - r, grid_size - 1 - c] = 1

# Calculate clue numbers - number cells that start words (across or down)
numbers = {}
clue_num = 1
for r in range(grid_size):
    for c in range(grid_size):
        if grid[r, c] == 1:
            continue
        starts_across = (c == 0 or grid[r, c - 1] == 1) and (c < grid_size - 1 and grid[r, c + 1] == 0)
        starts_down = (r == 0 or grid[r - 1, c] == 1) and (r < grid_size - 1 and grid[r + 1, c] == 0)
        if starts_across or starts_down:
            numbers[(r, c)] = clue_num
            clue_num += 1

# Prepare heatmap data - black cells = 1, white cells = 0
heatmap_data = []
for r in range(grid_size):
    for c in range(grid_size):
        heatmap_data.append([c, grid_size - 1 - r, int(grid[r, c])])

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "heatmap",
    "width": 3600,
    "height": 3600,
    "backgroundColor": "#ffffff",
    "marginTop": 120,
    "marginBottom": 100,
    "marginLeft": 100,
    "marginRight": 100,
}

# Title
chart.options.title = {
    "text": "crossword-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Remove colorAxis legend
chart.options.color_axis = {"min": 0, "max": 1, "stops": [[0, "#ffffff"], [1, "#000000"]], "visible": False}

# X-axis (columns 1-15)
chart.options.x_axis = {
    "categories": [str(i + 1) for i in range(grid_size)],
    "title": {"text": None},
    "labels": {"style": {"fontSize": "28px"}},
    "lineWidth": 2,
    "lineColor": "#000000",
    "tickWidth": 0,
    "tickLength": 0,
    "startOnTick": False,
    "endOnTick": False,
}

# Y-axis (rows A-O)
row_labels = [chr(65 + i) for i in range(grid_size)]
chart.options.y_axis = {
    "categories": list(reversed(row_labels)),
    "title": {"text": None},
    "labels": {"style": {"fontSize": "28px"}},
    "lineWidth": 2,
    "lineColor": "#000000",
    "tickWidth": 0,
    "tickLength": 0,
    "startOnTick": False,
    "endOnTick": False,
    "reversed": False,
}

# Legend disabled
chart.options.legend = {"enabled": False}

# Create heatmap series
series = HeatmapSeries()
series.name = "Grid"
series.data = heatmap_data
series.border_width = 2
series.border_color = "#000000"
series.data_labels = {"enabled": False}

chart.add_series(series)

# Add clue numbers as annotations
annotations = []
for (r, c), num in numbers.items():
    annotations.append(
        {
            "point": {"x": c, "y": grid_size - 1 - r, "xAxis": 0, "yAxis": 0},
            "text": str(num),
            "align": "left",
            "verticalAlign": "top",
            "x": -85,
            "y": -75,
            "style": {"fontSize": "28px", "fontWeight": "bold", "color": "#000000"},
            "backgroundColor": "transparent",
            "borderWidth": 0,
            "shadow": False,
        }
    )

chart.options.annotations = [{"labels": annotations, "draggable": ""}]

# Plot options for heatmap - ensure all cells have visible borders
chart.options.plot_options = {
    "heatmap": {
        "borderWidth": 3,
        "borderColor": "#333333",
        "dataLabels": {"enabled": False},
        "colsize": 1,
        "rowsize": 1,
    }
}

# Download Highcharts JS and heatmap module
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

heatmap_url = "https://code.highcharts.com/modules/heatmap.js"
with urllib.request.urlopen(heatmap_url, timeout=30) as response:
    heatmap_js = response.read().decode("utf-8")

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
    <script>{heatmap_js}</script>
    <script>{annotations_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
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
chrome_options.add_argument("--window-size=3600,3600")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()

# Also save HTML for interactive version
html_output = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/heatmap.js"></script>
    <script src="https://code.highcharts.com/modules/annotations.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_output)
