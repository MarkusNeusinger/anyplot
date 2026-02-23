""" pyplots.ai
density-basic: Basic Density Plot
Library: highcharts 1.10.3 | Python 3.14.3
Quality: 92/100 | Updated: 2026-02-23
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaSeries
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - simulating heights (cm) with bimodal distribution
np.random.seed(42)
n_samples = 500
values_a = np.random.normal(162, 6, n_samples // 2)  # Female heights
values_b = np.random.normal(178, 6, n_samples // 2)  # Male heights
values = np.concatenate([values_a, values_b])

# Kernel Density Estimation (Gaussian kernel)
x_min, x_max = values.min() - 12, values.max() + 12
x_grid = np.linspace(x_min, x_max, 300)

# Silverman's rule of thumb for bandwidth
n = len(values)
bandwidth = 0.9 * min(np.std(values), np.subtract(*np.percentile(values, [75, 25])) / 1.34) * n ** (-1 / 5)

# Compute Gaussian KDE
density = np.zeros_like(x_grid)
for xi in values:
    density += np.exp(-0.5 * ((x_grid - xi) / bandwidth) ** 2)
density /= n * bandwidth * np.sqrt(2 * np.pi)

# Find the two peak positions for annotation
midpoint = len(x_grid) // 2
peak1_idx = np.argmax(density[:midpoint])
peak2_idx = midpoint + np.argmax(density[midpoint:])
peak1_x = float(x_grid[peak1_idx])
peak2_x = float(x_grid[peak2_idx])

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "area",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 180,
    "marginLeft": 180,
    "marginRight": 60,
    "marginTop": 140,
    "style": {"fontFamily": "Arial, Helvetica, sans-serif"},
}

# Title
chart.options.title = {
    "text": "density-basic \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "64px", "fontWeight": "600", "color": "#2c3e50"},
    "margin": 40,
}

# Disable credits
chart.options.credits = {"enabled": False}

# X-axis - clean L-shaped frame with plotBands/plotLines for peak emphasis
chart.options.x_axis = {
    "title": {"text": "Height (cm)", "style": {"fontSize": "48px", "color": "#444444"}, "margin": 24},
    "labels": {"style": {"fontSize": "36px", "color": "#666666"}},
    "lineColor": "#cccccc",
    "lineWidth": 2,
    "tickWidth": 0,
    "tickInterval": 5,
    "gridLineWidth": 0,
    "plotBands": [
        {"from": peak1_x - 8, "to": peak1_x + 8, "color": "rgba(48, 105, 152, 0.06)", "zIndex": 0},
        {"from": peak2_x - 8, "to": peak2_x + 8, "color": "rgba(48, 105, 152, 0.06)", "zIndex": 0},
    ],
    "plotLines": [
        {
            "value": peak1_x,
            "color": "rgba(48, 105, 152, 0.45)",
            "width": 3,
            "dashStyle": "Dash",
            "zIndex": 4,
            "label": {
                "text": f"Peak: {peak1_x:.0f} cm",
                "style": {"fontSize": "32px", "color": "#306998", "fontWeight": "600"},
                "rotation": 0,
                "y": 16,
            },
        },
        {
            "value": peak2_x,
            "color": "rgba(48, 105, 152, 0.45)",
            "width": 3,
            "dashStyle": "Dash",
            "zIndex": 4,
            "label": {
                "text": f"Peak: {peak2_x:.0f} cm",
                "style": {"fontSize": "32px", "color": "#306998", "fontWeight": "600"},
                "rotation": 0,
                "y": 16,
            },
        },
    ],
}

# Y-axis - subtle horizontal grid only
chart.options.y_axis = {
    "title": {"text": "Density", "style": {"fontSize": "48px", "color": "#444444"}, "margin": 24},
    "labels": {"style": {"fontSize": "36px", "color": "#666666"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.10)",
    "lineColor": "#cccccc",
    "lineWidth": 2,
    "tickAmount": 7,
    "min": 0,
}

# Plot options
chart.options.plot_options = {
    "area": {
        "fillColor": {
            "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
            "stops": [[0, "rgba(48, 105, 152, 0.45)"], [1, "rgba(48, 105, 152, 0.03)"]],
        },
        "lineWidth": 5,
        "marker": {"enabled": False},
        "color": "#306998",
        "states": {"hover": {"lineWidth": 5}},
    },
    "scatter": {
        "marker": {"radius": 15, "fillColor": "rgba(48, 105, 152, 0.55)", "symbol": "diamond", "lineWidth": 0},
        "states": {"hover": {"enabled": False}},
    },
    "series": {"animation": False},
}

# Disable tooltip for static export
chart.options.tooltip = {"enabled": False}

# Legend
chart.options.legend = {
    "enabled": True,
    "layout": "horizontal",
    "align": "right",
    "verticalAlign": "top",
    "floating": True,
    "x": -40,
    "y": 60,
    "itemStyle": {"fontSize": "34px", "fontWeight": "normal", "color": "#555555"},
    "symbolHeight": 20,
    "symbolWidth": 32,
    "itemDistance": 40,
    "borderWidth": 0,
}

# Add density curve as area series
area_series = AreaSeries()
area_series.data = [[round(float(x), 2), round(float(y), 6)] for x, y in zip(x_grid, density, strict=True)]
area_series.name = "Density"
chart.add_series(area_series)

# Add rug plot - vertical tick marks along x-axis
rug_sample = values[::3]  # Show every 3rd observation for good coverage
rug_y = max(density) * 0.008  # Small positive value near axis
rug_data = [[round(float(v), 2), round(float(rug_y), 6)] for v in sorted(rug_sample)]

rug_series = ScatterSeries()
rug_series.data = rug_data
rug_series.name = "Observations"
rug_series.marker = {"symbol": "diamond", "fillColor": "rgba(48, 105, 152, 0.55)", "lineWidth": 0, "radius": 15}
chart.add_series(rug_series)

# Download Highcharts JS for inline embedding
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

# Save standalone HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    standalone_html = f"""<!DOCTYPE html>
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
    f.write(standalone_html)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4900,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
