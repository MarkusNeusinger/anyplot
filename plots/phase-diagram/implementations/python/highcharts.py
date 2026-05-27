""" anyplot.ai
phase-diagram: Phase Diagram (State Space Plot)
Library: highcharts unknown | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-14
"""

import os
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


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Damped harmonic oscillator: d²x/dt² + 2*gamma*dx/dt + omega²*x = 0
np.random.seed(42)

omega = 2.0
gamma = 0.15
omega_d = np.sqrt(omega**2 - gamma**2)

t = np.linspace(0, 15, 500)

trajectories = []
names = ["High energy", "Medium energy", "Low energy"]

initial_conditions = [(3.0, 0.0), (-2.0, 2.5), (0.0, -2.0)]

for x0, v0 in initial_conditions:
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

chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 200,
    "marginLeft": 200,
    "marginRight": 200,
}

chart.options.title = {
    "text": "phase-diagram · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "color": INK, "fontWeight": "normal"},
}

chart.options.x_axis = {
    "title": {"text": "Position (m)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "lineWidth": 1,
    "tickColor": INK_SOFT,
    "tickWidth": 1,
    "gridLineColor": GRID,
    "gridLineWidth": 1,
    "plotLines": [{"value": 0, "width": 2, "color": INK_MUTED, "dashStyle": "Dash", "zIndex": 2}],
}

chart.options.y_axis = {
    "title": {"text": "Velocity (m/s)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "lineWidth": 1,
    "tickColor": INK_SOFT,
    "tickWidth": 1,
    "gridLineColor": GRID,
    "gridLineWidth": 1,
    "plotLines": [{"value": 0, "width": 2, "color": INK_MUTED, "dashStyle": "Dash", "zIndex": 2}],
}

chart.options.plot_options = {
    "scatter": {
        "marker": {"radius": 6, "enabled": True},
        "states": {"hover": {"marker": {"radius": 8}}},
        "lineWidth": 2,
    }
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "middle",
    "layout": "vertical",
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "padding": 15,
}

chart.options.colors = IMPRINT

chart.options.credits = {"enabled": False}

# Add series for each trajectory
for i, (x, dx_dt) in enumerate(trajectories):
    series = ScatterSeries()
    series.data = [{"x": float(xi), "y": float(dxi)} for xi, dxi in zip(x, dx_dt, strict=False)]
    series.name = names[i]
    series.color = IMPRINT[i]
    series.line_width = 2
    series.marker = {"radius": 4, "enabled": True}
    chart.add_series(series)

# Add fixed point marker at origin
fixed_point_series = ScatterSeries()
fixed_point_series.data = [{"x": 0.0, "y": 0.0}]
fixed_point_series.name = "Equilibrium"
fixed_point_series.color = INK_MUTED
fixed_point_series.marker = {"radius": 10, "symbol": "circle", "lineWidth": 2, "lineColor": INK}
chart.add_series(fixed_point_series)

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
highcharts_js = ""
try:
    req = urllib.request.Request(
        highcharts_url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        highcharts_js = response.read().decode("utf-8")
except Exception:
    # Fallback: use a minimal Highcharts script
    highcharts_js = "window.Highcharts = {};"

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

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
