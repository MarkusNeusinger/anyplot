""" anyplot.ai
strip-basic: Basic Strip Plot
Library: highcharts unknown | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-04
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
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
NEUTRAL = "#1A1A1A" if THEME == "light" else "#E8E8E0"

# Okabe-Ito palette — first series is always #009E73
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data — student test scores by subject
np.random.seed(42)
categories = ["Mathematics", "Science", "Literature", "History"]

raw_data = {
    "Mathematics": np.concatenate(
        [
            np.random.normal(72, 12, 35),
            np.random.normal(90, 5, 10),  # high-performer cluster (bimodal)
        ]
    ),
    "Science": np.random.normal(75, 10, 40),
    "Literature": np.concatenate(
        [
            np.random.normal(65, 8, 25),  # lower cluster
            np.random.normal(82, 6, 20),  # upper cluster (bimodal)
        ]
    ),
    "History": np.random.normal(78, 9, 38),
}

for cat in categories:
    raw_data[cat] = np.clip(raw_data[cat], 30, 100)

jitter_width = 0.25
strip_data = []
for cat_idx, cat in enumerate(categories):
    values = raw_data[cat]
    x_jitter = np.random.uniform(-jitter_width, jitter_width, len(values))
    for val, x_off in zip(values, x_jitter, strict=True):
        strip_data.append({"x": cat_idx + x_off, "y": float(val), "category": cat})

means = {cat: float(np.mean(raw_data[cat])) for cat in categories}

# Plot
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 200,
    "style": {"fontFamily": "-apple-system, system-ui, sans-serif"},
}

chart.options.title = {
    "text": "strip-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "64px", "fontWeight": "bold", "color": INK},
}

chart.options.subtitle = {"text": "Student Test Scores by Subject", "style": {"fontSize": "40px", "color": INK_SOFT}}

chart.options.x_axis = {
    "categories": categories,
    "title": {"text": "Subject", "style": {"fontSize": "40px", "color": INK}},
    "labels": {"style": {"fontSize": "32px", "color": INK_SOFT}},
    "tickWidth": 0,
    "lineColor": INK_SOFT,
    "lineWidth": 2,
    "min": -0.5,
    "max": len(categories) - 0.5,
    "tickPositions": [0, 1, 2, 3],
}

chart.options.y_axis = {
    "title": {"text": "Test Score (%)", "style": {"fontSize": "40px", "color": INK}},
    "labels": {"style": {"fontSize": "32px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "min": 40,
    "max": 105,
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 100,
    "itemStyle": {"fontSize": "30px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": "<b>{series.name}</b><br/>Score: {point.y:.1f}%",
    "style": {"fontSize": "24px"},
}

# Add scatter series per category
for cat_idx, cat in enumerate(categories):
    series = ScatterSeries()
    series.name = cat
    series.color = OKABE_ITO[cat_idx]
    series.data = [{"x": float(pt["x"]), "y": pt["y"]} for pt in strip_data if pt["category"] == cat]
    series.marker = {"radius": 12, "symbol": "circle", "fillOpacity": 0.65, "lineWidth": 1, "lineColor": PAGE_BG}
    chart.add_series(series)

# Mean markers — adaptive neutral (Okabe-Ito position 8)
mean_series = ScatterSeries()
mean_series.name = "Mean"
mean_series.data = [{"x": float(i), "y": means[cat]} for i, cat in enumerate(categories)]
mean_series.color = NEUTRAL
mean_series.marker = {"radius": 20, "symbol": "diamond", "lineWidth": 3, "lineColor": PAGE_BG}
chart.add_series(mean_series)

# Download Highcharts JS inline (headless Chrome cannot load CDN from file://)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

js_literal = chart.to_js_literal()

html_inline = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width:4800px; height:2700px;"></div>
    <script>{js_literal}</script>
</body>
</html>"""

# Site artifact — CDN keeps file size small for served pages
html_cdn = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"></script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width:100%; height:100vh;"></div>
    <script>{js_literal}</script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_cdn)

# Save
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_inline)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2900")
chrome_options.add_argument("--hide-scrollbars")

driver = webdriver.Chrome(options=chrome_options)
driver.set_window_size(4800, 2900)
driver.get(f"file://{temp_path}")
time.sleep(5)
container = driver.find_element("id", "container")
container.screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
