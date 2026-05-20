"""anyplot.ai
datamatrix-basic: Basic Data Matrix 2D Barcode
Library: highcharts | Python 3.13
Quality: 91/100 | Updated: 2026-05-20
"""

import os
import tempfile
import time
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
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - create an 18x18 Data Matrix pattern
content = "SERIAL:12345678"
size = 18

# Create Data Matrix pattern with finder and timing patterns
matrix = np.zeros((size, size), dtype=int)

# L-shaped finder pattern (solid black on left and bottom edges)
matrix[:, 0] = 1  # Left edge - solid black column
matrix[size - 1, :] = 1  # Bottom edge - solid black row

# Alternating (clock) pattern on top and right edges
for i in range(size):
    matrix[0, i] = (i + 1) % 2  # Top edge alternating
    matrix[i, size - 1] = i % 2  # Right edge alternating

# Fill interior with pattern (simulating encoded data)
np.random.seed(42)
data_bits = np.random.randint(0, 2, size=((size - 2) * (size - 2)))
idx = 0
for row in range(1, size - 1):
    for col in range(1, size - 1):
        if idx < len(data_bits):
            matrix[row, col] = data_bits[idx]
            idx += 1

# Prepare heatmap data: [x, y, value] format
rows, cols = matrix.shape
heatmap_data = []
for row in range(rows):
    for col in range(cols):
        y = rows - 1 - row  # Invert row for bottom-to-top display (L-pattern at bottom-left)
        value = int(matrix[row, col])
        heatmap_data.append([col, y, value])

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "heatmap",
    "width": 2400,
    "height": 2400,
    "backgroundColor": PAGE_BG,
    "marginTop": 220,
    "marginBottom": 180,
    "marginLeft": 180,
    "marginRight": 180,
}

chart.options.title = {
    "text": "datamatrix-basic · python · highcharts · anyplot.ai",
    "style": {"fontSize": "66px", "fontWeight": "bold", "color": INK},
}

chart.options.subtitle = {
    "text": f'Data Matrix Encoding: "{content}"',
    "style": {"fontSize": "44px", "color": INK_SOFT},
}

chart.options.x_axis = {
    "title": {"text": None},
    "min": -0.5,
    "max": cols - 0.5,
    "tickLength": 0,
    "labels": {"enabled": False},
    "gridLineWidth": 0,
    "lineWidth": 0,
}

chart.options.y_axis = {
    "title": {"text": None},
    "min": -0.5,
    "max": rows - 0.5,
    "tickLength": 0,
    "labels": {"enabled": False},
    "gridLineWidth": 0,
    "lineWidth": 0,
    "reversed": False,
}

# Barcode cells stay black/white regardless of theme (data, not chrome)
chart.options.color_axis = {"min": 0, "max": 1, "stops": [[0, "#ffffff"], [1, "#000000"]], "visible": False}

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}

series = HeatmapSeries()
series.name = "Data Matrix"
series.data = heatmap_data
series.border_width = 0
series.colsize = 1
series.rowsize = 1
series.tooltip = {"headerFormat": "", "pointFormat": "Cell ({point.x}, {point.y})"}
series.data_labels = {"enabled": False}

chart.add_series(series)

# Load Highcharts JS from local npm package (CDN blocked in CI; install via: npm install highcharts --prefix /tmp/hc-tmp)
HC_NPM = Path("/tmp/hc-tmp/node_modules/highcharts")
highcharts_js = (HC_NPM / "highcharts.js").read_text(encoding="utf-8")
heatmap_js = (HC_NPM / "modules" / "heatmap.js").read_text(encoding="utf-8")

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 2400px; height: 2400px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML artifact (theme-suffixed)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot for PNG artifact
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=2400,2400")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
