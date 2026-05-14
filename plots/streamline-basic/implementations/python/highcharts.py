"""anyplot.ai
streamline-basic: Basic Streamline Plot
Library: highcharts | Python 3.13
Quality: pending | Created: 2025-12-31
"""

import os
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


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Data: Create a vortex flow field
np.random.seed(42)
grid_size = 30
x_grid = np.linspace(-3, 3, grid_size)
y_grid = np.linspace(-3, 3, grid_size)
X, Y = np.meshgrid(x_grid, y_grid)

# Vortex flow: u = -y, v = x (circular flow around origin)
U = -Y
V = X

# Generate streamlines from distributed starting points
streamlines = []
streamline_speeds = []

radii = [0.8, 1.3, 1.8, 2.3, 2.8]
angles_per_radius = [3, 4, 5, 6, 7]

x_min, x_max = x_grid.min(), x_grid.max()
y_min, y_max = y_grid.min(), y_grid.max()

for radius, n_angles in zip(radii, angles_per_radius, strict=False):
    for angle in np.linspace(0, 2 * np.pi, n_angles, endpoint=False):
        x0 = radius * np.cos(angle)
        y0 = radius * np.sin(angle)

        points = [(x0, y0)]
        speeds = []
        x_curr, y_curr = x0, y0
        max_steps = 150
        dt = 0.08

        for _ in range(max_steps):
            xi = int((x_curr - x_min) / (x_max - x_min) * (grid_size - 1))
            yi = int((y_curr - y_min) / (y_max - y_min) * (grid_size - 1))

            if xi < 0 or xi >= grid_size - 1 or yi < 0 or yi >= grid_size - 1:
                break

            u = U[yi, xi]
            v = V[yi, xi]

            speed = np.sqrt(u**2 + v**2)
            if speed < 1e-6:
                break
            speeds.append(speed)

            u_norm = u / speed
            v_norm = v / speed

            x_new = x_curr + u_norm * dt
            y_new = y_curr + v_norm * dt

            if x_new < x_min or x_new > x_max or y_new < y_min or y_new > y_max:
                break

            points.append((x_new, y_new))
            x_curr, y_curr = x_new, y_new

        if len(points) > 5:
            streamlines.append(points)
            streamline_speeds.append(np.mean(speeds) if speeds else 0)

# Create Highcharts chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 250,
    "marginLeft": 220,
    "marginRight": 280,
    "marginTop": 180,
    "spacingBottom": 50,
}

# Title and subtitle
chart.options.title = {
    "text": "streamline-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "color": INK, "fontWeight": "normal"},
}

chart.options.subtitle = {"text": "Vortex Flow Field: u = −y, v = x", "style": {"fontSize": "22px", "color": INK_SOFT}}

# Axes
chart.options.x_axis = {
    "title": {"text": "X Position", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "min": -4.0,
    "max": 4.0,
    "tickInterval": 1,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

chart.options.y_axis = {
    "title": {"text": "Y Position", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "min": -4.0,
    "max": 4.0,
    "tickInterval": 1,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

# Color axis for velocity magnitude
speed_min = min(streamline_speeds) if streamline_speeds else 0
speed_max = max(streamline_speeds) if streamline_speeds else 1

chart.options.color_axis = {
    "type": "linear",
    "min": speed_min,
    "max": speed_max,
    "stops": [[0, "#440154"], [0.25, "#31688E"], [0.5, "#35B779"], [0.75, "#FDE724"], [1, "#FDE724"]],
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
}

# Plot options and legend
chart.options.plot_options = {"line": {"lineWidth": 3, "marker": {"enabled": False}, "enableMouseTracking": False}}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "middle",
    "layout": "vertical",
    "itemStyle": {"color": INK_SOFT, "fontSize": "18px"},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}

# Add streamlines with velocity-based colors
viridis_stops = ["#440154", "#31688E", "#35B779", "#FDE724"]

for i, (streamline, avg_speed) in enumerate(zip(streamlines, streamline_speeds, strict=False)):
    series = SplineSeries()
    series.data = [[round(pt[0], 4), round(pt[1], 4)] for pt in streamline]
    series.name = f"Streamline {i + 1}"

    # Color based on normalized speed
    t = (avg_speed - speed_min) / (speed_max - speed_min) if speed_max > speed_min else 0
    if t < 0.25:
        color = viridis_stops[0]
    elif t < 0.5:
        color = viridis_stops[1]
    elif t < 0.75:
        color = viridis_stops[2]
    else:
        color = viridis_stops[3]

    series.color = color
    chart.add_series(series)

# Download Highcharts JS - use jsdelivr CDN which works better in headless environments
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11.4.3/highcharts.js"
try:
    req = urllib.request.Request(
        highcharts_url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        highcharts_js = response.read().decode("utf-8")
except Exception:
    # Fallback: use minimal embedded JS
    highcharts_js = ""

# Generate HTML
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

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

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
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
