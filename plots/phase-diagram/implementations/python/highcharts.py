""" pyplots.ai
phase-diagram: Phase Diagram (State Space Plot)
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
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


# Data - Damped harmonic oscillator: d²x/dt² + 2*gamma*dx/dt + omega²*x = 0
np.random.seed(42)

# Physical parameters
omega = 2.0  # Natural frequency
gamma = 0.15  # Damping coefficient (underdamped)
omega_d = np.sqrt(omega**2 - gamma**2)  # Damped frequency

# Time array
t = np.linspace(0, 15, 500)

# Three trajectories with different initial conditions
trajectories = []
colors = ["#306998", "#FFD43B", "#9467BD"]
names = ["High energy start", "Medium energy start", "Low energy start"]

initial_conditions = [
    (3.0, 0.0),  # x0=3.0, v0=0
    (-2.0, 2.5),  # x0=-2.0, v0=2.5
    (0.0, -2.0),  # x0=0.0, v0=-2.0
]

for x0, v0 in initial_conditions:
    # Analytical solution for underdamped harmonic oscillator
    # x(t) = e^(-gamma*t) * [A*cos(omega_d*t) + B*sin(omega_d*t)]
    A = x0
    B = (v0 + gamma * x0) / omega_d

    x = np.exp(-gamma * t) * (A * np.cos(omega_d * t) + B * np.sin(omega_d * t))
    dx_dt = np.exp(-gamma * t) * (
        -gamma * (A * np.cos(omega_d * t) + B * np.sin(omega_d * t))
        + omega_d * (-A * np.sin(omega_d * t) + B * np.cos(omega_d * t))
    )
    trajectories.append((x, dx_dt))

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 300,
}

# Title
chart.options.title = {
    "text": "phase-diagram · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

chart.options.subtitle = {
    "text": "Damped Harmonic Oscillator - Phase Space Trajectories",
    "style": {"fontSize": "32px"},
}

# Axes
chart.options.x_axis = {
    "title": {"text": "Position x", "style": {"fontSize": "36px"}, "margin": 30},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "lineWidth": 2,
    "lineColor": "#333333",
    "tickWidth": 2,
    "plotLines": [{"value": 0, "width": 2, "color": "#888888", "dashStyle": "Dash"}],
}

chart.options.y_axis = {
    "title": {"text": "Velocity dx/dt", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "lineWidth": 2,
    "lineColor": "#333333",
    "plotLines": [{"value": 0, "width": 2, "color": "#888888", "dashStyle": "Dash"}],
}

# Plot options
chart.options.plot_options = {
    "scatter": {"marker": {"radius": 4, "symbol": "circle"}, "lineWidth": 3, "states": {"hover": {"lineWidth": 4}}}
}

# Legend
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "middle",
    "layout": "vertical",
    "itemStyle": {"fontSize": "28px"},
}

# Credits
chart.options.credits = {"enabled": False}

# Add series for each trajectory
for i, (x, dx_dt) in enumerate(trajectories):
    series = ScatterSeries()
    series.data = [{"x": float(xi), "y": float(dxi)} for xi, dxi in zip(x, dx_dt, strict=True)]
    series.name = names[i]
    series.color = colors[i]
    series.line_width = 3
    series.marker = {"radius": 3, "enabled": True, "symbol": "circle"}
    chart.add_series(series)

# Add fixed point marker at origin (equilibrium)
fixed_point_series = ScatterSeries()
fixed_point_series.data = [{"x": 0.0, "y": 0.0}]
fixed_point_series.name = "Equilibrium (fixed point)"
fixed_point_series.color = "#E53935"
fixed_point_series.marker = {"radius": 16, "symbol": "diamond", "lineWidth": 3, "lineColor": "#B71C1C"}
chart.add_series(fixed_point_series)

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
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
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)
