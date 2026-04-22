""" pyplots.ai
andrews-curves: Andrews Curves for Multivariate Data
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
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
from sklearn.datasets import load_iris
from sklearn.preprocessing import StandardScaler


# Data - Iris dataset normalized
iris = load_iris()
X = StandardScaler().fit_transform(iris.data)
y = iris.target
species_names = ["Setosa", "Versicolor", "Virginica"]

# Andrews curve transformation: f(t) = x1/sqrt(2) + x2*sin(t) + x3*cos(t) + x4*sin(2t) + ...
t = np.linspace(-np.pi, np.pi, 200)


def andrews_curve(x, t):
    """Transform multivariate observation to Andrews curve"""
    n = len(x)
    result = x[0] / np.sqrt(2)
    for i in range(1, n):
        if i % 2 == 1:
            result += x[i] * np.sin((i // 2 + 1) * t)
        else:
            result += x[i] * np.cos((i // 2) * t)
    return result


# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart settings
chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 180,
    "marginTop": 120,
    "marginLeft": 150,
    "marginRight": 100,
}

# Title
chart.options.title = {
    "text": "Iris Species · andrews-curves · highcharts · pyplots.ai",
    "style": {"fontSize": "56px", "fontWeight": "bold"},
    "y": 60,
}

# Axes
chart.options.x_axis = {
    "title": {"text": "t (radians)", "style": {"fontSize": "40px"}, "margin": 30},
    "labels": {"style": {"fontSize": "32px"}, "y": 40},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0,0,0,0.15)",
    "tickInterval": 1,
    "min": -3.15,
    "max": 3.15,
}

chart.options.y_axis = {
    "title": {"text": "f(t)", "style": {"fontSize": "40px"}, "margin": 30},
    "labels": {"style": {"fontSize": "32px"}, "x": -15},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0,0,0,0.15)",
    "tickInterval": 1,
}

# Colors for species (colorblind-safe)
colors = ["#306998", "#FFD43B", "#9467BD"]

# Legend styling - positioned inside chart area to avoid clipping
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "36px", "fontWeight": "bold"},
    "symbolWidth": 60,
    "symbolHeight": 4,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 80,
    "itemDistance": 20,
    "itemMarginTop": 10,
    "backgroundColor": "rgba(255,255,255,0.9)",
    "borderWidth": 1,
    "borderColor": "#cccccc",
    "padding": 15,
}

# Plot options for transparency
chart.options.plot_options = {
    "line": {"lineWidth": 3, "marker": {"enabled": False}, "animation": False},
    "series": {"animation": False},
}

# Generate curves for each observation (sample 20 per species for clarity)
np.random.seed(42)
samples_per_species = 20

for species_idx in range(3):
    species_mask = y == species_idx
    species_X = X[species_mask]
    sample_indices = np.random.choice(len(species_X), min(samples_per_species, len(species_X)), replace=False)

    for i, idx in enumerate(sample_indices):
        curve_values = andrews_curve(species_X[idx], t)
        data_points = [[float(t[j]), float(curve_values[j])] for j in range(len(t))]

        series = LineSeries()
        series.data = data_points
        series.name = species_names[species_idx]
        series.color = colors[species_idx]
        series.opacity = 0.5
        series.show_in_legend = i == 0  # Only show first curve in legend
        series.line_width = 2

        chart.add_series(series)

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline script
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

# Write temp HTML and capture screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4900,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

# Screenshot the chart element for exact dimensions
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()

# Also save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)
