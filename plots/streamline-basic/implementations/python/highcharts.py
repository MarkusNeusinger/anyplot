""" pyplots.ai
streamline-basic: Basic Streamline Plot
Library: highcharts unknown | Python 3.13.11
Quality: 90/100 | Created: 2025-12-31
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Create a vortex flow field
np.random.seed(42)
grid_size = 30
x_grid = np.linspace(-3, 3, grid_size)
y_grid = np.linspace(-3, 3, grid_size)
X, Y = np.meshgrid(x_grid, y_grid)

# Vortex flow: u = -y, v = x (circular flow around origin)
U = -Y
V = X

# Generate streamlines from distributed starting points at varying radii
streamlines = []
streamline_speeds = []  # Track average speed for color encoding

# Use different radii for varied circular patterns
# Reduce inner streamlines to prevent dense packing that makes paths hard to distinguish
radii = [0.8, 1.3, 1.8, 2.3, 2.8]
angles_per_radius = [3, 4, 5, 6, 7]

x_min, x_max = x_grid.min(), x_grid.max()
y_min, y_max = y_grid.min(), y_grid.max()

for radius, n_angles in zip(radii, angles_per_radius, strict=False):
    for angle in np.linspace(0, 2 * np.pi, n_angles, endpoint=False):
        # Starting point at given radius
        x0 = radius * np.cos(angle)
        y0 = radius * np.sin(angle)

        # Trace streamline using inline Euler integration
        points = [(x0, y0)]
        speeds = []
        x_curr, y_curr = x0, y0
        max_steps = 150
        dt = 0.08

        for _ in range(max_steps):
            # Find grid indices
            xi = int((x_curr - x_min) / (x_max - x_min) * (grid_size - 1))
            yi = int((y_curr - y_min) / (y_max - y_min) * (grid_size - 1))

            # Check bounds
            if xi < 0 or xi >= grid_size - 1 or yi < 0 or yi >= grid_size - 1:
                break

            # Get velocity
            u = U[yi, xi]
            v = V[yi, xi]

            # Calculate speed for color encoding
            speed = np.sqrt(u**2 + v**2)
            if speed < 1e-6:
                break
            speeds.append(speed)

            # Normalize velocity for consistent step size
            u_norm = u / speed
            v_norm = v / speed

            # Step forward
            x_new = x_curr + u_norm * dt
            y_new = y_curr + v_norm * dt

            # Check if out of bounds
            if x_new < x_min or x_new > x_max or y_new < y_min or y_new > y_max:
                break

            points.append((x_new, y_new))
            x_curr, y_curr = x_new, y_new

        # Only keep meaningful streamlines
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
    "backgroundColor": "#ffffff",
    "marginBottom": 250,
    "marginLeft": 220,
    "marginRight": 450,
    "marginTop": 180,
    "spacingBottom": 50,
}

# Title
chart.options.title = {
    "text": "streamline-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "56px", "fontWeight": "bold"},
}

# Subtitle describing the vortex
chart.options.subtitle = {
    "text": "Vortex Flow Field: u = -y, v = x (color indicates velocity magnitude)",
    "style": {"fontSize": "40px", "color": "#666666"},
}

# Axes with extended range to prevent clipping
chart.options.x_axis = {
    "title": {"text": "X Position (arbitrary units)", "style": {"fontSize": "42px"}},
    "labels": {"style": {"fontSize": "32px"}},
    "min": -4.0,
    "max": 4.0,
    "tickInterval": 1,
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "lineWidth": 2,
    "lineColor": "#333333",
}

chart.options.y_axis = {
    "title": {"text": "Y Position (arbitrary units)", "style": {"fontSize": "42px"}},
    "labels": {"style": {"fontSize": "32px"}},
    "min": -4.0,
    "max": 4.0,
    "tickInterval": 1,
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "lineWidth": 2,
    "lineColor": "#333333",
}

# Color palette based on velocity magnitude (viridis-like colorblind-safe)
speed_min = min(streamline_speeds) if streamline_speeds else 0
speed_max = max(streamline_speeds) if streamline_speeds else 1
speed_range = speed_max - speed_min if speed_max > speed_min else 1

# Viridis-inspired colors: dark purple -> blue -> teal -> green
viridis_colors = ["#440154", "#3B528B", "#21918C", "#5DC863"]

# Plot options
chart.options.plot_options = {"line": {"lineWidth": 5, "marker": {"enabled": False}, "enableMouseTracking": False}}

# Legend - disabled for streamlines, we'll use a custom HTML color scale
chart.options.legend = {"enabled": False}

# Build color scale legend HTML for the right side
color_scale_html = f"""
<div style="position:absolute; right:50px; top:300px; font-family:Arial,sans-serif;">
    <div style="font-size:32px; font-weight:bold; margin-bottom:20px; color:#333;">Velocity Magnitude</div>
    <div style="display:flex; align-items:center; margin-bottom:15px;">
        <div style="width:40px; height:30px; background:{viridis_colors[3]}; margin-right:15px;"></div>
        <span style="font-size:28px;">High ({speed_max:.1f})</span>
    </div>
    <div style="display:flex; align-items:center; margin-bottom:15px;">
        <div style="width:40px; height:30px; background:{viridis_colors[2]}; margin-right:15px;"></div>
        <span style="font-size:28px;">Med-High</span>
    </div>
    <div style="display:flex; align-items:center; margin-bottom:15px;">
        <div style="width:40px; height:30px; background:{viridis_colors[1]}; margin-right:15px;"></div>
        <span style="font-size:28px;">Med-Low</span>
    </div>
    <div style="display:flex; align-items:center; margin-bottom:15px;">
        <div style="width:40px; height:30px; background:{viridis_colors[0]}; margin-right:15px;"></div>
        <span style="font-size:28px;">Low ({speed_min:.1f})</span>
    </div>
</div>
"""

# Add streamlines as series with velocity-based colors
for i, (streamline, avg_speed) in enumerate(zip(streamlines, streamline_speeds, strict=False)):
    series = LineSeries()
    series.data = [[round(pt[0], 4), round(pt[1], 4)] for pt in streamline]
    series.name = f"Streamline {i + 1} (v={avg_speed:.2f})"

    # Inline color selection based on normalized speed
    t = (avg_speed - speed_min) / speed_range
    if t < 0.25:
        series.color = viridis_colors[0]  # Dark purple (low speed)
    elif t < 0.5:
        series.color = viridis_colors[1]  # Blue
    elif t < 0.75:
        series.color = viridis_colors[2]  # Teal
    else:
        series.color = viridis_colors[3]  # Green (high speed)

    series.line_width = 5
    chart.add_series(series)

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts and color scale legend
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; position:relative;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    {color_scale_html}
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save as plot.html for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
