""" pyplots.ai
sudoku-basic: Basic Sudoku Grid
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.scatter import ScatterSeries
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Example Sudoku puzzle with starting numbers (0 = empty)
grid = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 3600,
    "height": 3600,
    "backgroundColor": "#ffffff",
    "plotBorderWidth": 0,
    "margin": [120, 100, 100, 100],
}

chart.options.title = {
    "text": "sudoku-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "56px", "fontWeight": "bold", "fontFamily": "Arial, sans-serif"},
    "y": 60,
}

# Disable legend
chart.options.legend = {"enabled": False}

# Configure axes for 9x9 grid
chart.options.x_axis = {
    "min": 0,
    "max": 9,
    "tickInterval": 1,
    "gridLineWidth": 0,
    "lineWidth": 0,
    "labels": {"enabled": False},
    "title": {"text": None},
}

chart.options.y_axis = {
    "min": 0,
    "max": 9,
    "tickInterval": 1,
    "gridLineWidth": 0,
    "lineWidth": 0,
    "labels": {"enabled": False},
    "title": {"text": None},
    "reversed": True,
}

# Prepare data points for numbers
data_points = []
for row in range(9):
    for col in range(9):
        value = grid[row][col]
        if value != 0:
            data_points.append(
                {
                    "x": col + 0.5,
                    "y": row + 0.5,
                    "name": str(value),
                    "marker": {"radius": 0},
                    "dataLabels": {
                        "enabled": True,
                        "format": str(value),
                        "style": {
                            "fontSize": "72px",
                            "fontWeight": "bold",
                            "fontFamily": "Arial, sans-serif",
                            "textOutline": "none",
                        },
                        "color": "#000000",
                    },
                }
            )

# Create scatter series for numbers
series = ScatterSeries()
series.data = data_points
series.name = "Numbers"
series.enable_mouse_tracking = False
chart.add_series(series)

# Disable tooltip
chart.options.tooltip = {"enabled": False}

# Export to PNG via Selenium
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with grid lines drawn via CSS/HTML
html_str = chart.to_js_literal()

# Build grid lines HTML - thin lines for cells, thick lines for 3x3 boxes
cell_size = 378  # (3600 - 200) / 9 ~ 378px per cell (accounting for margins)
offset_x = 100  # Left margin
offset_y = 120  # Top margin

grid_lines_html = ""

# Thin lines for all cells (light gray)
for i in range(10):
    # Vertical lines
    x = offset_x + i * cell_size
    grid_lines_html += f'<div style="position:absolute; left:{x}px; top:{offset_y}px; width:2px; height:{cell_size * 9}px; background:#999999;"></div>'
    # Horizontal lines
    y = offset_y + i * cell_size
    grid_lines_html += f'<div style="position:absolute; left:{offset_x}px; top:{y}px; width:{cell_size * 9}px; height:2px; background:#999999;"></div>'

# Thick lines for 3x3 boxes (black)
for i in range(4):
    # Vertical lines
    x = offset_x + i * 3 * cell_size
    grid_lines_html += f'<div style="position:absolute; left:{x - 2}px; top:{offset_y}px; width:6px; height:{cell_size * 9}px; background:#000000;"></div>'
    # Horizontal lines
    y = offset_y + i * 3 * cell_size
    grid_lines_html += f'<div style="position:absolute; left:{offset_x}px; top:{y - 2}px; width:{cell_size * 9}px; height:6px; background:#000000;"></div>'

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:#ffffff;">
    <div id="container" style="width: 3600px; height: 3600px; position: relative;"></div>
    {grid_lines_html}
    <script>{html_str}</script>
</body>
</html>"""

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=3700,3700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

# Take screenshot and crop to exact 3600x3600
driver.save_screenshot("plot_temp.png")
driver.quit()

# Crop to exact dimensions using PIL
img = Image.open("plot_temp.png")
img_cropped = img.crop((0, 0, 3600, 3600))
img_cropped.save("plot.png")
Path("plot_temp.png").unlink()

# Also save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    # For the HTML version, use CDN links (works in browser)
    html_interactive = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0; background:#ffffff;">
    <div id="container" style="width: 3600px; height: 3600px; position: relative;"></div>
    {grid_lines_html}
    <script>{html_str}</script>
</body>
</html>"""
    f.write(html_interactive)

Path(temp_path).unlink()
