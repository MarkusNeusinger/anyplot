""" pyplots.ai
cat-box-strip: Box Plot with Strip Overlay
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
from highcharts_core.options.series.boxplot import BoxPlotSeries
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Plant growth measurements under different light conditions
np.random.seed(42)
categories = ["Low Light", "Medium Light", "High Light", "Full Sun"]

# Generate realistic plant growth data (cm) with different distributions
data_by_category = {
    "Low Light": np.random.normal(12, 3, 40),  # Lower growth, moderate spread
    "Medium Light": np.random.normal(22, 4, 45),  # Medium growth
    "High Light": np.random.normal(35, 5, 50),  # Higher growth, more variation
    "Full Sun": np.concatenate(
        [  # Highest growth with outliers
            np.random.normal(42, 4, 45),
            np.array([20, 22, 58, 60]),  # Some outliers
        ]
    ),
}

# Calculate box plot statistics for each category
box_data = []
for cat in categories:
    values = data_by_category[cat]
    q1 = np.percentile(values, 25)
    median = np.percentile(values, 50)
    q3 = np.percentile(values, 75)
    iqr = q3 - q1
    whisker_low = max(values.min(), q1 - 1.5 * iqr)
    whisker_high = min(values.max(), q3 + 1.5 * iqr)
    box_data.append([whisker_low, q1, median, q3, whisker_high])

# Prepare scatter data with jitter for strip overlay
scatter_data = []
for i, cat in enumerate(categories):
    values = data_by_category[cat]
    for val in values:
        # Add jitter to x position (-0.2 to 0.2)
        jitter = np.random.uniform(-0.2, 0.2)
        scatter_data.append([i + jitter, float(val)])

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "boxplot",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 200,
    "spacingBottom": 50,
    "style": {"fontFamily": "Arial, sans-serif"},
}

# Title
chart.options.title = {
    "text": "cat-box-strip · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# X-axis
chart.options.x_axis = {
    "categories": categories,
    "title": {"text": "Light Condition", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Plant Growth (cm)", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineColor": "#e0e0e0",
    "gridLineWidth": 1,
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "28px"},
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 100,
}

# Plot options
chart.options.plot_options = {
    "boxplot": {
        "fillColor": "rgba(48, 105, 152, 0.3)",
        "color": "#306998",
        "lineWidth": 3,
        "medianWidth": 5,
        "medianColor": "#FFD43B",
        "stemWidth": 3,
        "stemColor": "#306998",
        "whiskerWidth": 4,
        "whiskerColor": "#306998",
        "whiskerLength": "50%",
    },
    "scatter": {
        "marker": {
            "radius": 10,
            "symbol": "circle",
            "fillColor": "rgba(255, 212, 59, 0.7)",
            "lineWidth": 2,
            "lineColor": "#FFD43B",
        }
    },
}

# Add box plot series
box_series = BoxPlotSeries()
box_series.name = "Distribution Statistics"
box_series.data = box_data
box_series.color = "#306998"
chart.add_series(box_series)

# Add scatter series for strip plot
scatter_series = ScatterSeries()
scatter_series.name = "Individual Measurements"
scatter_series.data = scatter_data
scatter_series.color = "#FFD43B"
chart.add_series(scatter_series)

# Download Highcharts JS files
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
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

# Also save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Setup Chrome for screenshot
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

Path(temp_path).unlink()  # Clean up temp file
