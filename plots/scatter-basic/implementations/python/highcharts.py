"""anyplot.ai
scatter-basic: Basic Scatter Plot
Library: highcharts | Python 3.14
Quality: pending | Created: 2026-04-23
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"

# Data — study hours vs exam scores, moderate positive correlation with realistic spread
np.random.seed(42)
n_points = 180
study_hours = np.random.gamma(shape=4.0, scale=1.4, size=n_points)
exam_scores = 38 + 6.2 * study_hours + np.random.normal(0, 7.5, n_points)
exam_scores = np.clip(exam_scores, 0, 100)

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "style": {"fontFamily": "'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif", "color": INK},
    "spacingTop": 80,
    "spacingRight": 120,
    "spacingBottom": 80,
    "spacingLeft": 80,
}

chart.options.title = {
    "text": "scatter-basic · highcharts · anyplot.ai",
    "align": "left",
    "x": 40,
    "style": {"fontSize": "68px", "fontWeight": "600", "color": INK, "letterSpacing": "-0.5px"},
    "margin": 20,
}

chart.options.subtitle = {
    "text": "Study hours versus exam performance across 180 students",
    "align": "left",
    "x": 40,
    "style": {"fontSize": "32px", "fontWeight": "400", "color": INK_MUTED},
}

chart.options.x_axis = {
    "title": {
        "text": "Study Hours per Day",
        "style": {"fontSize": "40px", "fontWeight": "500", "color": INK},
        "margin": 28,
    },
    "labels": {"style": {"fontSize": "28px", "color": INK_SOFT}, "y": 36},
    "lineColor": INK_SOFT,
    "lineWidth": 2,
    "tickColor": INK_SOFT,
    "tickLength": 0,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "min": 0,
    "max": 14,
    "tickInterval": 2,
}

chart.options.y_axis = {
    "title": {"text": "Exam Score (%)", "style": {"fontSize": "40px", "fontWeight": "500", "color": INK}, "margin": 28},
    "labels": {"style": {"fontSize": "28px", "color": INK_SOFT}, "x": -16},
    "lineColor": INK_SOFT,
    "lineWidth": 0,
    "tickColor": INK_SOFT,
    "tickLength": 0,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "min": 0,
    "max": 100,
    "tickInterval": 20,
}

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderRadius": 10,
    "borderWidth": 1,
    "shadow": False,
    "style": {"fontSize": "28px", "color": INK},
    "headerFormat": "",
    "pointFormat": "<b>{point.x:.1f} h</b> study · <b>{point.y:.0f}%</b> score",
}

chart.options.plot_options = {
    "scatter": {
        "marker": {
            "radius": 18,
            "symbol": "circle",
            "lineWidth": 2,
            "lineColor": PAGE_BG,
            "fillOpacity": 0.7,
            "states": {"hover": {"enabled": True, "radiusPlus": 4, "lineWidthPlus": 1}},
        },
        "states": {"hover": {"halo": {"size": 14, "opacity": 0.18}}},
        "stickyTracking": False,
    }
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
chrome_options.add_argument("--window-size=4900,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
container = driver.find_element("id", "container")
container.screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
