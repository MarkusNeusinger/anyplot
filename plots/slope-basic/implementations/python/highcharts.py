""" pyplots.ai
slope-basic: Basic Slope Chart (Slopegraph)
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Product sales comparing Q1 vs Q4 (in thousands)
products = ["Product A", "Product B", "Product C", "Product D", "Product E", "Product F", "Product G", "Product H"]
q1_sales = [85, 120, 45, 95, 150, 72, 110, 63]
q4_sales = [110, 95, 88, 140, 125, 105, 145, 58]

# Colors: blue for increase, yellow for decrease
color_increase = "#306998"  # Python Blue
color_decrease = "#FFD43B"  # Python Yellow

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginLeft": 350,
    "marginRight": 350,
    "marginBottom": 200,
    "spacingBottom": 50,
}

# Title
chart.options.title = {
    "text": "slope-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "64px", "fontWeight": "bold"},
}

# Subtitle
chart.options.subtitle = {"text": "Product Sales: Q1 vs Q4 (thousands)", "style": {"fontSize": "42px"}}

# X-axis (time points)
chart.options.x_axis = {
    "categories": ["Q1", "Q4"],
    "title": {"text": None},
    "labels": {"style": {"fontSize": "36px", "fontWeight": "bold"}},
    "lineWidth": 2,
    "tickWidth": 0,
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Sales (thousands)", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 1,
    "gridLineDashStyle": "Dash",
    "min": 0,
}

# Legend
chart.options.legend = {"enabled": False}

# Plot options for line styling
chart.options.plot_options = {
    "line": {
        "lineWidth": 6,
        "marker": {"enabled": True, "radius": 16, "symbol": "circle"},
        "dataLabels": {
            "enabled": True,
            "style": {"fontSize": "28px", "fontWeight": "normal", "textOutline": "none"},
            "format": "{point.y}",
        },
    }
}

# Add series for each product
series_list = []
for i, product in enumerate(products):
    start_val = q1_sales[i]
    end_val = q4_sales[i]

    # Determine color based on direction
    color = color_increase if end_val >= start_val else color_decrease

    series = LineSeries()
    series.name = product
    series.data = [
        {"y": start_val, "dataLabels": {"align": "right", "x": -20, "format": f"{product}: {start_val}"}},
        {"y": end_val, "dataLabels": {"align": "left", "x": 20, "format": f"{product}: {end_val}"}},
    ]
    series.color = color
    series_list.append(series)

chart.options.series = series_list

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

# Also save as plot.html for interactive version
Path("plot.html").write_text(html_content, encoding="utf-8")

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
