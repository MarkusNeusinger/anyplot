""" anyplot.ai
bar-3d-categorical: 3D Bar Chart for Categorical Comparison
Library: highcharts unknown | Python 3.13.13
Quality: 81/100 | Created: 2026-05-15
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import ColumnSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data: quarterly revenue ($ thousands) for five product categories
categories = ["Electronics", "Clothing", "Food", "Sports", "Books"]
quarters = ["Q1", "Q2", "Q3", "Q4"]
sales_data = {
    "Q1": [420, 280, 350, 180, 120],
    "Q2": [380, 310, 370, 210, 130],
    "Q3": [450, 260, 360, 290, 115],
    "Q4": [520, 340, 390, 195, 155],
}

# Plot
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "column",
    "options3d": {
        "enabled": True,
        "alpha": 22,
        "beta": 40,
        "depth": 450,
        "viewDistance": 25,
        "frame": {
            "bottom": {"size": 2, "color": GRID},
            "back": {"size": 1, "color": GRID},
            "side": {"size": 1, "color": GRID},
        },
    },
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 200,
    "marginTop": 140,
    "marginLeft": 200,
    "marginRight": 180,
}

chart.options.title = {
    "text": "bar-3d-categorical · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "color": INK, "fontWeight": "600"},
    "margin": 20,
}

chart.options.subtitle = {
    "text": "Quarterly Revenue by Product Category ($ thousands) — Electronics leads across all quarters; Q4 peaks in every segment",
    "style": {"fontSize": "20px", "color": INK_SOFT},
    "margin": 30,
}

chart.options.x_axis = {
    "categories": categories,
    "title": {"text": "Product Category", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
}

chart.options.y_axis = {
    "title": {"text": "Revenue ($ thousands)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "min": 0,
}

chart.options.plot_options = {
    "column": {
        "depth": 45,
        "grouping": False,
        "groupZPadding": 12,
        "borderColor": "rgba(255,255,255,0.20)",
        "borderWidth": 1,
        "dataLabels": {
            "enabled": True,
            "format": "{point.y}",
            "style": {"fontSize": "18px", "color": INK, "textOutline": "none", "fontWeight": "normal"},
        },
    }
}

chart.options.legend = {
    "itemStyle": {"color": INK_SOFT, "fontSize": "18px"},
    "itemHoverStyle": {"color": INK},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "borderRadius": 4,
    "padding": 16,
    "title": {"text": "Quarter", "style": {"color": INK, "fontSize": "18px", "fontWeight": "600"}},
    "align": "right",
    "verticalAlign": "middle",
    "layout": "vertical",
}

chart.options.colors = IMPRINT

for i, quarter in enumerate(quarters):
    series = ColumnSeries()
    series.name = quarter
    series.data = sales_data[quarter]
    series.color = IMPRINT[i]
    # Emphasize Q4 (peak quarter) with a prominent border to guide the viewer
    if quarter == "Q4":
        series.border_color = INK_SOFT
        series.border_width = 2
    chart.add_series(series)

# Download Highcharts JS files for inline embedding (CDN blocked in headless Chrome)
_HC_URLS = ["https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"]
_HC_3D_URLS = [
    "https://code.highcharts.com/highcharts-3d.js",
    "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts-3d.js",
]

highcharts_js = None
for url in _HC_URLS:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
        break
    except Exception:
        continue
if highcharts_js is None:
    raise RuntimeError("Failed to download highcharts.js from all mirrors")

highcharts_3d_js = None
for url in _HC_3D_URLS:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            highcharts_3d_js = response.read().decode("utf-8")
        break
    except Exception:
        continue
if highcharts_3d_js is None:
    raise RuntimeError("Failed to download highcharts-3d.js from all mirrors")

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_3d_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
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
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
