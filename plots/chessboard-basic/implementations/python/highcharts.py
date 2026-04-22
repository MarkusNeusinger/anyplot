""" pyplots.ai
chessboard-basic: Chess Board Grid Visualization
Library: highcharts unknown | Python 3.13.11
Quality: 93/100 | Created: 2026-01-08
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.heatmap import HeatmapSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - 8x8 chessboard with alternating colors
# Value 0 = light square, 1 = dark square
# Chess convention: h1 (bottom-right from white's perspective) is light
columns = ["a", "b", "c", "d", "e", "f", "g", "h"]
rows = ["1", "2", "3", "4", "5", "6", "7", "8"]

# Generate board data: each point is [col_index, row_index, value]
# Value 0 = light square, 1 = dark square
# Chess convention: h1 (bottom-right) is light, a1 (bottom-left) is dark
# col indices: a=0, b=1, ..., h=7
# row indices: 1=0, 2=1, ..., 8=7
# h1 = (col=7, row=0): 7+0=7 odd -> should be light (value=0)
# a1 = (col=0, row=0): 0+0=0 even -> should be dark (value=1)
board_data = []
for row_idx in range(8):
    for col_idx in range(8):
        # (col + row) odd -> light square (0), even -> dark square (1)
        is_light = (col_idx + row_idx) % 2 == 1
        board_data.append([col_idx, row_idx, 0 if is_light else 1])

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for square 1:1 aspect ratio
chart.options.chart = {
    "type": "heatmap",
    "width": 3600,
    "height": 3600,
    "backgroundColor": "#ffffff",
    "marginTop": 120,
    "marginBottom": 200,
    "marginLeft": 150,
    "marginRight": 100,
}

# Title
chart.options.title = {
    "text": "chessboard-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# X-axis (columns a-h)
chart.options.x_axis = {
    "categories": columns,
    "title": {"text": None},
    "labels": {"style": {"fontSize": "36px", "fontWeight": "bold"}},
    "lineWidth": 2,
    "lineColor": "#333333",
    "tickLength": 0,
    "opposite": False,
}

# Y-axis (rows 1-8)
chart.options.y_axis = {
    "categories": rows,
    "title": {"text": None},
    "labels": {"style": {"fontSize": "36px", "fontWeight": "bold"}},
    "lineWidth": 2,
    "lineColor": "#333333",
    "tickLength": 0,
    "reversed": False,
}

# Color axis for light/dark squares
# Classic chess colors: cream (#F0D9B5) for light, brown (#B58863) for dark
chart.options.color_axis = {"min": 0, "max": 1, "stops": [[0, "#F0D9B5"], [1, "#B58863"]], "visible": False}

# Disable legend
chart.options.legend = {"enabled": False}

# Tooltip
chart.options.tooltip = {
    "enabled": True,
    "formatter": """function() {
        var col = this.series.xAxis.categories[this.point.x];
        var row = this.series.yAxis.categories[this.point.y];
        return '<b>' + col + row + '</b>';
    }""",
    "style": {"fontSize": "24px"},
}

# Plot options for heatmap
chart.options.plot_options = {"heatmap": {"borderWidth": 2, "borderColor": "#333333", "dataLabels": {"enabled": False}}}

# Create and add series
series = HeatmapSeries()
series.data = board_data
series.name = "Chess Board"

chart.add_series(series)

# Export to PNG via Selenium
# Download Highcharts JS and heatmap module (required for headless Chrome)
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
<body style="margin:0;">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

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
