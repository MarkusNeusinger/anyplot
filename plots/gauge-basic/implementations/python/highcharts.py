""" pyplots.ai
gauge-basic: Basic Gauge Chart
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Current sales performance against target
value = 72  # Current value
min_value = 0
max_value = 100
thresholds = [30, 70]  # Red/Yellow/Green zones

# Chart options for solid gauge
chart_options = {
    "chart": {
        "type": "gauge",
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "plotBackgroundColor": None,
        "plotBorderWidth": 0,
        "plotShadow": False,
    },
    "title": {
        "text": "gauge-basic · highcharts · pyplots.ai",
        "style": {"fontSize": "48px", "fontWeight": "bold"},
        "y": 80,
    },
    "pane": {
        "startAngle": -90,
        "endAngle": 90,
        "center": ["50%", "75%"],
        "size": "140%",
        "background": [
            {
                "backgroundColor": {
                    "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
                    "stops": [[0, "#FFF"], [1, "#333"]],
                },
                "borderWidth": 0,
                "outerRadius": "109%",
                "innerRadius": "0%",
            },
            {
                "backgroundColor": {
                    "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
                    "stops": [[0, "#333"], [1, "#FFF"]],
                },
                "borderWidth": 1,
                "outerRadius": "107%",
                "innerRadius": "0%",
            },
            {"backgroundColor": "#DDD", "borderWidth": 0, "outerRadius": "105%", "innerRadius": "103%"},
        ],
    },
    "yAxis": {
        "min": min_value,
        "max": max_value,
        "minorTickInterval": "auto",
        "minorTickWidth": 2,
        "minorTickLength": 15,
        "minorTickPosition": "inside",
        "minorTickColor": "#666",
        "tickPixelInterval": 50,
        "tickWidth": 3,
        "tickPosition": "inside",
        "tickLength": 20,
        "tickColor": "#666",
        "labels": {"step": 2, "rotation": "auto", "style": {"fontSize": "28px"}, "distance": 25},
        "title": {"text": "Performance (%)", "style": {"fontSize": "36px"}, "y": 50},
        "plotBands": [
            {"from": min_value, "to": thresholds[0], "color": "#9467BD", "thickness": 40},  # Low zone (purple)
            {"from": thresholds[0], "to": thresholds[1], "color": "#FFD43B", "thickness": 40},  # Mid zone (yellow)
            {"from": thresholds[1], "to": max_value, "color": "#306998", "thickness": 40},  # High zone (blue)
        ],
    },
    "series": [
        {
            "name": "Performance",
            "data": [value],
            "tooltip": {"valueSuffix": "%"},
            "dataLabels": {
                "format": '<span style="font-size:64px;font-weight:bold">{y}</span>',
                "borderWidth": 0,
                "y": 120,
                "style": {"fontSize": "64px"},
            },
            "dial": {
                "radius": "80%",
                "backgroundColor": "#1a3d5c",
                "baseWidth": 20,
                "baseLength": "0%",
                "rearLength": "0%",
            },
            "pivot": {"backgroundColor": "#1a3d5c", "radius": 15},
        }
    ],
    "tooltip": {"enabled": False},
    "credits": {"enabled": False},
}

# Download Highcharts JS files for inline embedding
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
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2900")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot_raw.png")
driver.quit()

# Crop to exact 4800x2700 dimensions
img = Image.open("plot_raw.png")
img_cropped = img.crop((0, 0, 4800, 2700))
img_cropped.save("plot.png")
Path("plot_raw.png").unlink()

Path(temp_path).unlink()  # Clean up temp file
