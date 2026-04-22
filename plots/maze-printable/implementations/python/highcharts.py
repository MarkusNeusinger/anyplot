""" pyplots.ai
maze-printable: Printable Maze Puzzle
Library: highcharts unknown | Python 3.13.11
Quality: 93/100 | Created: 2026-01-07
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Maze generation using DFS (Depth-First Search) algorithm
np.random.seed(42)

WIDTH = 25  # Number of cells horizontally
HEIGHT = 25  # Number of cells vertically

# Initialize maze grid (walls everywhere)
# 0 = wall, 1 = passage
maze = np.zeros((HEIGHT * 2 + 1, WIDTH * 2 + 1), dtype=int)

# Visited cells tracker
visited = np.zeros((HEIGHT, WIDTH), dtype=bool)


# DFS maze generation (recursive backtracker)
def carve_maze(cy, cx):
    visited[cy, cx] = True
    maze[cy * 2 + 1, cx * 2 + 1] = 1  # Mark cell as passage

    # Randomize direction order
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    np.random.shuffle(directions)

    for dy, dx in directions:
        ny, nx = cy + dy, cx + dx
        if 0 <= ny < HEIGHT and 0 <= nx < WIDTH and not visited[ny, nx]:
            # Carve wall between current and next cell
            maze[cy * 2 + 1 + dy, cx * 2 + 1 + dx] = 1
            carve_maze(ny, nx)


# Generate maze starting from top-left
carve_maze(0, 0)

# Grid dimensions
maze_cols = WIDTH * 2 + 1
maze_rows = HEIGHT * 2 + 1

# Create heatmap data: [x, y, value] where value is 0 for passage, 1 for wall
heatmap_data = []
for row in range(maze_rows):
    for col in range(maze_cols):
        # value: 1 = wall (black), 0 = passage (white)
        value = 0 if maze[row, col] == 1 else 1
        heatmap_data.append([col, row, value])

# Create the chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for square printable maze
chart.options.chart = {
    "type": "heatmap",
    "width": 3600,
    "height": 3600,
    "backgroundColor": "#ffffff",
    "spacing": [100, 60, 60, 60],
    "animation": False,
}

# Title
chart.options.title = {
    "text": "maze-printable · highcharts · pyplots.ai",
    "style": {"fontSize": "56px", "fontWeight": "bold", "color": "#000000"},
    "y": 50,
}

# Subtitle with instructions
chart.options.subtitle = {
    "text": "Find the path from S (Start) to G (Goal)",
    "style": {"fontSize": "36px", "color": "#333333"},
    "y": 90,
}

# Hide legend
chart.options.legend = {"enabled": False}

# Configure axes
chart.options.x_axis = {"min": -0.5, "max": maze_cols - 0.5, "visible": False, "gridLineWidth": 0}

chart.options.y_axis = {"min": -0.5, "max": maze_rows - 0.5, "visible": False, "gridLineWidth": 0, "reversed": True}

# Color axis for heatmap (black for walls, white for passages)
chart.options.color_axis = {"min": 0, "max": 1, "stops": [[0, "#ffffff"], [1, "#000000"]], "visible": False}

# Plot options
chart.options.plot_options = {
    "series": {"animation": False, "enableMouseTracking": False, "states": {"inactive": {"opacity": 1}}},
    "heatmap": {"borderWidth": 0, "colsize": 1, "rowsize": 1},
}

# Start position (top-left cell passage at grid position 1,1)
start_x = 1
start_y = 1

# Goal position (bottom-right cell passage)
goal_x = WIDTH * 2 - 1
goal_y = HEIGHT * 2 - 1

# Heatmap series for maze walls
maze_series = {"type": "heatmap", "name": "Maze", "data": heatmap_data, "borderWidth": 0, "colsize": 1, "rowsize": 1}

# Start marker series
start_series = {
    "type": "scatter",
    "name": "Start",
    "data": [{"x": start_x, "y": start_y}],
    "color": "#306998",
    "marker": {"symbol": "triangle", "radius": 20, "lineWidth": 3, "lineColor": "#000000"},
    "dataLabels": {
        "enabled": True,
        "format": "S",
        "style": {"fontSize": "42px", "fontWeight": "bold", "color": "#306998", "textOutline": "3px white"},
        "y": -30,
    },
    "zIndex": 10,
}

# Goal marker series
goal_series = {
    "type": "scatter",
    "name": "Goal",
    "data": [{"x": goal_x, "y": goal_y}],
    "color": "#FFD43B",
    "marker": {"symbol": "diamond", "radius": 20, "lineWidth": 3, "lineColor": "#000000"},
    "dataLabels": {
        "enabled": True,
        "format": "G",
        "style": {"fontSize": "42px", "fontWeight": "bold", "color": "#B8860B", "textOutline": "3px white"},
        "y": -30,
    },
    "zIndex": 10,
}

# Build the options with series
chart.options.series = [maze_series, start_series, goal_series]

# Credits
chart.options.credits = {"enabled": False}

# Download Highcharts JS and heatmap module
highcharts_url = "https://code.highcharts.com/highcharts.js"
heatmap_url = "https://code.highcharts.com/modules/heatmap.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

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

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    interactive_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>maze-printable · highcharts · pyplots.ai</title>
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/heatmap.js"></script>
</head>
<body style="margin:0; background-color: #ffffff;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(interactive_html)

# Setup Chrome for screenshot
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=3600,3600")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
