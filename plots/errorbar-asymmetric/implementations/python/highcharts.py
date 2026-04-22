""" pyplots.ai
errorbar-asymmetric: Asymmetric Error Bars Plot
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
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Quarterly sales forecast with asymmetric confidence intervals
np.random.seed(42)
categories = ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024", "Q1 2025", "Q2 2025"]
# Central values (point estimates in millions USD)
y_values = [12.5, 14.2, 13.8, 18.5, 15.2, 16.8]
# Asymmetric errors - upside potential typically larger in optimistic forecasts
error_lower = [1.2, 1.5, 2.0, 2.5, 1.8, 2.2]  # Downside risk
error_upper = [2.5, 3.0, 2.8, 4.5, 3.2, 3.8]  # Upside potential

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for 4800x2700 canvas
chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 280,
    "marginLeft": 280,
    "marginRight": 150,
    "marginTop": 200,
}

# Title
chart.options.title = {
    "text": "errorbar-asymmetric · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle explaining the error bars
chart.options.subtitle = {
    "text": "Quarterly Sales Forecast with 10th-90th Percentile Confidence Intervals",
    "style": {"fontSize": "32px", "color": "#666666"},
}

# X-axis configuration
chart.options.x_axis = {
    "categories": categories,
    "title": {"text": "Quarter", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
}

# Y-axis configuration - let axis auto-scale to better use canvas space
chart.options.y_axis = {
    "title": {"text": "Sales Forecast (Million USD)", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineColor": "#e0e0e0",
    "gridLineWidth": 1,
}

# Legend configuration - positioned closer to the data, inside the plot area
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "32px"},
    "symbolRadius": 0,
    "symbolWidth": 40,
    "symbolHeight": 24,
    "align": "right",
    "verticalAlign": "top",
    "x": -80,
    "y": 120,
    "layout": "vertical",
    "backgroundColor": "#ffffff",
    "borderColor": "#e0e0e0",
    "borderWidth": 1,
    "padding": 16,
}

# Plot options - configure errorbar series with visible caps
chart.options.plot_options = {
    "errorbar": {"stemWidth": 6, "whiskerLength": 40, "whiskerWidth": 6},
    "scatter": {"marker": {"radius": 16, "symbol": "circle"}},
}

# Create errorbar data with asymmetric errors: [low, high] format
errorbar_data = []
for y, el, eu in zip(y_values, error_lower, error_upper, strict=True):
    errorbar_data.append([y - el, y + eu])

# Create series data for central points
scatter_data = []
for i, y in enumerate(y_values):
    scatter_data.append({"x": i, "y": y})

# Add series - use native errorbar series type for authentic error bars with caps
chart.options.series = [
    {
        "name": "Point Estimate",
        "type": "scatter",
        "data": scatter_data,
        "color": "#FFD43B",
        "marker": {"radius": 18, "symbol": "diamond", "lineColor": "#306998", "lineWidth": 3},
        "zIndex": 5,
    },
    {
        "name": "10th-90th Percentile Range",
        "type": "errorbar",
        "data": errorbar_data,
        "color": "#306998",
        "stemColor": "#306998",
        "whiskerColor": "#306998",
        "showInLegend": True,
    },
]

# Download Highcharts JS and highcharts-more.js (needed for some chart types)
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

# Save HTML for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot with headless Chrome
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
