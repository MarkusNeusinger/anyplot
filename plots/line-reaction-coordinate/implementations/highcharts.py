""" pyplots.ai
line-reaction-coordinate: Reaction Coordinate Energy Diagram
Library: highcharts unknown | Python 3.14.3
Quality: 83/100 | Created: 2026-03-21
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.spline import SplineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Single-step exothermic reaction energy profile
reactant_energy = 50.0  # kJ/mol
product_energy = 20.0  # kJ/mol
transition_state_energy = 120.0  # kJ/mol

activation_energy = transition_state_energy - reactant_energy  # Ea = 70 kJ/mol
delta_h = product_energy - reactant_energy  # ΔH = -30 kJ/mol

# Generate smooth reaction coordinate curve
reaction_coord = np.linspace(0, 1, 300)

# Energy profile using piecewise construction to avoid unphysical dips
# Plateau regions + smooth Hermite interpolation through transition state
energy = np.full_like(reaction_coord, reactant_energy)

plateau_end = 0.15
rise_end = 0.45  # transition state peak
fall_end = 0.85

for i, rc in enumerate(reaction_coord):
    if rc <= plateau_end:
        energy[i] = reactant_energy
    elif rc <= rise_end:
        # Smooth rise from reactant level to transition state (monotonic)
        t = (rc - plateau_end) / (rise_end - plateau_end)
        t_smooth = t * t * (3 - 2 * t)  # Hermite smoothstep
        energy[i] = reactant_energy + (transition_state_energy - reactant_energy) * t_smooth
    elif rc <= fall_end:
        # Smooth fall from transition state to product level (monotonic)
        t = (rc - rise_end) / (fall_end - rise_end)
        t_smooth = t * t * (3 - 2 * t)
        energy[i] = transition_state_energy - (transition_state_energy - product_energy) * t_smooth
    else:
        energy[i] = product_energy

# Find actual transition state position
ts_idx = np.argmax(energy)
ts_rc = float(reaction_coord[ts_idx])
ts_energy = float(energy[ts_idx])

# Plot
chart = Chart(container="container")
chart.options = HighchartsOptions()

ea_arrow_x = 0.20
dh_arrow_x = 0.80

chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "spacingTop": 80,
    "spacingBottom": 100,
    "spacingLeft": 100,
    "spacingRight": 120,
    "style": {"fontFamily": "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"},
}

chart.options.title = {
    "text": "line-reaction-coordinate \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "600", "color": "#1a1a2e"},
}

chart.options.x_axis = {
    "title": {
        "text": "Reaction Coordinate",
        "style": {"fontSize": "36px", "fontWeight": "600", "color": "#333333"},
        "margin": 24,
    },
    "labels": {"enabled": False},
    "min": -0.05,
    "max": 1.05,
    "lineColor": "#999999",
    "lineWidth": 2,
    "tickLength": 0,
    "gridLineWidth": 0,
}

chart.options.y_axis = {
    "title": {
        "text": "Potential Energy (kJ/mol)",
        "style": {"fontSize": "36px", "fontWeight": "600", "color": "#333333"},
        "margin": 24,
    },
    "labels": {"style": {"fontSize": "28px", "color": "#444444"}},
    "min": 0,
    "max": 135,
    "gridLineWidth": 0,
    "lineColor": "#999999",
    "lineWidth": 2,
    "tickColor": "#999999",
    "plotLines": [
        {"value": reactant_energy, "color": "#aaaaaa", "width": 2, "dashStyle": "Dash", "zIndex": 1},
        {"value": product_energy, "color": "#aaaaaa", "width": 2, "dashStyle": "Dash", "zIndex": 1},
    ],
}

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}
chart.options.tooltip = {"enabled": False}

chart.options.plot_options = {
    "spline": {"lineWidth": 5, "marker": {"enabled": False}, "states": {"hover": {"lineWidth": 6}}}
}

# Energy curve series
curve_data = [[float(rc), float(e)] for rc, e in zip(reaction_coord, energy, strict=False)]
energy_series = SplineSeries()
energy_series.data = curve_data
energy_series.name = "Energy Profile"
energy_series.color = "#306998"
energy_series.line_width = 5
chart.add_series(energy_series)

# Generate JS literal
html_str = chart.to_js_literal()

# Build annotations with proper xAxis/yAxis bindings for data coordinates
ea_mid_y = (reactant_energy + ts_energy) / 2
dh_mid_y = (reactant_energy + product_energy) / 2

annotations_js = f"""
    annotations: [{{
        draggable: '',
        labelOptions: {{
            allowOverlap: true,
            overflow: 'allow',
            crop: false
        }},
        labels: [{{
            point: {{xAxis: 0, yAxis: 0, x: {ts_rc}, y: {ts_energy}}},
            text: 'Transition State (\u2021)',
            style: {{fontSize: '32px', fontWeight: '700', color: '#d35400'}},
            backgroundColor: 'rgba(255,255,255,0.92)',
            borderColor: '#d35400',
            borderWidth: 2,
            borderRadius: 8,
            padding: 14,
            y: -55
        }}, {{
            point: {{xAxis: 0, yAxis: 0, x: 0.06, y: {reactant_energy}}},
            text: 'Reactants',
            style: {{fontSize: '34px', fontWeight: '700', color: '#306998'}},
            backgroundColor: 'rgba(255,255,255,0)',
            borderWidth: 0,
            y: -40
        }}, {{
            point: {{xAxis: 0, yAxis: 0, x: 0.94, y: {product_energy}}},
            text: 'Products',
            style: {{fontSize: '34px', fontWeight: '700', color: '#306998'}},
            backgroundColor: 'rgba(255,255,255,0)',
            borderWidth: 0,
            y: -40
        }}, {{
            point: {{xAxis: 0, yAxis: 0, x: {ea_arrow_x}, y: {ea_mid_y}}},
            text: 'E\u2090 = {int(activation_energy)} kJ/mol',
            style: {{fontSize: '30px', fontWeight: '700', color: '#d35400'}},
            backgroundColor: 'rgba(255,255,255,0.95)',
            borderColor: '#d35400',
            borderWidth: 2,
            borderRadius: 8,
            padding: 12,
            x: -200,
            y: 0
        }}, {{
            point: {{xAxis: 0, yAxis: 0, x: {dh_arrow_x}, y: {dh_mid_y}}},
            text: '\u0394H = {int(delta_h)} kJ/mol',
            style: {{fontSize: '30px', fontWeight: '700', color: '#2980b9'}},
            backgroundColor: 'rgba(255,255,255,0.95)',
            borderColor: '#2980b9',
            borderWidth: 2,
            borderRadius: 8,
            padding: 12,
            x: 140,
            y: 0
        }}],
        shapes: [{{
            type: 'path',
            points: [
                {{xAxis: 0, yAxis: 0, x: {ea_arrow_x}, y: {reactant_energy}}},
                {{xAxis: 0, yAxis: 0, x: {ea_arrow_x}, y: {ts_energy}}}
            ],
            stroke: '#d35400',
            strokeWidth: 4,
            markerEnd: 'arrow',
            markerStart: 'arrow'
        }}, {{
            type: 'path',
            points: [
                {{xAxis: 0, yAxis: 0, x: {dh_arrow_x}, y: {product_energy}}},
                {{xAxis: 0, yAxis: 0, x: {dh_arrow_x}, y: {reactant_energy}}}
            ],
            stroke: '#2980b9',
            strokeWidth: 4,
            markerEnd: 'arrow',
            markerStart: 'arrow'
        }}]
    }}],
"""

# Inject annotations into the chart options JS
html_str = html_str.replace("credits: {", annotations_js + "\n  credits: {")

# Download Highcharts JS and annotations module
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
hc_req = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(hc_req, timeout=30) as resp:
    highcharts_js = resp.read().decode("utf-8")

annotations_url = "https://cdn.jsdelivr.net/npm/highcharts@11/modules/annotations.js"
ann_req = urllib.request.Request(annotations_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(ann_req, timeout=30) as resp:
    annotations_module_js = resp.read().decode("utf-8")

# Build HTML
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{annotations_module_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

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
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
