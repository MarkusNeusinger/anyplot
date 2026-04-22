""" pyplots.ai
bar-stacked-labeled: Stacked Bar Chart with Total Labels
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import ColumnSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Quarterly revenue by product category
categories = ["Q1", "Q2", "Q3", "Q4"]
components = ["Electronics", "Clothing", "Home & Garden", "Sports"]
colors = ["#306998", "#FFD43B", "#9467BD", "#17BECF"]

# Revenue data (in thousands of dollars)
data = {
    "Electronics": [120, 145, 135, 180],
    "Clothing": [85, 110, 95, 125],
    "Home & Garden": [60, 75, 90, 70],
    "Sports": [45, 55, 80, 65],
}

# Calculate totals for each quarter
totals = [sum(data[comp][i] for comp in components) for i in range(len(categories))]

# Create chart with container
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "column",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginTop": 180,
    "marginBottom": 200,
    "spacingBottom": 50,
}

# Title
chart.options.title = {
    "text": "bar-stacked-labeled · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle
chart.options.subtitle = {
    "text": "Quarterly Revenue by Product Category (in thousands USD)",
    "style": {"fontSize": "32px"},
}

# X-axis
chart.options.x_axis = {
    "categories": categories,
    "title": {"text": "Quarter", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
}

# Y-axis
chart.options.y_axis = {
    "min": 0,
    "title": {"text": "Revenue (thousands USD)", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
    "stackLabels": {
        "enabled": True,
        "style": {"fontSize": "36px", "fontWeight": "bold", "color": "#333333"},
        "format": "${total}K",
    },
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "28px"},
    "symbolHeight": 24,
    "symbolWidth": 24,
    "symbolRadius": 4,
    "verticalAlign": "top",
    "layout": "horizontal",
    "align": "right",
    "x": -50,
    "y": 80,
}

# Plot options for stacking
chart.options.plot_options = {
    "column": {
        "stacking": "normal",
        "borderWidth": 1,
        "borderColor": "#ffffff",
        "dataLabels": {
            "enabled": True,
            "style": {"fontSize": "22px", "fontWeight": "normal", "textOutline": "none"},
            "format": "{y}",
            "color": "#333333",
        },
    }
}

# Tooltip
chart.options.tooltip = {
    "headerFormat": "<b>{point.x}</b><br/>",
    "pointFormat": "{series.name}: ${point.y}K<br/>Total: ${point.stackTotal}K",
    "style": {"fontSize": "24px"},
}

# Add series for each component
for idx, component in enumerate(components):
    series = ColumnSeries()
    series.name = component
    series.data = data[component]
    series.color = colors[idx]
    chart.add_series(series)

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

# Save HTML output as well
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
