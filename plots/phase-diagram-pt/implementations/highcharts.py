""" pyplots.ai
phase-diagram-pt: Thermodynamic Phase Diagram (Pressure-Temperature)
Library: highcharts unknown | Python 3.14.3
Quality: 89/100 | Created: 2026-03-14
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
temp_sg = np.linspace(190, 273.16, 80)
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

# Intentional color palette for each boundary
color_sublimation = "#306998"  # Python blue
color_vaporization = "#D64045"  # Warm red
color_melting = "#2D936C"  # Teal green

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#fafafa",
    "style": {"fontFamily": "'Segoe UI', Arial, Helvetica, sans-serif"},
    "spacingLeft": 80,
    "spacingRight": 80,
    "spacingBottom": 60,
    "marginBottom": 220,
    "spacingTop": 40,
}

chart.options.title = {
    "text": "Water Phase Diagram · phase-diagram-pt · highcharts · pyplots.ai",
    "style": {"fontSize": "42px", "fontWeight": "600", "color": "#2c3e50"},
    "margin": 40,
}

chart.options.subtitle = {"text": None}

chart.options.x_axis = {
    "title": {"text": "Temperature (K)", "style": {"fontSize": "32px", "color": "#4a5568"}, "margin": 20},
    "labels": {"style": {"fontSize": "24px", "color": "#4a5568"}},
    "tickInterval": 50,
    "min": 180,
    "max": 750,
    "gridLineWidth": 0,
    "lineColor": "#cbd5e0",
    "lineWidth": 2,
    "tickWidth": 0,
    "plotBands": [
        {"from": 180, "to": 273.16, "color": "rgba(48, 105, 152, 0.06)"},
        {"from": 647.1, "to": 750, "color": "rgba(230, 126, 34, 0.06)"},
    ],
}

chart.options.y_axis = {
    "type": "logarithmic",
    "title": {"text": "Pressure (Pa)", "style": {"fontSize": "32px", "color": "#4a5568"}, "margin": 20},
    "labels": {"style": {"fontSize": "24px", "color": "#4a5568"}},
    "min": 10,
    "max": 1e9,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0,0,0,0.06)",
    "gridLineDashStyle": "Dot",
    "lineColor": "#cbd5e0",
    "lineWidth": 2,
}

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "enabled": True,
    "headerFormat": "",
    "pointFormat": "<b>{series.name}</b><br>T: {point.x:.1f} K<br>P: {point.y:.2e} Pa",
    "style": {"fontSize": "22px"},
    "backgroundColor": "rgba(255,255,255,0.95)",
    "borderColor": "#cbd5e0",
    "borderRadius": 8,
    "shadow": {"color": "rgba(0,0,0,0.1)", "offsetX": 2, "offsetY": 2, "width": 6},
}

# Series data
sg_data = [[float(t), float(p)] for t, p in zip(temp_sg, pressure_sg, strict=True)]
lg_data = [[float(t), float(p)] for t, p in zip(temp_lg, pressure_lg, strict=True)]
sl_data = [[float(t), float(p)] for t, p in zip(temp_sl, pressure_sl, strict=True)]

# Gas region shading - area fill below sublimation + vaporization curves
gas_boundary_data = sg_data + lg_data
chart.add_series(
    {
        "type": "area",
        "name": "Gas Region",
        "data": gas_boundary_data,
        "threshold": 10,
        "fillColor": "rgba(46, 204, 113, 0.08)",
        "lineWidth": 0,
        "marker": {"enabled": False},
        "enableMouseTracking": False,
        "showInLegend": False,
    }
)

# Liquid region shading - area fill above vaporization curve (approximate)
liquid_fill_data = [[float(t), float(p)] for t, p in zip(temp_lg, pressure_lg, strict=True)]
chart.add_series(
    {
        "type": "area",
        "name": "Liquid Region",
        "data": liquid_fill_data,
        "threshold": 1e9,
        "fillColor": "rgba(52, 152, 219, 0.07)",
        "lineWidth": 0,
        "marker": {"enabled": False},
        "enableMouseTracking": False,
        "showInLegend": False,
    }
)

# Boundary curves with distinct colors
chart.add_series(
    {
        "type": "line",
        "name": "Sublimation Curve",
        "data": sg_data,
        "color": color_sublimation,
        "lineWidth": 6,
        "dashStyle": "ShortDash",
        "marker": {"enabled": False},
        "enableMouseTracking": True,
        "states": {"hover": {"lineWidth": 8}},
        "showInLegend": False,
        "zIndex": 5,
    }
)

chart.add_series(
    {
        "type": "line",
        "name": "Vaporization Curve",
        "data": lg_data,
        "color": color_vaporization,
        "lineWidth": 6,
        "marker": {"enabled": False},
        "enableMouseTracking": True,
        "states": {"hover": {"lineWidth": 8}},
        "showInLegend": False,
        "zIndex": 5,
    }
)

chart.add_series(
    {
        "type": "line",
        "name": "Melting Curve",
        "data": sl_data,
        "color": color_melting,
        "lineWidth": 6,
        "marker": {"enabled": False},
        "enableMouseTracking": True,
        "states": {"hover": {"lineWidth": 8}},
        "showInLegend": False,
        "zIndex": 5,
    }
)

# Triple point with annotation
chart.add_series(
    {
        "type": "scatter",
        "name": "Triple Point",
        "data": [[float(triple_t), float(triple_p)]],
        "color": "#8e44ad",
        "marker": {"symbol": "circle", "radius": 20, "lineColor": "#ffffff", "lineWidth": 4, "fillColor": "#8e44ad"},
        "dataLabels": {
            "enabled": True,
            "useHTML": True,
            "format": (
                '<div style="background:rgba(142,68,173,0.9);color:#fff;padding:10px 18px;'
                "border-radius:8px;font-size:26px;font-weight:600;line-height:1.4;"
                'box-shadow:0 3px 12px rgba(0,0,0,0.15);">'
                "Triple Point<br>"
                '<span style="font-weight:400;font-size:22px;">273.16 K, 611.7 Pa</span>'
                "</div>"
            ),
            "align": "left",
            "x": 35,
            "y": -10,
        },
        "enableMouseTracking": True,
        "showInLegend": False,
        "zIndex": 10,
    }
)

# Critical point with annotation
chart.add_series(
    {
        "type": "scatter",
        "name": "Critical Point",
        "data": [[float(critical_t), float(critical_p)]],
        "color": "#e67e22",
        "marker": {"symbol": "diamond", "radius": 20, "lineColor": "#ffffff", "lineWidth": 4, "fillColor": "#e67e22"},
        "dataLabels": {
            "enabled": True,
            "useHTML": True,
            "format": (
                '<div style="background:rgba(230,126,34,0.9);color:#fff;padding:10px 18px;'
                "border-radius:8px;font-size:26px;font-weight:600;line-height:1.4;"
                'box-shadow:0 3px 12px rgba(0,0,0,0.15);">'
                "Critical Point<br>"
                '<span style="font-weight:400;font-size:22px;">647.1 K, 22.06 MPa</span>'
                "</div>"
            ),
            "align": "right",
            "x": -35,
            "y": -20,
        },
        "enableMouseTracking": True,
        "showInLegend": False,
        "zIndex": 10,
    }
)

# Phase region labels with distinct colors matching their regions
phase_labels = [
    ("SOLID", [215, 3e7], "#306998", "700"),
    ("LIQUID", [400, 2e7], "#2980b9", "700"),
    ("GAS", [500, 30], "#27ae60", "700"),
    ("SUPERCRITICAL<br>FLUID", [700, 2e8], "#e67e22", "600"),
]

for label_text, pos, color, weight in phase_labels:
    chart.add_series(
        {
            "type": "scatter",
            "name": label_text.replace("<br>", " "),
            "data": [[pos[0], pos[1]]],
            "color": "transparent",
            "marker": {"enabled": False},
            "dataLabels": {
                "enabled": True,
                "format": label_text,
                "style": {
                    "fontSize": "44px",
                    "fontWeight": weight,
                    "color": color,
                    "textOutline": "3px rgba(250,250,250,0.8)",
                    "letterSpacing": "3px",
                },
                "align": "center",
                "verticalAlign": "middle",
            },
            "enableMouseTracking": False,
            "showInLegend": False,
        }
    )

# Curve legend in bottom-right using HTML annotations
chart.add_series(
    {
        "type": "scatter",
        "name": "Legend",
        "data": [[680, 600]],
        "color": "transparent",
        "marker": {"enabled": False},
        "dataLabels": {
            "enabled": True,
            "useHTML": True,
            "format": (
                '<div style="font-size:22px;line-height:2.0;color:#4a5568;">'
                f'<span style="color:{color_sublimation};font-weight:700;">── ──</span> Sublimation<br>'
                f'<span style="color:{color_vaporization};font-weight:700;">─────</span> Vaporization<br>'
                f'<span style="color:{color_melting};font-weight:700;">─────</span> Melting'
                "</div>"
            ),
            "align": "left",
        },
        "enableMouseTracking": False,
        "showInLegend": False,
    }
)

chart.options.plot_options = {
    "series": {"animation": False},
    "line": {"marker": {"enabled": False}},
    "area": {"marker": {"enabled": False}},
}

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
