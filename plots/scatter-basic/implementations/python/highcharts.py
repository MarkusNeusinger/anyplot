""" anyplot.ai
scatter-basic: Basic Scatter Plot
Library: highcharts unknown | Python 3.14.4
Quality: 88/100 | Created: 2026-04-23
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
BRAND = "#009E73"

# Data — study hours vs exam scores with moderate positive correlation
np.random.seed(42)
n_points = 120
study_hours = np.random.normal(6, 1.8, n_points)
exam_scores = study_hours * 7.5 + np.random.normal(0, 6, n_points) + 30
exam_scores = np.clip(exam_scores, 0, 100)

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "style": {"fontFamily": "'Inter', 'Segoe UI', Helvetica, Arial, sans-serif", "color": INK},
    "spacing": [60, 60, 60, 60],
}

chart.options.title = {
    "text": "scatter-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "64px", "fontWeight": "500", "color": INK},
    "margin": 50,
}

chart.options.x_axis = {
    "title": {"text": "Study Hours per Day", "style": {"fontSize": "44px", "color": INK}, "margin": 30},
    "labels": {"style": {"fontSize": "32px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
}

chart.options.y_axis = {
    "title": {"text": "Exam Score (%)", "style": {"fontSize": "44px", "color": INK}, "margin": 30},
    "labels": {"style": {"fontSize": "32px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
}

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderRadius": 8,
    "borderWidth": 1,
    "style": {"fontSize": "26px", "color": INK},
    "headerFormat": "",
    "pointFormat": "Hours: <b>{point.x:.1f}</b><br/>Score: <b>{point.y:.1f}</b>",
}

chart.options.plot_options = {
    "scatter": {"marker": {"radius": 20, "symbol": "circle", "lineWidth": 2, "lineColor": PAGE_BG, "fillOpacity": 0.7}}
}

scatter = ScatterSeries()
scatter.data = [[float(h), float(s)] for h, s in zip(study_hours, exam_scores, strict=True)]
scatter.name = "Students"
scatter.color = BRAND
chart.add_series(scatter)

# Download Highcharts JS (headless Chrome cannot load CDN from file://)
highcharts_url = "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.4.8/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

chart_js = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{chart_js}</script>
</body>
</html>"""

# Save HTML artifact for the site
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Render PNG via headless Chrome
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4900,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
container = driver.find_element("id", "container")
container.screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
