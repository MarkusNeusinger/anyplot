"""anyplot.ai
scatter-basic: Basic Scatter Plot
Library: highcharts | Python 3.14
Quality: pending | Updated: 2026-04-23
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
BRAND = "#009E73"  # Okabe-Ito position 1

# Data — study hours vs exam scores (moderate positive correlation + noise)
np.random.seed(42)
n_points = 180
study_hours = np.random.uniform(1, 12, n_points)
exam_scores = np.clip(40 + study_hours * 4.5 + np.random.normal(0, 7, n_points), 30, 100)

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "style": {"fontFamily": "'Inter', 'Helvetica Neue', Arial, sans-serif", "color": INK},
    "spacingTop": 60,
    "spacingBottom": 60,
    "spacingLeft": 60,
    "spacingRight": 60,
}

chart.options.title = {
    "text": "scatter-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "56px", "fontWeight": "600", "color": INK},
    "margin": 40,
}

chart.options.x_axis = {
    "title": {"text": "Study Hours (per week)", "style": {"fontSize": "40px", "color": INK}, "margin": 30},
    "labels": {"style": {"fontSize": "30px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "tickLength": 10,
    "tickInterval": 2,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "startOnTick": True,
    "endOnTick": True,
}

chart.options.y_axis = {
    "title": {"text": "Exam Score (%)", "style": {"fontSize": "40px", "color": INK}, "margin": 30},
    "labels": {"style": {"fontSize": "30px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "tickLength": 10,
    "tickInterval": 10,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "startOnTick": True,
    "endOnTick": True,
}

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderRadius": 8,
    "borderWidth": 1,
    "style": {"fontSize": "24px", "color": INK},
    "pointFormat": "Hours: <b>{point.x:.1f}</b><br/>Score: <b>{point.y:.1f}%</b>",
    "headerFormat": "",
}

chart.options.plot_options = {
    "scatter": {"marker": {"radius": 14, "symbol": "circle", "lineWidth": 2, "lineColor": PAGE_BG, "fillOpacity": 0.7}}
}

series = ScatterSeries()
series.data = [[float(h), float(s)] for h, s in zip(study_hours, exam_scores, strict=True)]
series.name = "Students"
series.color = BRAND
chart.add_series(series)

# Download Highcharts JS (required for headless Chrome).
# Primary host blocks non-browser UA via Cloudflare, so fall back to the cdnjs mirror.
highcharts_urls = [
    "https://code.highcharts.com/highcharts.js",
    "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.4.8/highcharts.js",
]
highcharts_js = None
for url in highcharts_urls:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
        break
    except urllib.error.HTTPError:
        continue
if highcharts_js is None:
    raise RuntimeError("Could not download Highcharts JS from any mirror")

# Build HTML with inline script
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

# Save interactive HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Headless Chrome screenshot for PNG artifact
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=4900,2900")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
container = driver.find_element("id", "container")
container.screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
