""" pyplots.ai
learning-curve-basic: Model Learning Curve
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Simulated learning curve from a classification model
np.random.seed(42)

train_sizes = [50, 100, 200, 400, 600, 800, 1000, 1200, 1400, 1600]

# Training scores: starts high, remains high (slight decrease with more data due to harder fitting)
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
# arearange series expects [[x, low, high], ...]
train_band_data = [[x, lo, hi] for x, lo, hi in zip(train_sizes, train_lower, train_upper, strict=True)]
val_band_data = [[x, lo, hi] for x, lo, hi in zip(train_sizes, val_lower, val_upper, strict=True)]
# line series expects [[x, y], ...]
train_line_data = [[x, y] for x, y in zip(train_sizes, train_scores_mean, strict=True)]
val_line_data = [[x, y] for x, y in zip(train_sizes, validation_scores_mean, strict=True)]

# Chart options
chart_options = {
    "chart": {
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "marginBottom": 180,
        "marginLeft": 200,
        "marginRight": 120,
        "marginTop": 150,
        "style": {"fontFamily": "Arial, sans-serif"},
    },
    "title": {
        "text": "learning-curve-basic · highcharts · pyplots.ai",
        "style": {"fontSize": "64px", "fontWeight": "bold"},
    },
    "subtitle": {"text": "Model Performance vs Training Set Size", "style": {"fontSize": "38px", "color": "#666666"}},
    "xAxis": {
        "title": {"text": "Training Set Size (samples)", "style": {"fontSize": "48px"}, "margin": 20},
        "labels": {"style": {"fontSize": "36px"}},
        "gridLineWidth": 1,
        "gridLineColor": "rgba(0, 0, 0, 0.1)",
        "gridLineDashStyle": "Dash",
        "min": 0,
        "max": 1700,
    },
    "yAxis": {
        "title": {"text": "Accuracy Score", "style": {"fontSize": "48px"}, "margin": 20},
        "labels": {"style": {"fontSize": "36px"}, "format": "{value:.2f}"},
        "gridLineWidth": 1,
        "gridLineColor": "rgba(0, 0, 0, 0.1)",
        "gridLineDashStyle": "Dash",
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
        "itemStyle": {"fontSize": "36px"},
        "itemMarginBottom": 15,
        "backgroundColor": "rgba(255, 255, 255, 0.9)",
        "borderWidth": 1,
        "borderColor": "#cccccc",
        "padding": 15,
    },
    "plotOptions": {
        "arearange": {"fillOpacity": 0.25, "lineWidth": 0, "marker": {"enabled": False}},
        "line": {"lineWidth": 6, "marker": {"enabled": True, "radius": 12, "lineWidth": 3, "lineColor": "#ffffff"}},
    },
    "series": [
        # Training confidence band
        {
            "name": "Training ±1 std",
            "type": "arearange",
            "data": train_band_data,
            "color": "#306998",
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
            "color": "#FFD43B",
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
            "color": "#306998",
            "lineWidth": 6,
            "zIndex": 1,
            "marker": {"fillColor": "#306998", "radius": 12, "lineWidth": 3, "lineColor": "#ffffff"},
        },
        # Validation score line
        {
            "name": "Validation Score",
            "type": "line",
            "data": val_line_data,
            "color": "#FFD43B",
            "lineWidth": 6,
            "zIndex": 1,
            "marker": {"fillColor": "#FFD43B", "radius": 12, "lineWidth": 3, "lineColor": "#ffffff"},
        },
    ],
}

# Download Highcharts JS and highcharts-more (needed for arearange)
highcharts_url = "https://code.highcharts.com/highcharts.js"
highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"

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
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            Highcharts.chart('container', {chart_options_json});
        }});
    </script>
</body>
</html>"""

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save the HTML for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--force-device-scale-factor=1")

driver = webdriver.Chrome(options=chrome_options)
driver.set_window_size(4900, 2900)
driver.get(f"file://{temp_path}")
time.sleep(5)

# Take screenshot
driver.save_screenshot("plot_raw.png")
driver.quit()

# Crop/resize to exact 4800x2700 using PIL
img = Image.open("plot_raw.png")
final_img = Image.new("RGB", (4800, 2700), (255, 255, 255))
final_img.paste(img.crop((0, 0, min(img.width, 4800), min(img.height, 2700))), (0, 0))
final_img.save("plot.png")

# Clean up
Path("plot_raw.png").unlink()
Path(temp_path).unlink()
