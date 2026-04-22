""" pyplots.ai
bar-grouped: Grouped Bar Chart
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
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


# Data - Quarterly revenue by product line (realistic business scenario)
categories = ["Q1", "Q2", "Q3", "Q4"]
products = {
    "Electronics": [245, 312, 287, 398],
    "Clothing": [189, 215, 243, 275],
    "Home & Garden": [156, 178, 195, 224],
}

# Colors - Python Blue first, then colorblind-safe palette
colors = ["#306998", "#FFD43B", "#9467BD"]

# Create chart with container specified
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for 4800x2700 px
chart.options.chart = {
    "type": "column",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 280,
    "style": {"fontFamily": "Arial, sans-serif"},
}

# Title
chart.options.title = {
    "text": "bar-grouped · highcharts · pyplots.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold"},
}

# Subtitle for context
chart.options.subtitle = {
    "text": "Quarterly Revenue by Product Line (in thousands USD)",
    "style": {"fontSize": "42px", "color": "#666666"},
}

# X-axis configuration
chart.options.x_axis = {
    "categories": categories,
    "title": {"text": "Quarter", "style": {"fontSize": "48px", "fontWeight": "bold"}},
    "labels": {"style": {"fontSize": "36px"}},
    "lineWidth": 2,
    "tickWidth": 2,
}

# Y-axis configuration
chart.options.y_axis = {
    "min": 0,
    "title": {"text": "Revenue (thousands USD)", "style": {"fontSize": "48px", "fontWeight": "bold"}},
    "labels": {"style": {"fontSize": "36px"}, "format": "${value}K"},
    "gridLineWidth": 1,
    "gridLineDashStyle": "Dash",
    "gridLineColor": "#cccccc",
}

# Legend configuration
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 100,
    "floating": True,
    "backgroundColor": "#ffffff",
    "borderWidth": 1,
    "borderColor": "#cccccc",
    "shadow": True,
    "itemStyle": {"fontSize": "36px", "fontWeight": "normal"},
    "symbolHeight": 24,
    "symbolWidth": 40,
    "symbolRadius": 4,
    "itemMarginBottom": 10,
}

# Plot options for grouped bars
chart.options.plot_options = {
    "column": {
        "groupPadding": 0.15,
        "pointPadding": 0.05,
        "borderWidth": 2,
        "borderColor": "#ffffff",
        "dataLabels": {
            "enabled": True,
            "format": "${y}K",
            "style": {"fontSize": "28px", "fontWeight": "bold", "textOutline": "2px white"},
        },
    }
}

# Add series for each product
for i, (product_name, values) in enumerate(products.items()):
    series = ColumnSeries()
    series.name = product_name
    series.data = values
    series.color = colors[i]
    chart.add_series(series)

# Download Highcharts JS for inline embedding (required for headless Chrome)
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
<body style="margin:0; padding:0; background:#ffffff;">
    <div id="container" style="width:4800px; height:2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save interactive HTML version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Set up headless Chrome for PNG export
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

# Capture screenshot
driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
