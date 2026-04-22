""" pyplots.ai
smith-chart-basic: Smith Chart for RF/Impedance
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-15
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


# Reference impedance
Z0 = 50.0

# Generate example impedance data: antenna impedance sweep 1-6 GHz
np.random.seed(42)
n_points = 50
frequencies = np.linspace(1e9, 6e9, n_points)  # 1-6 GHz

# Simulate a resonant antenna with varying impedance
# Near resonance around 3.5 GHz, impedance passes through Z0
f_res = 3.5e9
Q = 5.0
f_norm = (frequencies - f_res) / (f_res / Q)
z_real = Z0 * (1 + 0.3 * np.exp(-(f_norm**2)))
z_imag = Z0 * 0.8 * np.tanh(f_norm) * (1 + 0.2 * np.sin(2 * np.pi * frequencies / 1e9))

# Normalize impedance and convert to reflection coefficient (gamma)
z_normalized = (z_real + 1j * z_imag) / Z0
gamma = (z_normalized - 1) / (z_normalized + 1)

# Convert gamma to Cartesian coordinates for plotting
gamma_x = gamma.real
gamma_y = gamma.imag


def resistance_circle(r, n_points=200):
    """Generate points for a constant resistance circle on Smith chart."""
    center_x = r / (r + 1)
    radius = 1 / (r + 1)
    theta = np.linspace(0, 2 * np.pi, n_points)
    x = center_x + radius * np.cos(theta)
    y = radius * np.sin(theta)
    # Clip to unit circle
    valid = x**2 + y**2 <= 1.001
    x[~valid] = np.nan
    y[~valid] = np.nan
    return x, y


def reactance_arc(x_val, n_points=200):
    """Generate points for a constant reactance arc on Smith chart."""
    if abs(x_val) < 0.001:
        return np.array([-1, 1]), np.array([0, 0])
    # Center at (1, 1/x), radius |1/x|
    center_y = 1.0 / x_val
    radius = abs(1.0 / x_val)
    # Full circle parametrization
    theta = np.linspace(0, 2 * np.pi, n_points)
    x = 1.0 + radius * np.cos(theta)
    y = center_y + radius * np.sin(theta)
    # Clip to unit circle
    valid = x**2 + y**2 <= 1.001
    x[~valid] = np.nan
    y[~valid] = np.nan
    return x, y


# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for square 1:1 aspect ratio Smith chart
chart.options.chart = {
    "width": 3600,
    "height": 3600,
    "backgroundColor": "#ffffff",
    "spacingTop": 100,
    "spacingBottom": 200,
    "spacingLeft": 100,
    "spacingRight": 100,
}

# Title
chart.options.title = {
    "text": "smith-chart-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

chart.options.subtitle = {"text": "Antenna Impedance Sweep 1-6 GHz (Z₀ = 50Ω)", "style": {"fontSize": "32px"}}

# Axes with 1:1 aspect ratio for circular chart
chart.options.x_axis = {
    "title": {"text": "Real(Γ)", "style": {"fontSize": "28px"}},
    "labels": {"style": {"fontSize": "22px"}},
    "min": -1.2,
    "max": 1.2,
    "tickInterval": 0.5,
    "gridLineWidth": 0,
    "lineWidth": 0,
}

chart.options.y_axis = {
    "title": {"text": "Imag(Γ)", "style": {"fontSize": "28px"}},
    "labels": {"style": {"fontSize": "22px"}},
    "min": -1.2,
    "max": 1.2,
    "tickInterval": 0.5,
    "gridLineWidth": 0,
    "lineWidth": 0,
}

# Legend configuration
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "24px"},
    "verticalAlign": "bottom",
    "layout": "horizontal",
    "align": "center",
    "y": 60,
}

# Unit circle (|Γ| = 1) - the boundary
theta = np.linspace(0, 2 * np.pi, 300)
unit_x = np.cos(theta)
unit_y = np.sin(theta)
unit_circle = ScatterSeries()
unit_circle.data = [[float(x), float(y)] for x, y in zip(unit_x, unit_y, strict=True)]
unit_circle.name = "Unit Circle"
unit_circle.marker = {"enabled": False}
unit_circle.line_width = 3
unit_circle.color = "#333333"
unit_circle.enable_mouse_tracking = False
unit_circle.show_in_legend = False
chart.add_series(unit_circle)

# Resistance circles (R = 0, 0.2, 0.5, 1, 2, 5)
resistance_values = [0, 0.2, 0.5, 1, 2, 5]
for r in resistance_values:
    rx, ry = resistance_circle(r, 300)
    # Remove NaN values and split into valid segments
    valid_mask = ~np.isnan(rx) & ~np.isnan(ry)
    rx_valid = rx[valid_mask]
    ry_valid = ry[valid_mask]
    if len(rx_valid) > 1:
        r_series = ScatterSeries()
        r_series.data = [[float(x), float(y)] for x, y in zip(rx_valid, ry_valid, strict=True)]
        r_series.name = f"R={r}"
        r_series.marker = {"enabled": False}
        r_series.line_width = 1.5
        r_series.color = "#306998"
        r_series.dash_style = "Dot"
        r_series.enable_mouse_tracking = False
        r_series.show_in_legend = False
        chart.add_series(r_series)

# Reactance arcs (X = ±0.2, ±0.5, ±1, ±2)
reactance_values = [0.2, 0.5, 1, 2, -0.2, -0.5, -1, -2]
for x_val in reactance_values:
    xa, ya = reactance_arc(x_val, 300)
    valid_mask = ~np.isnan(xa) & ~np.isnan(ya)
    xa_valid = xa[valid_mask]
    ya_valid = ya[valid_mask]
    if len(xa_valid) > 1:
        x_series = ScatterSeries()
        x_series.data = [[float(x), float(y)] for x, y in zip(xa_valid, ya_valid, strict=True)]
        x_series.name = f"X={x_val}"
        x_series.marker = {"enabled": False}
        x_series.line_width = 1.5
        x_series.color = "#B8860B"
        x_series.dash_style = "Dot"
        x_series.enable_mouse_tracking = False
        x_series.show_in_legend = False
        chart.add_series(x_series)

# Horizontal axis (X = 0)
h_axis = ScatterSeries()
h_axis.data = [[-1.0, 0.0], [1.0, 0.0]]
h_axis.name = "Real Axis"
h_axis.marker = {"enabled": False}
h_axis.line_width = 2
h_axis.color = "#333333"
h_axis.enable_mouse_tracking = False
h_axis.show_in_legend = False
chart.add_series(h_axis)

# VSWR circles (constant |Γ|)
vswr_values = [1.5, 2.0, 3.0]
vswr_colors = ["#9467BD", "#17BECF", "#8C564B"]
for i, vswr in enumerate(vswr_values):
    gamma_mag = (vswr - 1) / (vswr + 1)
    v_theta = np.linspace(0, 2 * np.pi, 150)
    vx = gamma_mag * np.cos(v_theta)
    vy = gamma_mag * np.sin(v_theta)
    vswr_series = ScatterSeries()
    vswr_series.data = [[float(x), float(y)] for x, y in zip(vx, vy, strict=True)]
    vswr_series.name = f"VSWR={vswr:.1f}"
    vswr_series.marker = {"enabled": False}
    vswr_series.line_width = 2.5
    vswr_series.color = vswr_colors[i]
    vswr_series.dash_style = "ShortDash"
    vswr_series.enable_mouse_tracking = False
    vswr_series.show_in_legend = True
    chart.add_series(vswr_series)

# Match center marker (Z = Z0)
match_series = ScatterSeries()
match_series.data = [[0.0, 0.0]]
match_series.name = "Matched (Z=Z₀)"
match_series.marker = {"enabled": True, "radius": 14, "symbol": "diamond", "fillColor": "#27AE60"}
match_series.show_in_legend = True
chart.add_series(match_series)

# Plot impedance locus curve
impedance_series = ScatterSeries()
impedance_series.data = [[float(x), float(y)] for x, y in zip(gamma_x, gamma_y, strict=True)]
impedance_series.name = "Impedance Locus (1-6 GHz)"
impedance_series.marker = {"enabled": True, "radius": 8, "symbol": "circle"}
impedance_series.line_width = 4
impedance_series.color = "#E74C3C"
impedance_series.show_in_legend = True
chart.add_series(impedance_series)

# Add frequency labels at key points
freq_label_indices = [0, n_points // 4, n_points // 2, 3 * n_points // 4, n_points - 1]
freq_annotations = []
for idx in freq_label_indices:
    freq_ghz = frequencies[idx] / 1e9
    freq_annotations.append(
        {
            "point": {"x": float(gamma_x[idx]), "y": float(gamma_y[idx]), "xAxis": 0, "yAxis": 0},
            "text": f"{freq_ghz:.1f} GHz",
            "style": {"fontSize": "22px", "fontWeight": "bold"},
            "backgroundColor": "rgba(255, 255, 255, 0.9)",
            "borderWidth": 2,
            "borderColor": "#333333",
            "padding": 10,
        }
    )

chart.options.annotations = [{"labels": freq_annotations, "labelOptions": {"shape": "rect"}}]

# Export to PNG
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

annotations_url = "https://code.highcharts.com/modules/annotations.js"
with urllib.request.urlopen(annotations_url, timeout=30) as response:
    annotations_js = response.read().decode("utf-8")

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
    <script>{annotations_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
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
chrome_options.add_argument("--window-size=3600,3600")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)
