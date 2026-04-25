""" anyplot.ai
gauge-basic: Basic Gauge Chart
Library: highcharts unknown | Python 3.14.4
Quality: 87/100 | Updated: 2026-04-25
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito zones: low / mid / high (intuitive + colorblind-safe)
ZONE_LOW = "#D55E00"  # vermillion (bad)
ZONE_MID = "#E69F00"  # orange (warning)
ZONE_HIGH = "#009E73"  # brand bluish green (good)

# Data
value = 72
min_value = 0
max_value = 100
thresholds = [30, 70]

# Chart options
chart_options = {
    "chart": {
        "type": "gauge",
        "width": 4800,
        "height": 2700,
        "backgroundColor": PAGE_BG,
        "plotBackgroundColor": None,
        "plotBorderWidth": 0,
        "plotShadow": False,
        "spacingTop": 40,
        "spacingBottom": 40,
        "style": {"color": INK},
    },
    "title": {
        "text": "gauge-basic · highcharts · anyplot.ai",
        "style": {"fontSize": "72px", "fontWeight": "bold", "color": INK},
        "y": 90,
    },
    "pane": {
        "startAngle": -90,
        "endAngle": 90,
        "center": ["50%", "78%"],
        "size": "140%",
        "background": [{"backgroundColor": PAGE_BG, "borderWidth": 0, "outerRadius": "109%", "innerRadius": "0%"}],
    },
    "yAxis": {
        "min": min_value,
        "max": max_value,
        "tickInterval": 10,
        "minorTickInterval": 5,
        "minorTickWidth": 2,
        "minorTickLength": 16,
        "minorTickPosition": "inside",
        "minorTickColor": INK_SOFT,
        "tickWidth": 3,
        "tickPosition": "inside",
        "tickLength": 26,
        "tickColor": INK_SOFT,
        "lineColor": INK_SOFT,
        "lineWidth": 0,
        "labels": {
            "rotation": "auto",
            "style": {"fontSize": "44px", "color": INK_SOFT, "fontWeight": "500"},
            "distance": 40,
        },
        "title": {"text": "Performance (%)", "style": {"fontSize": "44px", "color": INK_SOFT}, "y": -120},
        "plotBands": [
            {
                "from": min_value,
                "to": thresholds[0],
                "color": ZONE_LOW,
                "thickness": 70,
                "outerRadius": "100%",
                "innerRadius": "92%",
            },
            {
                "from": thresholds[0],
                "to": thresholds[1],
                "color": ZONE_MID,
                "thickness": 70,
                "outerRadius": "100%",
                "innerRadius": "92%",
            },
            {
                "from": thresholds[1],
                "to": max_value,
                "color": ZONE_HIGH,
                "thickness": 70,
                "outerRadius": "100%",
                "innerRadius": "92%",
            },
        ],
    },
    "series": [
        {
            "name": "Performance",
            "data": [value],
            "tooltip": {"valueSuffix": "%"},
            "dataLabels": {
                "format": f'<span style="font-size:160px;font-weight:bold;color:{INK}">{{y}}</span>',
                "borderWidth": 0,
                "backgroundColor": "transparent",
                "y": 180,
                "useHTML": True,
                "style": {"color": INK},
            },
            "dial": {
                "radius": "82%",
                "backgroundColor": INK,
                "borderColor": INK,
                "baseWidth": 22,
                "topWidth": 4,
                "baseLength": "0%",
                "rearLength": "0%",
            },
            "pivot": {"backgroundColor": INK, "radius": 18, "borderWidth": 0},
        }
    ],
    "tooltip": {"enabled": False},
    "credits": {"enabled": False},
}

# Download Highcharts JS (inline embed required for headless Chrome)
HC_BASE = "https://cdn.jsdelivr.net/npm/highcharts@11.4.8"
with urllib.request.urlopen(f"{HC_BASE}/highcharts.js", timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")
with urllib.request.urlopen(f"{HC_BASE}/highcharts-more.js", timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Generate HTML
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

# Render PNG via headless Chrome
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
