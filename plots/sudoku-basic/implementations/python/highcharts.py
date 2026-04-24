""" anyplot.ai
sudoku-basic: Basic Sudoku Grid
Library: highcharts unknown | Python 3.14.4
Quality: 89/100 | Updated: 2026-04-24
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data: partially filled Sudoku puzzle (0 = empty cell)
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

# Build grid lines as native highcharts plotLines:
# thin lines for cell boundaries, thick lines for 3x3 box boundaries
thin_positions = [1, 2, 4, 5, 7, 8]
thick_positions = [0, 3, 6, 9]

axis_plot_lines = [{"value": v, "width": 2, "color": INK_SOFT, "zIndex": 3} for v in thin_positions] + [
    {"value": v, "width": 8, "color": INK, "zIndex": 5} for v in thick_positions
]

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 3600,
    "height": 3600,
    "backgroundColor": PAGE_BG,
    "plotBackgroundColor": PAGE_BG,
    "plotBorderWidth": 0,
    "margin": [180, 120, 60, 120],
    "style": {"fontFamily": "Arial, sans-serif"},
}

chart.options.title = {
    "text": "sudoku-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "56px", "fontWeight": "bold", "color": INK, "fontFamily": "Arial, sans-serif"},
    "margin": 60,
}

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}
chart.options.tooltip = {"enabled": False}

chart.options.x_axis = [
    {
        "min": 0,
        "max": 9,
        "tickInterval": 1,
        "gridLineWidth": 0,
        "lineWidth": 0,
        "tickLength": 0,
        "labels": {"enabled": False},
        "title": {"text": ""},
        "plotLines": axis_plot_lines,
        "startOnTick": True,
        "endOnTick": True,
    }
]

chart.options.y_axis = [
    {
        "min": 0,
        "max": 9,
        "tickInterval": 1,
        "gridLineWidth": 0,
        "lineWidth": 0,
        "tickLength": 0,
        "labels": {"enabled": False},
        "title": {"text": ""},
        "plotLines": axis_plot_lines,
        "reversed": True,
        "startOnTick": True,
        "endOnTick": True,
    }
]

# Numbers rendered as invisible scatter points with data labels centered per cell
data_points = []
for row in range(9):
    for col in range(9):
        value = grid[row][col]
        if value != 0:
            data_points.append(
                {
                    "x": col + 0.5,
                    "y": row + 0.5,
                    "dataLabels": {
                        "enabled": True,
                        "format": str(value),
                        "align": "center",
                        "verticalAlign": "middle",
                        "style": {
                            "fontSize": "96px",
                            "fontWeight": "bold",
                            "fontFamily": "Arial, sans-serif",
                            "textOutline": "none",
                            "color": INK,
                        },
                    },
                }
            )

series = ScatterSeries()
series.data = data_points
series.name = "Numbers"
series.marker = {"enabled": False}
series.enable_mouse_tracking = False
chart.add_series(series)

# Download Highcharts JS (embed inline for headless Chrome)
highcharts_url = "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.4.8/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

html_str = chart.to_js_literal()

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; padding:0; background:{PAGE_BG}; overflow:hidden;">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via headless Chrome
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=3600,3600")

driver = webdriver.Chrome(options=chrome_options)
# Force exact viewport dimensions (headless outer vs inner can differ)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3600, "height": 3600, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
