""" pyplots.ai
histogram-cumulative: Cumulative Histogram
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Student test scores (realistic educational context)
np.random.seed(42)
scores = np.concatenate(
    [
        np.random.normal(65, 10, 150),  # Average performers
        np.random.normal(85, 5, 80),  # High performers
        np.random.normal(45, 8, 50),  # Struggling students
    ]
)
scores = np.clip(scores, 0, 100)  # Clip to valid score range

# Calculate cumulative histogram data
n_bins = 20
counts, bin_edges = np.histogram(scores, bins=n_bins, range=(0, 100))
cumulative_counts = np.cumsum(counts)
cumulative_proportion = cumulative_counts / len(scores) * 100  # Percentage

# Prepare data for Highcharts area/step chart
# Using bin centers for x values
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
data_points = [[float(x), float(y)] for x, y in zip(bin_centers, cumulative_proportion, strict=True)]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "area",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 250,
    "marginLeft": 200,
    "marginRight": 100,
    "marginTop": 180,
}

# Title
chart.options.title = {
    "text": "histogram-cumulative · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle
chart.options.subtitle = {"text": "Student Test Score Distribution (n=280)", "style": {"fontSize": "32px"}}

# X-axis
chart.options.x_axis = {
    "title": {"text": "Test Score", "style": {"fontSize": "36px"}, "margin": 20},
    "labels": {"style": {"fontSize": "28px"}},
    "min": 0,
    "max": 100,
    "tickInterval": 10,
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Cumulative Percentage (%)", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}, "format": "{value}%"},
    "min": 0,
    "max": 100,
    "tickInterval": 10,
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
}

# Legend
chart.options.legend = {"enabled": True, "itemStyle": {"fontSize": "28px"}}

# Plot options for step-like appearance
chart.options.plot_options = {
    "area": {
        "step": "center",
        "marker": {"enabled": True, "radius": 10, "fillColor": "#306998", "lineColor": "#306998", "lineWidth": 2},
        "lineWidth": 4,
        "color": "#306998",
        "fillColor": {
            "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
            "stops": [[0, "rgba(48, 105, 152, 0.5)"], [1, "rgba(48, 105, 152, 0.1)"]],
        },
    }
}

# Credits
chart.options.credits = {"enabled": False}

# Add series
series = AreaSeries()
series.data = data_points
series.name = "Cumulative Distribution"
chart.add_series(series)

# Export to PNG via Selenium
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

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
    f.write(html_content)
