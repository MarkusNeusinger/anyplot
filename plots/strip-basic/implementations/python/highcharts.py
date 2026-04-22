""" pyplots.ai
strip-basic: Basic Strip Plot
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
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


# Data - student test scores by subject
np.random.seed(42)
categories = ["Mathematics", "Science", "Literature", "History"]
colors = ["#306998", "#FFD43B", "#9467BD", "#17BECF"]

# Generate realistic test score data (different distributions per subject)
raw_data = {
    "Mathematics": np.concatenate(
        [
            np.random.normal(72, 12, 35),  # Wider spread
            np.random.normal(90, 5, 10),  # High performers
        ]
    ),
    "Science": np.random.normal(75, 10, 40),  # Normal distribution
    "Literature": np.concatenate(
        [
            np.random.normal(65, 8, 25),  # Lower cluster
            np.random.normal(82, 6, 20),  # Upper cluster (bimodal)
        ]
    ),
    "History": np.random.normal(78, 9, 38),  # Slightly higher scores
}

# Clip values to realistic range (0-100)
for cat in categories:
    raw_data[cat] = np.clip(raw_data[cat], 30, 100)

# Create strip plot data with random jitter
jitter_width = 0.25  # Moderate jitter as per spec recommendation (0.1-0.3)
strip_data = []
for cat_idx, cat in enumerate(categories):
    values = raw_data[cat]
    # Random horizontal jitter within jitter_width
    x_jitter = np.random.uniform(-jitter_width, jitter_width, len(values))

    for val, x_off in zip(values, x_jitter, strict=True):
        strip_data.append({"x": cat_idx + x_off, "y": float(val), "category": cat, "color": colors[cat_idx]})

# Calculate mean for each category (for reference markers)
means = {cat: float(np.mean(raw_data[cat])) for cat in categories}

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 200,
}

# Title
chart.options.title = {
    "text": "strip-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold"},
}

# Subtitle describing data
chart.options.subtitle = {"text": "Student Test Scores by Subject", "style": {"fontSize": "48px"}}

# X-axis (categorical)
chart.options.x_axis = {
    "categories": categories,
    "title": {"text": "Subject", "style": {"fontSize": "48px"}},
    "labels": {"style": {"fontSize": "36px"}},
    "tickWidth": 0,
    "lineWidth": 2,
    "min": -0.5,
    "max": len(categories) - 0.5,
    "tickPositions": [0, 1, 2, 3],
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Test Score", "style": {"fontSize": "48px"}},
    "labels": {"style": {"fontSize": "36px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
    "gridLineDashStyle": "Dash",
    "min": 40,
    "max": 105,
}

# Legend - position at top right to avoid cutting off
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 100,
    "itemStyle": {"fontSize": "36px"},
}

# Credits
chart.options.credits = {"enabled": False}

# Tooltip
chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": "<b>{point.category}</b><br/>Score: {point.y:.1f}",
    "style": {"fontSize": "24px"},
}

# Add scatter series for each category (for legend)
for cat_idx, cat in enumerate(categories):
    series = ScatterSeries()
    series.name = cat
    series.color = colors[cat_idx]
    series.data = [{"x": float(pt["x"]), "y": pt["y"], "category": cat} for pt in strip_data if pt["category"] == cat]
    series.marker = {
        "radius": 14,
        "symbol": "circle",
        "fillColor": colors[cat_idx],
        "fillOpacity": 0.6,  # Transparency for overlapping points
        "lineWidth": 2,
        "lineColor": "#ffffff",
    }
    chart.add_series(series)

# Add mean markers as horizontal line segments
mean_series = ScatterSeries()
mean_series.name = "Mean"
mean_series.data = [{"x": float(i), "y": means[cat]} for i, cat in enumerate(categories)]
mean_series.marker = {"radius": 18, "symbol": "diamond", "fillColor": "#E74C3C", "lineWidth": 3, "lineColor": "#ffffff"}
mean_series.color = "#E74C3C"
chart.add_series(mean_series)

# Download Highcharts JS (required for headless Chrome)
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
chrome_options.add_argument("--window-size=4800,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

# Take screenshot of just the chart container element
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()

# Also save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    interactive_html = f"""<!DOCTYPE html>
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
    f.write(interactive_html)
