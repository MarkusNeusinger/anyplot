""" pyplots.ai
scatter-categorical: Categorical Scatter Plot
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
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


# Data - Plant growth study with three fertilizer types
np.random.seed(42)

categories = ["Fertilizer A", "Fertilizer B", "Fertilizer C"]
colors = ["#306998", "#FFD43B", "#9467BD"]  # Python Blue, Python Yellow, Purple

# Generate data for each category with different patterns
data_by_category = {}
n_points = 40

# Fertilizer A: moderate growth, medium variance
nitrogen_a = np.random.uniform(20, 80, n_points)
growth_a = 0.4 * nitrogen_a + np.random.normal(10, 5, n_points)
data_by_category["Fertilizer A"] = list(zip(nitrogen_a.tolist(), growth_a.tolist(), strict=True))

# Fertilizer B: high growth, low variance (best performer)
nitrogen_b = np.random.uniform(25, 85, n_points)
growth_b = 0.6 * nitrogen_b + np.random.normal(15, 3, n_points)
data_by_category["Fertilizer B"] = list(zip(nitrogen_b.tolist(), growth_b.tolist(), strict=True))

# Fertilizer C: lower growth, higher variance
nitrogen_c = np.random.uniform(15, 75, n_points)
growth_c = 0.3 * nitrogen_c + np.random.normal(5, 8, n_points)
data_by_category["Fertilizer C"] = list(zip(nitrogen_c.tolist(), growth_c.tolist(), strict=True))

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
    "spacingBottom": 80,
}

# Title
chart.options.title = {
    "text": "scatter-categorical · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Axes
chart.options.x_axis = {
    "title": {"text": "Nitrogen Applied (kg/ha)", "style": {"fontSize": "36px"}, "margin": 30},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
}

chart.options.y_axis = {
    "title": {"text": "Plant Growth (cm)", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
}

# Legend
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 100,
    "itemStyle": {"fontSize": "28px"},
}

# Plot options for scatter series
chart.options.plot_options = {
    "scatter": {"marker": {"radius": 12, "symbol": "circle"}, "states": {"hover": {"marker": {"enabled": True}}}}
}

# Add series for each category
for i, category in enumerate(categories):
    series = ScatterSeries()
    series.name = category
    series.data = data_by_category[category]
    series.color = colors[i]
    series.marker = {"radius": 12, "fillColor": colors[i], "lineWidth": 2, "lineColor": "#ffffff"}
    chart.add_series(series)

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

# Also save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    interactive_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>scatter-categorical · highcharts · pyplots.ai</title>
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0; display:flex; justify-content:center; align-items:center; min-height:100vh; background:#f5f5f5;">
    <div id="container" style="width: 1200px; height: 675px;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(interactive_html)
