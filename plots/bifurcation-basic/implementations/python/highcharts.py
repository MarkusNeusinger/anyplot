""" pyplots.ai
bifurcation-basic: Bifurcation Diagram for Dynamical Systems
Library: highcharts unknown | Python 3.14.3
Quality: 88/100 | Created: 2026-03-20
"""

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


# Data — logistic map bifurcation diagram
# x(n+1) = r * x(n) * (1 - x(n))
r_values = np.linspace(2.5, 4.0, 1500)
n_transient = 200
n_plot = 100

# Split points into regions for color-coded storytelling
stable_points = []  # r < 3.0: stable fixed point
periodic_points = []  # 3.0 <= r < 3.5699: period-doubling cascade
chaotic_points = []  # r >= 3.5699: chaotic regime

for r in r_values:
    x = 0.5
    for _ in range(n_transient):
        x = r * x * (1.0 - x)
    for _ in range(n_plot):
        x = r * x * (1.0 - x)
        pt = [round(float(r), 5), round(float(x), 5)]
        if r < 3.0:
            stable_points.append(pt)
        elif r < 3.5699:
            periodic_points.append(pt)
        else:
            chaotic_points.append(pt)

# Build chart using highcharts-core Python API
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#f8f9fb",
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif"},
    "marginTop": 180,
    "marginBottom": 220,
    "marginLeft": 220,
    "marginRight": 140,
}

chart.options.title = {
    "text": "bifurcation-basic \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "58px", "fontWeight": "700", "color": "#1a2530", "letterSpacing": "1px"},
    "margin": 40,
}

chart.options.subtitle = {
    "text": "x(n+1) = r \u00b7 x(n) \u00b7 (1 \u2212 x(n)) \u2014 period-doubling route from stability to chaos",
    "style": {"fontSize": "36px", "color": "#6c7a89", "fontWeight": "400"},
}

chart.options.x_axis = {
    "title": {
        "text": "Growth Rate Parameter (r)",
        "style": {"fontSize": "42px", "color": "#2c3e50", "fontWeight": "500"},
        "margin": 30,
    },
    "labels": {"style": {"fontSize": "32px", "color": "#6c7a89"}},
    "min": 2.5,
    "max": 4.0,
    "tickInterval": 0.25,
    "startOnTick": True,
    "endOnTick": True,
    "gridLineWidth": 0,
    "lineColor": "#bdc3c7",
    "lineWidth": 2,
    "plotBands": [
        {
            "from": 2.5,
            "to": 3.0,
            "color": "rgba(46, 204, 113, 0.06)",
            "label": {
                "text": "Stable",
                "style": {"fontSize": "28px", "color": "rgba(39, 174, 96, 0.5)", "fontWeight": "600"},
                "verticalAlign": "bottom",
                "y": -20,
            },
        },
        {
            "from": 3.0,
            "to": 3.5699,
            "color": "rgba(52, 152, 219, 0.06)",
            "label": {
                "text": "Period-Doubling",
                "style": {"fontSize": "28px", "color": "rgba(41, 128, 185, 0.5)", "fontWeight": "600"},
                "verticalAlign": "bottom",
                "y": -20,
            },
        },
        {
            "from": 3.5699,
            "to": 4.0,
            "color": "rgba(155, 89, 182, 0.06)",
            "label": {
                "text": "Chaos",
                "style": {"fontSize": "28px", "color": "rgba(142, 68, 173, 0.5)", "fontWeight": "600"},
                "verticalAlign": "bottom",
                "y": -20,
            },
        },
    ],
    "plotLines": [
        {
            "value": 3.0,
            "color": "rgba(39, 174, 96, 0.55)",
            "width": 3,
            "dashStyle": "LongDash",
            "label": {
                "text": "r \u2248 3.0  \u2022  period-2",
                "style": {"fontSize": "30px", "color": "rgba(39, 174, 96, 0.85)", "fontWeight": "500"},
                "rotation": 0,
                "y": -15,
                "x": 10,
            },
        },
        {
            "value": 3.449,
            "color": "rgba(41, 128, 185, 0.55)",
            "width": 3,
            "dashStyle": "LongDash",
            "label": {
                "text": "r \u2248 3.449  \u2022  period-4",
                "style": {"fontSize": "30px", "color": "rgba(41, 128, 185, 0.85)", "fontWeight": "500"},
                "rotation": 0,
                "y": -15,
                "x": 10,
            },
        },
        {
            "value": 3.544,
            "color": "rgba(142, 68, 173, 0.55)",
            "width": 3,
            "dashStyle": "LongDash",
            "label": {
                "text": "period-8",
                "style": {"fontSize": "28px", "color": "rgba(142, 68, 173, 0.85)", "fontWeight": "500"},
                "rotation": 270,
                "y": 60,
                "x": -12,
            },
        },
        {
            "value": 3.5699,
            "color": "rgba(142, 68, 173, 0.7)",
            "width": 3,
            "dashStyle": "ShortDash",
            "label": {
                "text": "onset of chaos",
                "style": {"fontSize": "28px", "color": "rgba(142, 68, 173, 0.85)", "fontWeight": "600"},
                "rotation": 270,
                "y": 60,
                "x": -12,
            },
        },
    ],
}

chart.options.y_axis = {
    "title": {
        "text": "Steady-State x",
        "style": {"fontSize": "42px", "color": "#2c3e50", "fontWeight": "500"},
        "margin": 30,
    },
    "labels": {"style": {"fontSize": "32px", "color": "#6c7a89"}},
    "min": 0,
    "max": 1.0,
    "tickInterval": 0.2,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.04)",
    "gridLineDashStyle": "Dot",
    "lineColor": "#bdc3c7",
    "lineWidth": 2,
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -30,
    "y": 80,
    "floating": True,
    "backgroundColor": "rgba(255, 255, 255, 0.85)",
    "borderWidth": 1,
    "borderColor": "#e0e0e0",
    "borderRadius": 8,
    "itemStyle": {"fontSize": "28px", "fontWeight": "400", "color": "#2c3e50"},
    "symbolRadius": 6,
    "symbolHeight": 14,
    "symbolWidth": 14,
    "itemMarginBottom": 8,
}
chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": '<span style="font-size:26px">r = <b>{point.x:.4f}</b><br/>x = <b>{point.y:.4f}</b></span>',
    "backgroundColor": "rgba(255, 255, 255, 0.95)",
    "borderColor": "#306998",
    "borderRadius": 10,
    "borderWidth": 2,
    "style": {"fontSize": "26px"},
}

chart.options.plot_options = {
    "scatter": {
        "turboThreshold": 200000,
        "marker": {"radius": 1.3, "symbol": "circle", "states": {"hover": {"radiusPlus": 3}}},
    }
}

# Three color-coded series for visual storytelling
s_stable = ScatterSeries()
s_stable.name = "Stable (r < 3.0)"
s_stable.color = "rgba(39, 174, 96, 0.4)"
s_stable.data = stable_points
chart.add_series(s_stable)

s_periodic = ScatterSeries()
s_periodic.name = "Period-Doubling (3.0 \u2264 r < 3.57)"
s_periodic.color = "rgba(41, 128, 185, 0.35)"
s_periodic.data = periodic_points
chart.add_series(s_periodic)

s_chaotic = ScatterSeries()
s_chaotic.name = "Chaotic (r \u2265 3.57)"
s_chaotic.color = "rgba(142, 68, 173, 0.3)"
s_chaotic.data = chaotic_points
chart.add_series(s_chaotic)

# Download Highcharts JS (with CDN fallback)
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

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
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
time.sleep(8)

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
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0; background:#fafbfc;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(interactive_html)
