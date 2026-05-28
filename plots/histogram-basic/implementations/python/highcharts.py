"""anyplot.ai
histogram-basic: Basic Histogram
Library: highcharts | Python 3.13
Quality: pending | Created: 2026-05-28
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import ColumnSeries
from highcharts_core.options.series.histogram import HistogramSeries
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
BRAND = "#009E73"

# Data — exam scores with bimodal distribution (main group + high achievers)
np.random.seed(42)
main_group = np.random.normal(loc=72, scale=12, size=400)
high_achievers = np.random.normal(loc=88, scale=5, size=100)
exam_scores = np.clip(np.concatenate([main_group, high_achievers]), 0, 100)

mean_score = float(np.mean(exam_scores))
median_score = float(np.median(exam_scores))

# Chart
title = "histogram-basic · python · highcharts · anyplot.ai"
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "column",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "marginBottom": 140,
    "marginLeft": 200,
    "marginRight": 80,
    "marginTop": 180,
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif"},
}

chart.options.title = {"text": title, "style": {"fontSize": "66px", "fontWeight": "600", "color": INK}, "margin": 20}

chart.options.subtitle = {
    "text": "500 students · Intro to Statistics, Fall 2024 · bimodal: main cluster ~72, high-achievers ~88",
    "style": {"fontSize": "34px", "color": INK_MUTED},
}

chart.options.x_axis = {
    "title": {"text": "Exam Score (points)", "style": {"fontSize": "56px", "color": INK}, "margin": 16},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "tickInterval": 10,
    "plotBands": [
        {
            "from": 0,
            "to": 60,
            "color": "rgba(174,48,48,0.07)",
            "label": {
                "text": "D/F",
                "style": {"fontSize": "32px", "color": "#AE3030", "fontWeight": "600"},
                "align": "center",
                "y": -10,
            },
        },
        {
            "from": 60,
            "to": 70,
            "color": "rgba(189,130,51,0.07)",
            "label": {
                "text": "C",
                "style": {"fontSize": "32px", "color": "#BD8233", "fontWeight": "600"},
                "align": "center",
                "y": -10,
            },
        },
        {
            "from": 70,
            "to": 80,
            "color": "rgba(0,158,115,0.07)",
            "label": {
                "text": "B",
                "style": {"fontSize": "32px", "color": "#009E73", "fontWeight": "600"},
                "align": "center",
                "y": -10,
            },
        },
        {
            "from": 80,
            "to": 90,
            "color": "rgba(68,103,163,0.07)",
            "label": {
                "text": "A",
                "style": {"fontSize": "32px", "color": "#4467A3", "fontWeight": "600"},
                "align": "center",
                "y": -10,
            },
        },
        {
            "from": 90,
            "to": 100,
            "color": "rgba(149,68,119,0.07)",
            "label": {
                "text": "A+",
                "style": {"fontSize": "32px", "color": "#954477", "fontWeight": "600"},
                "align": "center",
                "y": -10,
            },
        },
    ],
    "plotLines": [
        {
            "value": round(mean_score, 1),
            "color": "#AE3030",
            "width": 3,
            "dashStyle": "Dash",
            "zIndex": 5,
            "label": {
                "text": f"Mean: {mean_score:.1f}",
                "style": {"fontSize": "32px", "color": "#AE3030", "fontWeight": "600"},
                "align": "right",
                "rotation": 0,
                "x": -10,
                "y": 44,
            },
        },
        {
            "value": round(median_score, 1),
            "color": "#4467A3",
            "width": 3,
            "dashStyle": "ShortDot",
            "zIndex": 5,
            "label": {
                "text": f"Median: {median_score:.1f}",
                "style": {"fontSize": "32px", "color": "#4467A3", "fontWeight": "600"},
                "align": "left",
                "rotation": 0,
                "x": 10,
                "y": 44,
            },
        },
    ],
}

chart.options.y_axis = {
    "title": {"text": "Number of Students", "style": {"fontSize": "56px", "color": INK}, "margin": 20},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "min": 0,
    "gridLineColor": GRID,
    "gridLineWidth": 1,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

chart.options.plot_options = {
    "histogram": {
        "pointPadding": 0,
        "groupPadding": 0,
        "borderWidth": 0.5,
        "borderColor": INK_SOFT,
        "binsNumber": 20,
        "color": BRAND,
    }
}

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}

# Hidden base series provides data for the histogram series
base_series = ColumnSeries()
base_series.name = "Raw Scores"
base_series.data = [round(float(v), 1) for v in exam_scores]
base_series.id = "exam-data"
base_series.visible = False
base_series.show_in_legend = False

# Histogram series derived from base data
hist_series = HistogramSeries()
hist_series.name = "Students"
hist_series.base_series = "exam-data"
hist_series.color = BRAND
hist_series.bins_number = 20

chart.add_series(base_series)
chart.add_series(hist_series)

# Download Highcharts JS and histogram module inline (required for headless Chrome)
_headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.highcharts.com/"}

_req = urllib.request.Request("https://code.highcharts.com/highcharts.js", headers=_headers)
with urllib.request.urlopen(_req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

_req2 = urllib.request.Request("https://code.highcharts.com/modules/histogram-bellcurve.js", headers=_headers)
with urllib.request.urlopen(_req2, timeout=30) as response:
    histogram_module_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{histogram_module_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML artifact for interactive version
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via headless Chrome
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=3200,1800")

driver = webdriver.Chrome(options=chrome_options)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin to exact 3200×1800 (belt-and-braces for ±1–2 px rounding)
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
