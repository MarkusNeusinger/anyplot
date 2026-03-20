""" pyplots.ai
bar-pareto: Pareto Chart with Cumulative Line
Library: highcharts unknown | Python 3.14.3
Quality: 85/100 | Created: 2026-03-20
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Manufacturing defect types sorted descending by frequency
categories = [
    "Scratches",
    "Dents",
    "Misalignment",
    "Cracks",
    "Discoloration",
    "Burrs",
    "Warping",
    "Contamination",
    "Missing Parts",
    "Oversize",
]
counts = np.array([187, 128, 93, 71, 54, 38, 27, 19, 12, 6])

# Cumulative percentage
cumulative = np.cumsum(counts) / counts.sum() * 100
cumulative_data = [round(float(v), 1) for v in cumulative]

# Bar data with Python Blue color
bar_data = [{"y": int(c), "color": "#306998"} for c in counts]

# Chart configuration
chart_config = {
    "chart": {
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "marginBottom": 300,
        "marginTop": 160,
        "marginLeft": 240,
        "marginRight": 240,
        "alignTicks": False,
        "style": {"fontFamily": "Arial, Helvetica, sans-serif"},
    },
    "title": {
        "text": "Manufacturing Defect Analysis \u00b7 bar-pareto \u00b7 highcharts \u00b7 pyplots.ai",
        "style": {"fontSize": "48px", "fontWeight": "bold", "color": "#2c3e50"},
        "margin": 50,
    },
    "subtitle": {
        "text": "Top 4 defect types account for 75% of all quality issues",
        "style": {"fontSize": "30px", "color": "#7f8c8d", "fontWeight": "normal"},
    },
    "xAxis": {
        "categories": categories,
        "title": {"text": "Defect Type", "style": {"fontSize": "34px", "color": "#555555"}, "margin": 20},
        "labels": {"style": {"fontSize": "28px", "color": "#555555"}, "rotation": -35},
        "lineColor": "#cccccc",
        "crosshair": True,
    },
    "yAxis": [
        {
            "title": {"text": "Defect Count", "style": {"fontSize": "34px", "color": "#306998"}, "margin": 15},
            "labels": {"style": {"fontSize": "26px", "color": "#555555"}, "format": "{value}"},
            "gridLineColor": "#e8e8e8",
            "gridLineWidth": 1,
            "gridLineDashStyle": "Dot",
            "min": 0,
        },
        {
            "title": {"text": "Cumulative %", "style": {"fontSize": "34px", "color": "#e67e22"}, "margin": 15},
            "labels": {"style": {"fontSize": "26px", "color": "#555555"}, "format": "{value}%"},
            "min": 0,
            "max": 100,
            "tickInterval": 20,
            "opposite": True,
            "gridLineWidth": 0,
            "plotLines": [
                {
                    "value": 80,
                    "color": "#c0392b",
                    "width": 3,
                    "dashStyle": "LongDash",
                    "zIndex": 5,
                    "label": {
                        "text": "80% threshold",
                        "align": "left",
                        "x": 10,
                        "y": -12,
                        "style": {"fontSize": "26px", "color": "#c0392b", "fontWeight": "bold", "fontStyle": "italic"},
                    },
                }
            ],
        },
    ],
    "tooltip": {
        "shared": True,
        "backgroundColor": "rgba(255, 255, 255, 0.95)",
        "borderColor": "#306998",
        "borderRadius": 8,
        "borderWidth": 2,
        "style": {"fontSize": "22px"},
    },
    "plotOptions": {"column": {"pointPadding": 0.08, "borderWidth": 0, "groupPadding": 0.05, "borderRadius": 5}},
    "series": [
        {
            "type": "column",
            "name": "Defect Count",
            "data": bar_data,
            "yAxis": 0,
            "dataLabels": {
                "enabled": True,
                "format": "{y}",
                "style": {"fontSize": "24px", "fontWeight": "bold", "color": "#2c3e50", "textOutline": "2px white"},
                "y": -8,
            },
        },
        {
            "type": "spline",
            "name": "Cumulative %",
            "data": cumulative_data,
            "yAxis": 1,
            "color": "#e67e22",
            "lineWidth": 4,
            "marker": {
                "enabled": True,
                "radius": 8,
                "fillColor": "#e67e22",
                "lineWidth": 3,
                "lineColor": "#ffffff",
                "symbol": "circle",
            },
            "dataLabels": {
                "enabled": True,
                "format": "{y:.1f}%",
                "style": {"fontSize": "22px", "fontWeight": "bold", "color": "#e67e22", "textOutline": "2px white"},
                "y": -20,
            },
        },
    ],
    "legend": {
        "enabled": True,
        "itemStyle": {"fontSize": "28px", "fontWeight": "normal", "color": "#555555"},
        "symbolRadius": 4,
        "symbolHeight": 18,
        "symbolWidth": 18,
        "itemDistance": 40,
    },
    "credits": {"enabled": False},
}

chart_json = json.dumps(chart_config)

# Download Highcharts JS
cdn_urls = ["https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"]
highcharts_js = None
for url in cdn_urls:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
        break
    except Exception:
        continue
if not highcharts_js:
    raise RuntimeError("Failed to download Highcharts JS from all CDN sources")

# Build HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; padding:0; background:#ffffff;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        Highcharts.chart('container', {chart_json});
    }});
    </script>
</body>
</html>"""

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save HTML for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

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
driver.save_screenshot("plot.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
