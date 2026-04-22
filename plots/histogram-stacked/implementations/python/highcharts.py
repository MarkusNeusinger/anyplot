""" pyplots.ai
histogram-stacked: Stacked Histogram
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
from highcharts_core.options.series.bar import ColumnSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Generate three groups with different distributions
np.random.seed(42)
group_a = np.random.normal(loc=45, scale=12, size=150)  # Centered around 45
group_b = np.random.normal(loc=55, scale=10, size=120)  # Centered around 55
group_c = np.random.normal(loc=65, scale=15, size=100)  # Centered around 65

# Combine all data to determine common bin edges
all_data = np.concatenate([group_a, group_b, group_c])
bin_edges = np.histogram_bin_edges(all_data, bins=15)
bin_centers = [(bin_edges[i] + bin_edges[i + 1]) / 2 for i in range(len(bin_edges) - 1)]
bin_labels = [f"{bin_edges[i]:.0f}-{bin_edges[i + 1]:.0f}" for i in range(len(bin_edges) - 1)]

# Calculate histogram counts for each group
counts_a, _ = np.histogram(group_a, bins=bin_edges)
counts_b, _ = np.histogram(group_b, bins=bin_edges)
counts_c, _ = np.histogram(group_c, bins=bin_edges)

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart options
chart.options.chart = {
    "type": "column",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 300,
}

# Title
chart.options.title = {
    "text": "histogram-stacked · highcharts · pyplots.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold"},
}

# Subtitle
chart.options.subtitle = {"text": "Measurement Distribution by Sensor Type", "style": {"fontSize": "42px"}}

# X-axis (categories for bins)
chart.options.x_axis = {
    "categories": bin_labels,
    "title": {"text": "Measurement Range", "style": {"fontSize": "48px"}, "margin": 40},
    "labels": {"style": {"fontSize": "28px"}},
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Frequency", "style": {"fontSize": "48px"}},
    "labels": {"style": {"fontSize": "36px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0,0,0,0.1)",
    "stackLabels": {"enabled": False},
}

# Plot options for stacking
chart.options.plot_options = {
    "column": {"stacking": "normal", "borderWidth": 1, "borderColor": "#ffffff", "dataLabels": {"enabled": False}}
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "36px"},
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 100,
}

# Colors - colorblind-safe palette
colors = ["#306998", "#FFD43B", "#9467BD"]

# Add series for each group
series_a = ColumnSeries()
series_a.data = [int(c) for c in counts_a]
series_a.name = "Sensor A"
series_a.color = colors[0]

series_b = ColumnSeries()
series_b.data = [int(c) for c in counts_b]
series_b.name = "Sensor B"
series_b.color = colors[1]

series_c = ColumnSeries()
series_c.data = [int(c) for c in counts_c]
series_c.name = "Sensor C"
series_c.color = colors[2]

chart.add_series(series_a)
chart.add_series(series_b)
chart.add_series(series_c)

# Export to PNG via Selenium
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
    f.write(html_content)
