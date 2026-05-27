""" anyplot.ai
learning-curve-basic: Model Learning Curve
Library: highcharts unknown | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-10
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
BRAND = "#009E73"  # Position 1 - first series
ORANGE = "#C475FD"  # Position 2

# Data - Simulated learning curve from a classification model
np.random.seed(42)

train_sizes = [50, 100, 200, 400, 600, 800, 1000, 1200, 1400, 1600]

# Training scores: starts high, remains high (slight decrease with more data)
train_scores_mean = [0.99, 0.98, 0.97, 0.96, 0.955, 0.95, 0.948, 0.946, 0.944, 0.943]
train_scores_std = [0.01, 0.012, 0.01, 0.008, 0.007, 0.006, 0.005, 0.005, 0.004, 0.004]

# Validation scores: starts low, increases and converges toward training
validation_scores_mean = [0.72, 0.78, 0.83, 0.87, 0.89, 0.905, 0.915, 0.922, 0.928, 0.932]
validation_scores_std = [0.06, 0.05, 0.04, 0.035, 0.03, 0.025, 0.022, 0.02, 0.018, 0.016]

# Calculate bounds for shaded regions (±1 std)
train_upper = [m + s for m, s in zip(train_scores_mean, train_scores_std, strict=True)]
train_lower = [m - s for m, s in zip(train_scores_mean, train_scores_std, strict=True)]
val_upper = [m + s for m, s in zip(validation_scores_mean, validation_scores_std, strict=True)]
val_lower = [m - s for m, s in zip(validation_scores_mean, validation_scores_std, strict=True)]

# Prepare data for Highcharts
train_band_data = [[x, lo, hi] for x, lo, hi in zip(train_sizes, train_lower, train_upper, strict=True)]
val_band_data = [[x, lo, hi] for x, lo, hi in zip(train_sizes, val_lower, val_upper, strict=True)]
train_line_data = [[x, y] for x, y in zip(train_sizes, train_scores_mean, strict=True)]
val_line_data = [[x, y] for x, y in zip(train_sizes, validation_scores_mean, strict=True)]

# Chart options
chart_options = {
    "chart": {
        "width": 4800,
        "height": 2700,
        "backgroundColor": PAGE_BG,
        "marginBottom": 180,
        "marginLeft": 200,
        "marginRight": 120,
        "marginTop": 150,
        "style": {"fontFamily": "Arial, sans-serif", "color": INK},
    },
    "title": {"text": "learning-curve-basic · highcharts · anyplot.ai", "style": {"fontSize": "28px", "color": INK}},
    "subtitle": {"text": "Model Performance vs Training Set Size", "style": {"fontSize": "22px", "color": INK_SOFT}},
    "xAxis": {
        "title": {"text": "Training Set Size (samples)", "style": {"fontSize": "22px", "color": INK}},
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "gridLineWidth": 1,
        "gridLineColor": GRID,
        "min": 0,
        "max": 1700,
    },
    "yAxis": {
        "title": {"text": "Accuracy Score", "style": {"fontSize": "22px", "color": INK}},
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}, "format": "{value:.2f}"},
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "gridLineWidth": 1,
        "gridLineColor": GRID,
        "min": 0.6,
        "max": 1.02,
    },
    "legend": {
        "enabled": True,
        "align": "right",
        "verticalAlign": "top",
        "layout": "vertical",
        "x": -50,
        "y": 120,
        "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
        "itemMarginBottom": 15,
        "backgroundColor": ELEVATED_BG,
        "borderWidth": 1,
        "borderColor": INK_SOFT,
        "padding": 15,
    },
    "plotOptions": {
        "arearange": {"fillOpacity": 0.25, "lineWidth": 0, "marker": {"enabled": False}},
        "line": {"lineWidth": 6, "marker": {"enabled": True, "radius": 8, "lineWidth": 2, "lineColor": PAGE_BG}},
    },
    "series": [
        # Training confidence band
        {
            "name": "Training ±1 std",
            "type": "arearange",
            "data": train_band_data,
            "color": BRAND,
            "fillOpacity": 0.25,
            "zIndex": 0,
            "showInLegend": False,
            "enableMouseTracking": False,
        },
        # Validation confidence band
        {
            "name": "Validation ±1 std",
            "type": "arearange",
            "data": val_band_data,
            "color": ORANGE,
            "fillOpacity": 0.35,
            "zIndex": 0,
            "showInLegend": False,
            "enableMouseTracking": False,
        },
        # Training score line
        {
            "name": "Training Score",
            "type": "line",
            "data": train_line_data,
            "color": BRAND,
            "lineWidth": 6,
            "zIndex": 1,
            "marker": {"fillColor": BRAND, "radius": 8, "lineWidth": 2, "lineColor": PAGE_BG},
        },
        # Validation score line
        {
            "name": "Validation Score",
            "type": "line",
            "data": val_line_data,
            "color": ORANGE,
            "lineWidth": 6,
            "zIndex": 1,
            "marker": {"fillColor": ORANGE, "radius": 8, "lineWidth": 2, "lineColor": PAGE_BG},
        },
    ],
}

# Download Highcharts JS and highcharts-more from jsDelivr CDN
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
highcharts_more_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts-more.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
chart_options_json = json.dumps(chart_options)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            Highcharts.chart('container', {chart_options_json});
        }});
    </script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML for screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Take screenshot with headless Chrome
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

# Clean up
Path(temp_path).unlink()
