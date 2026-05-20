"""anyplot.ai
crossword-basic: Crossword Puzzle Grid
Library: highcharts-core | Python 3.13
Quality: 91/100 | Updated: 2026-05-20
"""

import json
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


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - 15x15 crossword grid with 180-degree rotational symmetry
np.random.seed(42)
grid_size = 15

grid = np.zeros((grid_size, grid_size), dtype=int)

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

for r, c in black_cells:
    grid[r, c] = 1
    grid[grid_size - 1 - r, grid_size - 1 - c] = 1

# Calculate clue numbers
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

# Heatmap data: [col, flipped_row, cell_value]
heatmap_data = []
for r in range(grid_size):
    for c in range(grid_size):
        heatmap_data.append([c, grid_size - 1 - r, int(grid[r, c])])

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "heatmap",
    "width": 2400,
    "height": 2400,
    "backgroundColor": PAGE_BG,
    "marginTop": 140,
    "marginBottom": 130,
    "marginLeft": 150,
    "marginRight": 80,
}

chart.options.title = {
    "text": "crossword-basic · python · highcharts · anyplot.ai",
    "style": {"fontSize": "66px", "fontWeight": "bold", "color": INK},
}

# White = entry cells, black = blocked cells (data colors are theme-independent)
chart.options.color_axis = {"min": 0, "max": 1, "stops": [[0, "#FFFFFF"], [1, "#000000"]], "visible": False}

row_labels = [chr(65 + i) for i in range(grid_size)]

chart.options.x_axis = {
    "categories": [str(i + 1) for i in range(grid_size)],
    "title": {"text": "Column", "style": {"fontSize": "56px", "color": INK}},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "lineWidth": 2,
    "lineColor": INK,
    "tickWidth": 0,
    "tickLength": 0,
}

chart.options.y_axis = {
    "categories": list(reversed(row_labels)),
    "title": {"text": "Row", "style": {"fontSize": "56px", "color": INK}},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "lineWidth": 2,
    "lineColor": INK,
    "tickWidth": 0,
    "tickLength": 0,
    "reversed": False,
}

chart.options.legend = {"enabled": False}

series = HeatmapSeries()
series.name = "Grid"
series.data = heatmap_data
series.border_width = 2
series.border_color = "#000000"
series.data_labels = {"enabled": False}

chart.add_series(series)

chart.options.plot_options = {
    "heatmap": {
        "borderWidth": 3,
        "borderColor": "#000000",
        "dataLabels": {"enabled": False},
        "colsize": 1,
        "rowsize": 1,
    }
}

# Download Highcharts JS and heatmap module (browser UA required to avoid 403)
_ua = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.highcharts.com/",
}
_js_assets = {}
for _url in ["https://code.highcharts.com/highcharts.js", "https://code.highcharts.com/modules/heatmap.js"]:
    _req = urllib.request.Request(_url, headers=_ua)
    with urllib.request.urlopen(_req, timeout=30) as _r:
        _js_assets[_url] = _r.read().decode("utf-8")

highcharts_js = _js_assets["https://code.highcharts.com/highcharts.js"]
heatmap_js = _js_assets["https://code.highcharts.com/modules/heatmap.js"]

# Clue positions as JSON for JS renderer (avoids deprecated annotations module)
clue_positions_json = json.dumps([{"r": r, "c": c, "num": num} for (r, c), num in numbers.items()])

html_str = chart.to_js_literal()

# Render clue numbers via Highcharts SVG renderer — no annotations module needed
# Uses window.load so it fires after DOMContentLoaded (where Highcharts initializes)
clue_script = f"""
window.addEventListener('load', function() {{
    var chart = Highcharts.charts[0];
    if (!chart) {{ return; }}
    var clues = {clue_positions_json};
    var cellW = chart.plotWidth / {grid_size};
    var cellH = chart.plotHeight / {grid_size};
    clues.forEach(function(p) {{
        var x = chart.plotLeft + p.c * cellW + cellW * 0.06;
        var y = chart.plotTop + p.r * cellH + cellH * 0.34;
        chart.renderer.text(String(p.num), x, y)
            .css({{ fontSize: '44px', fontWeight: 'bold', color: '#000000' }})
            .attr({{ zIndex: 10 }})
            .add();
    }});
}});
"""

html_inline = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 2400px; height: 2400px;"></div>
    <script>{html_str}</script>
    <script>{clue_script}</script>
</body>
</html>"""

# HTML artifact with CDN for interactive use
html_cdn = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/heatmap.js"></script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
    <script>{clue_script}</script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_cdn)

# Write temp file and screenshot for PNG artifact
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_inline)
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
