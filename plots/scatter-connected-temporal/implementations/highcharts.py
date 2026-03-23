""" pyplots.ai
scatter-connected-temporal: Connected Scatter Plot with Temporal Path
Library: highcharts unknown | Python 3.14.3
Quality: 84/100 | Updated: 2026-03-23
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data — US unemployment rate vs inflation rate (1990-2023)
years = np.arange(1990, 2024)
n_years = len(years)

unemployment = np.array(
    [
        5.6,
        6.8,
        7.5,
        6.9,
        6.1,
        5.6,
        5.4,
        4.9,
        4.5,
        4.2,
        4.0,
        4.7,
        5.8,
        6.0,
        5.5,
        5.1,
        4.6,
        4.6,
        5.8,
        9.3,
        9.6,
        8.9,
        8.1,
        7.4,
        6.2,
        5.3,
        4.9,
        4.4,
        3.9,
        3.7,
        8.1,
        5.4,
        3.6,
        3.6,
    ]
)

inflation = np.array(
    [
        5.4,
        4.2,
        3.0,
        3.0,
        2.6,
        2.8,
        3.0,
        2.3,
        1.6,
        2.2,
        3.4,
        2.8,
        1.6,
        2.3,
        2.7,
        3.4,
        3.2,
        2.8,
        3.8,
        -0.4,
        1.6,
        3.2,
        2.1,
        1.5,
        1.6,
        0.1,
        1.3,
        2.1,
        2.4,
        1.8,
        1.2,
        4.7,
        8.0,
        4.1,
    ]
)

# Color gradient from light steel blue to dark navy for temporal progression
start_color = np.array([160, 200, 230])
end_color = np.array([20, 50, 120])
key_years = {1990, 2000, 2009, 2020, 2023}

# Build point data with per-point color and marker size
point_data = []
for i in range(n_years):
    t = i / (n_years - 1)
    c = (1 - t) * start_color + t * end_color
    color = f"rgb({int(c[0])},{int(c[1])},{int(c[2])})"
    year = int(years[i])
    is_key = year in key_years

    point = {
        "x": float(unemployment[i]),
        "y": float(inflation[i]),
        "name": str(year),
        "color": color,
        "marker": {
            "radius": 16 if is_key else 10,
            "lineWidth": 3 if is_key else 2,
            "lineColor": "#ffffff",
            "symbol": "circle",
        },
    }

    if is_key:
        point["dataLabels"] = {
            "enabled": True,
            "format": str(year),
            "style": {"fontSize": "32px", "fontWeight": "700", "color": "#2c3e50", "textOutline": "3px white"},
            "y": -30,
        }

    point_data.append(point)

# Chart setup
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#fafbfc",
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif"},
    "marginTop": 180,
    "marginBottom": 300,
    "marginLeft": 260,
    "marginRight": 200,
}

chart.options.title = {
    "text": "scatter-connected-temporal \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "58px", "fontWeight": "600", "color": "#2c3e50", "letterSpacing": "1px"},
    "margin": 40,
}

chart.options.subtitle = {
    "text": "Unemployment vs Inflation in the US (1990\u20132023) \u2014 tracing the Phillips Curve over time",
    "style": {"fontSize": "36px", "color": "#7f8c8d", "fontWeight": "400"},
}

chart.options.x_axis = {
    "title": {
        "text": "Unemployment Rate (%)",
        "style": {"fontSize": "42px", "color": "#34495e", "fontWeight": "500"},
        "margin": 30,
    },
    "labels": {"style": {"fontSize": "32px", "color": "#7f8c8d"}},
    "min": 2.5,
    "max": 11.0,
    "tickInterval": 1,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.06)",
    "gridLineDashStyle": "Dot",
    "lineColor": "#bdc3c7",
    "lineWidth": 2,
}

chart.options.y_axis = {
    "title": {
        "text": "Inflation Rate (%)",
        "style": {"fontSize": "42px", "color": "#34495e", "fontWeight": "500"},
        "margin": 30,
    },
    "labels": {"style": {"fontSize": "32px", "color": "#7f8c8d"}},
    "min": -1.5,
    "max": 9.5,
    "tickInterval": 1,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.06)",
    "gridLineDashStyle": "Dot",
    "lineColor": "#bdc3c7",
    "lineWidth": 2,
}

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": (
        '<span style="font-size:28px;color:{point.color}">\u25cf</span> '
        '<span style="font-size:28px">'
        " Year: <b>{point.name}</b><br/>"
        " Unemployment: <b>{point.x:.1f}%</b><br/>"
        " Inflation: <b>{point.y:.1f}%</b></span>"
    ),
    "backgroundColor": "rgba(255, 255, 255, 0.95)",
    "borderColor": "#306998",
    "borderRadius": 10,
    "borderWidth": 2,
    "style": {"fontSize": "28px"},
}

# Serialize chart options to dict and inject raw series with per-point colors
chart_dict = chart.options.to_dict()

# Add series directly to dict (bypasses Python API color limitations)
chart_dict["series"] = [
    {
        "type": "line",
        "name": "Phillips Curve Path",
        "data": point_data,
        "lineWidth": 3,
        "lineColor": "rgba(48, 105, 152, 0.30)",
        "marker": {"enabled": True, "radius": 10, "lineWidth": 2, "lineColor": "#ffffff"},
        "states": {"hover": {"lineWidthPlus": 0}},
        "turboThreshold": 0,
    }
]

chart_options_json = json.dumps(chart_dict)

# Download Highcharts JS
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline JS
html_str = f"Highcharts.chart('container', {chart_options_json});"

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:#fafbfc;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML and take screenshot
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

container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    interactive_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"></script>
</head>
<body style="margin:0; background:#fafbfc;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(interactive_html)
