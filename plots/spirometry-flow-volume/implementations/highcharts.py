""" pyplots.ai
spirometry-flow-volume: Spirometry Flow-Volume Loop
Library: highcharts unknown | Python 3.14.3
Quality: 84/100 | Created: 2026-03-18
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Spirometry flow-volume loop
np.random.seed(42)
n_points = 150

# Measured flow-volume loop
fvc = 4.8  # Forced Vital Capacity in liters
pef = 9.5  # Peak Expiratory Flow in L/s
fev1_volume = 3.6  # FEV1 volume marker

# Expiratory limb: sharp rise to PEF then roughly linear decline
vol_exp = np.linspace(0, fvc, n_points)
t_peak = 0.08  # PEF occurs early (~8% of FVC)
peak_idx = int(t_peak * n_points)

# Rising phase to PEF
flow_rise = pef * np.sin(np.linspace(0, np.pi / 2, peak_idx + 1))
# Declining phase from PEF to zero
flow_decline = pef * (1 - np.linspace(0, 1, n_points - peak_idx)) ** 0.85
flow_exp = np.concatenate([flow_rise, flow_decline[1:]])
flow_exp += np.random.normal(0, 0.05, n_points)
flow_exp = np.clip(flow_exp, 0, None)
flow_exp[0] = 0
flow_exp[-1] = 0

# Inspiratory limb: symmetric U-shaped curve (negative flow)
vol_insp = np.linspace(fvc, 0, n_points)
pif = -6.0  # Peak Inspiratory Flow
flow_insp = pif * np.sin(np.linspace(0, np.pi, n_points))
flow_insp += np.random.normal(0, 0.04, n_points)
flow_insp = np.clip(flow_insp, None, 0)
flow_insp[0] = 0
flow_insp[-1] = 0

# Predicted normal loop (slightly larger/better values)
pred_fvc = 5.2
pred_pef = 10.8
vol_pred_exp = np.linspace(0, pred_fvc, n_points)
t_peak_pred = 0.08
peak_idx_pred = int(t_peak_pred * n_points)
flow_pred_rise = pred_pef * np.sin(np.linspace(0, np.pi / 2, peak_idx_pred + 1))
flow_pred_decline = pred_pef * (1 - np.linspace(0, 1, n_points - peak_idx_pred)) ** 0.85
flow_pred_exp = np.concatenate([flow_pred_rise, flow_pred_decline[1:]])

vol_pred_insp = np.linspace(pred_fvc, 0, n_points)
pred_pif = -7.0
flow_pred_insp = pred_pif * np.sin(np.linspace(0, np.pi, n_points))

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 280,
    "marginLeft": 280,
    "marginRight": 200,
    "marginTop": 280,
}

chart.options.title = {
    "text": "spirometry-flow-volume · highcharts · pyplots.ai",
    "style": {"fontSize": "56px", "fontWeight": "bold"},
}

chart.options.subtitle = {
    "text": "Measured vs Predicted Normal · FVC: 4.80 L · FEV1: 3.60 L · PEF: 9.50 L/s",
    "style": {"fontSize": "36px", "color": "#666666"},
}

# X-axis
chart.options.x_axis = {
    "title": {"text": "Volume (L)", "style": {"fontSize": "44px"}, "margin": 25},
    "labels": {"style": {"fontSize": "34px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.06)",
    "min": -0.2,
    "max": 5.6,
    "tickInterval": 0.5,
    "plotLines": [{"value": 0, "color": "rgba(0, 0, 0, 0.3)", "width": 2}],
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Flow (L/s)", "style": {"fontSize": "44px"}},
    "labels": {"style": {"fontSize": "34px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.06)",
    "min": -8,
    "max": 12,
    "tickInterval": 2,
    "plotLines": [{"value": 0, "color": "rgba(0, 0, 0, 0.4)", "width": 3, "zIndex": 3}],
}

# Plot options
chart.options.plot_options = {
    "line": {"marker": {"enabled": False}, "lineWidth": 6, "states": {"hover": {"lineWidthPlus": 1}}},
    "scatter": {"marker": {"radius": 16, "lineWidth": 3, "lineColor": "#ffffff"}},
}

chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "36px"},
    "symbolWidth": 60,
    "y": 10,
    "x": 0,
    "align": "center",
    "verticalAlign": "bottom",
    "floating": False,
}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "style": {"fontSize": "28px"},
    "backgroundColor": "rgba(255, 255, 255, 0.95)",
    "borderRadius": 8,
    "headerFormat": "",
    "pointFormat": "Volume: <b>{point.x:.2f} L</b><br/>Flow: <b>{point.y:.2f} L/s</b>",
}

# Measured expiratory limb
exp_series = LineSeries()
exp_series.data = [[round(float(v), 3), round(float(f), 3)] for v, f in zip(vol_exp, flow_exp, strict=True)]
exp_series.name = "Measured (Expiratory)"
exp_series.color = "#306998"
exp_series.line_width = 6
chart.add_series(exp_series)

# Measured inspiratory limb
insp_series = LineSeries()
insp_series.data = [[round(float(v), 3), round(float(f), 3)] for v, f in zip(vol_insp, flow_insp, strict=True)]
insp_series.name = "Measured (Inspiratory)"
insp_series.color = "#306998"
insp_series.dash_style = "Solid"
insp_series.line_width = 6
insp_series.show_in_legend = False
chart.add_series(insp_series)

# Predicted expiratory limb
pred_exp_series = LineSeries()
pred_exp_series.data = [
    [round(float(v), 3), round(float(f), 3)] for v, f in zip(vol_pred_exp, flow_pred_exp, strict=True)
]
pred_exp_series.name = "Predicted Normal"
pred_exp_series.color = "#999999"
pred_exp_series.dash_style = "Dash"
pred_exp_series.line_width = 4
chart.add_series(pred_exp_series)

# Predicted inspiratory limb
pred_insp_series = LineSeries()
pred_insp_series.data = [
    [round(float(v), 3), round(float(f), 3)] for v, f in zip(vol_pred_insp, flow_pred_insp, strict=True)
]
pred_insp_series.name = "Predicted Normal (Insp)"
pred_insp_series.color = "#999999"
pred_insp_series.dash_style = "Dash"
pred_insp_series.line_width = 4
pred_insp_series.show_in_legend = False
chart.add_series(pred_insp_series)

# PEF marker point
pef_idx = np.argmax(flow_exp)
pef_val = round(float(flow_exp[pef_idx]), 1)
pef_marker = ScatterSeries()
pef_marker.data = [
    {
        "x": round(float(vol_exp[pef_idx]), 3),
        "y": round(float(flow_exp[pef_idx]), 3),
        "dataLabels": {
            "enabled": True,
            "format": f"PEF: {pef_val} L/s",
            "style": {"fontSize": "36px", "fontWeight": "bold", "color": "#c0392b"},
            "x": 30,
            "y": -35,
        },
    }
]
pef_marker.name = "PEF"
pef_marker.color = "#c0392b"
pef_marker.marker = {"symbol": "circle", "radius": 16, "fillColor": "#c0392b", "lineWidth": 3, "lineColor": "#ffffff"}
pef_marker.show_in_legend = False
chart.add_series(pef_marker)

# FEV1 marker - find the volume closest to FEV1
fev1_idx = np.argmin(np.abs(vol_exp - fev1_volume))
fev1_marker = ScatterSeries()
fev1_marker.data = [
    {
        "x": round(float(vol_exp[fev1_idx]), 3),
        "y": round(float(flow_exp[fev1_idx]), 3),
        "dataLabels": {
            "enabled": True,
            "format": f"FEV1: {fev1_volume:.1f} L",
            "style": {"fontSize": "36px", "fontWeight": "bold", "color": "#2980b9"},
            "x": 35,
            "y": -10,
        },
    }
]
fev1_marker.name = "FEV1"
fev1_marker.color = "#2980b9"
fev1_marker.marker = {"symbol": "diamond", "radius": 16, "fillColor": "#2980b9", "lineWidth": 3, "lineColor": "#ffffff"}
fev1_marker.show_in_legend = False
chart.add_series(fev1_marker)

# Load Highcharts JS for inline embedding
html_str = chart.to_js_literal()

highcharts_js_path = Path(__file__).resolve().parents[3] / "node_modules" / "highcharts" / "highcharts.js"
if highcharts_js_path.exists():
    highcharts_js = highcharts_js_path.read_text(encoding="utf-8")
else:
    highcharts_url = "https://code.highcharts.com/highcharts.js"
    req = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        highcharts_js = response.read().decode("utf-8")

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

# Screenshot with headless Chrome
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

# Save interactive HTML
with open("plot.html", "w", encoding="utf-8") as f:
    interactive_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(interactive_html)
