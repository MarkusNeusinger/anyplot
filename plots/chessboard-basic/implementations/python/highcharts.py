""" anyplot.ai
chessboard-basic: Chess Board Grid Visualization
Library: highcharts unknown | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-17
"""

import os
import tempfile
import time
from pathlib import Path

import requests
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.heatmap import HeatmapSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Chess board colors - adjusted for visibility in both themes
if THEME == "light":
    LIGHT_SQUARE = "#F0D9B5"  # Classic cream
    DARK_SQUARE = "#B58863"  # Classic brown
else:
    LIGHT_SQUARE = "#D4AF77"  # Lighter gold for dark theme
    DARK_SQUARE = "#4A3C28"  # Darker brown for dark theme

# Data - 8x8 chessboard with alternating colors
# Value 0 = light square, 1 = dark square
# Chess convention: h1 (bottom-right from white's perspective) is light
columns = ["a", "b", "c", "d", "e", "f", "g", "h"]
rows = ["1", "2", "3", "4", "5", "6", "7", "8"]

# Generate board data: each point is [col_index, row_index, value]
# Value 0 = light square, 1 = dark square
# Chess convention: h1 = (col=7, row=0): 7+0=7 odd -> light (value=0)
# a1 = (col=0, row=0): 0+0=0 even -> dark (value=1)
board_data = []
for row_idx in range(8):
    for col_idx in range(8):
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
    "backgroundColor": PAGE_BG,
    "marginTop": 120,
    "marginBottom": 200,
    "marginLeft": 150,
    "marginRight": 100,
}

# Title
chart.options.title = {
    "text": "chessboard-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK},
}

# X-axis (columns a-h)
chart.options.x_axis = {
    "categories": columns,
    "title": {"text": None},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineWidth": 2,
    "lineColor": INK_SOFT,
    "tickLength": 0,
    "opposite": False,
}

# Y-axis (rows 1-8)
chart.options.y_axis = {
    "categories": rows,
    "title": {"text": None},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineWidth": 2,
    "lineColor": INK_SOFT,
    "tickLength": 0,
    "reversed": False,
}

# Color axis for light/dark squares
chart.options.color_axis = {"min": 0, "max": 1, "stops": [[0, LIGHT_SQUARE], [1, DARK_SQUARE]], "visible": False}

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
    "style": {"fontSize": "16px", "color": INK},
    "backgroundColor": PAGE_BG,
    "borderColor": INK_SOFT,
}

# Plot options for heatmap
chart.options.plot_options = {"heatmap": {"borderWidth": 2, "borderColor": INK_SOFT, "dataLabels": {"enabled": False}}}

# Create and add series
series = HeatmapSeries()
series.data = board_data
series.name = "Chess Board"

chart.add_series(series)


# Export to PNG via Selenium
# Download Highcharts JS and heatmap module (required for headless Chrome)
def download_js(url, max_retries=3):
    """Download JavaScript from CDN with retries."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(2**attempt)  # Exponential backoff
            else:
                raise


highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
highcharts_js = download_js(highcharts_url)

heatmap_url = "https://cdn.jsdelivr.net/npm/highcharts/modules/heatmap.js"
heatmap_js = download_js(heatmap_url)

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write HTML output
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
chrome_options.add_argument("--window-size=3600,3600")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
