""" pyplots.ai
phase-diagram-pt: Thermodynamic Phase Diagram (Pressure-Temperature)
Library: highcharts unknown | Python 3.14.3
Quality: 84/100 | Created: 2026-03-14
"""

import glob as _glob
import subprocess
import tempfile
import time
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Water phase diagram (realistic)
# Triple point: 273.16 K, 611.73 Pa (0.00604 atm)
# Critical point: 647.1 K, 2.2064e7 Pa (217.7 atm)
triple_t, triple_p = 273.16, 611.73
critical_t, critical_p = 647.1, 2.2064e7

# Solid-gas boundary (sublimation curve) - Clausius-Clapeyron approximation
temp_sg = np.linspace(200, 273.16, 80)
L_sub = 51059  # J/mol sublimation enthalpy
R = 8.314
pressure_sg = triple_p * np.exp((L_sub / R) * (1 / triple_t - 1 / temp_sg))

# Liquid-gas boundary (vaporization curve) - from triple point to critical point
temp_lg = np.linspace(273.16, 647.1, 100)
L_vap = 40660  # J/mol vaporization enthalpy
pressure_lg = triple_p * np.exp((L_vap / R) * (1 / triple_t - 1 / temp_lg))

# Solid-liquid boundary (melting curve) - water has negative slope, cap at y_max
y_max = 1e9
temp_sl_end = triple_t + (triple_p - y_max) / (-1.3e7)
temp_sl = np.linspace(triple_t, temp_sl_end, 60)
pressure_sl = triple_p + (temp_sl - triple_t) * (-1.3e7)

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "style": {"fontFamily": "Arial, Helvetica, sans-serif"},
    "spacingLeft": 80,
    "spacingRight": 120,
    "spacingBottom": 60,
    "marginBottom": 250,
    "spacingTop": 40,
}

chart.options.title = {
    "text": "Water Phase Diagram \u00b7 phase-diagram-pt \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "42px", "fontWeight": "500", "color": "#333333"},
    "margin": 40,
}

chart.options.subtitle = {"text": None}

chart.options.x_axis = {
    "title": {"text": "Temperature (K)", "style": {"fontSize": "32px", "color": "#555555"}, "margin": 20},
    "labels": {"style": {"fontSize": "24px", "color": "#555555"}},
    "tickInterval": 50,
    "min": 180,
    "max": 780,
    "gridLineWidth": 0,
    "lineColor": "#cccccc",
    "lineWidth": 2,
    "tickWidth": 0,
}

chart.options.y_axis = {
    "type": "logarithmic",
    "title": {"text": "Pressure (Pa)", "style": {"fontSize": "32px", "color": "#555555"}, "margin": 20},
    "labels": {"style": {"fontSize": "24px", "color": "#555555"}},
    "min": 10,
    "max": 1e9,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0,0,0,0.08)",
    "lineColor": "#cccccc",
    "lineWidth": 2,
}

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "enabled": True,
    "headerFormat": "",
    "pointFormat": "<b>{series.name}</b><br>T: {point.x:.1f} K<br>P: {point.y:.2e} Pa",
    "style": {"fontSize": "22px"},
}

# Series data
sg_data = [[float(t), float(p)] for t, p in zip(temp_sg, pressure_sg, strict=True)]
lg_data = [[float(t), float(p)] for t, p in zip(temp_lg, pressure_lg, strict=True)]
sl_data = [[float(t), float(p)] for t, p in zip(temp_sl, pressure_sl, strict=True)]

chart.add_series(
    {
        "type": "line",
        "name": "Sublimation Curve",
        "data": sg_data,
        "color": "#306998",
        "lineWidth": 6,
        "marker": {"enabled": False},
        "enableMouseTracking": True,
        "states": {"hover": {"lineWidth": 7}},
    }
)

chart.add_series(
    {
        "type": "line",
        "name": "Vaporization Curve",
        "data": lg_data,
        "color": "#306998",
        "lineWidth": 6,
        "marker": {"enabled": False},
        "enableMouseTracking": True,
        "states": {"hover": {"lineWidth": 7}},
    }
)

chart.add_series(
    {
        "type": "line",
        "name": "Melting Curve",
        "data": sl_data,
        "color": "#306998",
        "lineWidth": 6,
        "marker": {"enabled": False},
        "enableMouseTracking": True,
        "states": {"hover": {"lineWidth": 7}},
    }
)

# Triple point
chart.add_series(
    {
        "type": "scatter",
        "name": "Triple Point",
        "data": [[float(triple_t), float(triple_p)]],
        "color": "#D64045",
        "marker": {"symbol": "circle", "radius": 18, "lineColor": "#ffffff", "lineWidth": 4},
        "dataLabels": {
            "enabled": True,
            "format": "Triple Point<br>(273.16 K, 611.7 Pa)",
            "style": {"fontSize": "28px", "fontWeight": "bold", "color": "#D64045", "textOutline": "3px white"},
            "align": "left",
            "x": 30,
            "y": -15,
        },
        "enableMouseTracking": True,
    }
)

# Critical point
chart.add_series(
    {
        "type": "scatter",
        "name": "Critical Point",
        "data": [[float(critical_t), float(critical_p)]],
        "color": "#E8963E",
        "marker": {"symbol": "diamond", "radius": 18, "lineColor": "#ffffff", "lineWidth": 4},
        "dataLabels": {
            "enabled": True,
            "format": "Critical Point<br>(647.1 K, 22.06 MPa)",
            "style": {"fontSize": "28px", "fontWeight": "bold", "color": "#E8963E", "textOutline": "3px white"},
            "align": "right",
            "x": -30,
            "y": -25,
        },
        "enableMouseTracking": True,
    }
)

# Phase region labels
phase_labels = [
    ("SOLID", [220, 8e6], "rgba(48,105,152,0.40)"),
    ("LIQUID", [420, 8e6], "rgba(48,105,152,0.40)"),
    ("GAS", [480, 50], "rgba(48,105,152,0.40)"),
    ("SUPERCRITICAL<br>FLUID", [690, 1e8], "rgba(48,105,152,0.30)"),
]

for label_text, pos, color in phase_labels:
    chart.add_series(
        {
            "type": "scatter",
            "name": label_text,
            "data": [[pos[0], pos[1]]],
            "color": "transparent",
            "marker": {"enabled": False},
            "dataLabels": {
                "enabled": True,
                "format": label_text,
                "style": {"fontSize": "40px", "fontWeight": "600", "color": color, "textOutline": "none"},
                "align": "center",
                "verticalAlign": "middle",
            },
            "enableMouseTracking": False,
        }
    )

chart.options.plot_options = {"series": {"animation": False}, "line": {"marker": {"enabled": False}}}

# Save interactive HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(chart.to_js_literal())

# PNG export via Selenium - download Highcharts JS from npm
subprocess.run(["npm", "pack", "highcharts", "--pack-destination", "/tmp"], capture_output=True, check=True)
hc_tarball = sorted(_glob.glob("/tmp/highcharts-*.tgz"))[-1]
subprocess.run(["tar", "-xzf", hc_tarball, "-C", "/tmp"], capture_output=True, check=True)
highcharts_js = Path("/tmp/package/highcharts.js").read_text(encoding="utf-8")

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0;">
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
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
