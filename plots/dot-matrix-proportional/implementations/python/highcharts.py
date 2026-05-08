"""anyplot.ai
dot-matrix-proportional: Dot Matrix Chart for Proportional Counts
Library: highcharts | Python 3.13
Quality: pending | Created: 2026-05-08
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
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data — Tech Survey: Preferred Code Editor (100 developers)
categories = [
    {"name": "VS Code", "count": 52},
    {"name": "JetBrains", "count": 28},
    {"name": "Vim / Neovim", "count": 12},
    {"name": "Other", "count": 8},
]
total = sum(c["count"] for c in categories)  # 100
cols = 10
rows = total // cols  # 10

# Assign grid positions — left-to-right, top-to-bottom (y inverted so first dot is top-left)
flat_cats = []
for cat in categories:
    flat_cats.extend([cat["name"]] * cat["count"])

dots_by_category = {c["name"]: [] for c in categories}
for idx, cat_name in enumerate(flat_cats):
    col = idx % cols
    row = rows - 1 - (idx // cols)
    dots_by_category[cat_name].append([col, row])

# Build chart — 4800×2700 landscape with right-side vertical legend
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "style": {"color": INK},
    "marginTop": 200,
    "marginBottom": 200,
    "marginLeft": 200,
    "marginRight": 900,
}
chart.options.title = {
    "text": "dot-matrix-proportional · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "color": INK, "fontWeight": "600"},
    "margin": 12,
}
chart.options.subtitle = {
    "text": "Preferred Code Editor · Tech Survey (n=100 developers · 1 dot = 1 respondent)",
    "style": {"fontSize": "20px", "color": INK_SOFT},
}
chart.options.x_axis = {
    "min": -0.5,
    "max": cols - 0.5,
    "labels": {"enabled": False},
    "title": {"text": None},
    "lineColor": "transparent",
    "tickLength": 0,
    "gridLineWidth": 0,
}
chart.options.y_axis = {
    "min": -0.5,
    "max": rows - 0.5,
    "labels": {"enabled": False},
    "title": {"text": None},
    "lineColor": "transparent",
    "tickLength": 0,
    "gridLineWidth": 0,
}
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "middle",
    "layout": "vertical",
    "itemStyle": {"fontSize": "22px", "color": INK_SOFT, "fontWeight": "normal"},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "borderRadius": 6,
    "padding": 20,
    "itemMarginBottom": 14,
    "symbolRadius": 12,
    "symbolHeight": 24,
    "symbolWidth": 24,
}
chart.options.plot_options = {
    "scatter": {"marker": {"radius": 100, "symbol": "circle", "lineWidth": 0}, "enableMouseTracking": False}
}
chart.options.tooltip = {"enabled": False}
chart.options.colors = OKABE_ITO
chart.options.credits = {"enabled": False}

for cat in categories:
    series = ScatterSeries()
    series.name = f"{cat['name']} ({cat['count']} / {total})"
    series.data = dots_by_category[cat["name"]]
    chart.add_series(series)

# Download and embed Highcharts JS inline (CDN blocked in headless Chrome)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js"
req = urllib.request.Request(
    highcharts_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

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
