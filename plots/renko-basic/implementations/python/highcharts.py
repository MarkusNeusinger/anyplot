""" pyplots.ai
renko-basic: Basic Renko Chart
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2026-01-08
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


# Data - Generate synthetic stock price data
np.random.seed(42)

# Simulate 300 days of stock prices starting at $100
n_days = 300
returns = np.random.normal(0.0005, 0.015, n_days)  # Daily returns
prices = 100 * np.cumprod(1 + returns)

# Calculate Renko bricks
brick_size = 2.0  # $2 per brick

bricks = []
base_price = np.floor(prices[0] / brick_size) * brick_size

for price in prices[1:]:
    diff = price - base_price
    if diff >= brick_size:
        num_bricks = int(diff // brick_size)
        for _ in range(num_bricks):
            bricks.append({"open": base_price, "close": base_price + brick_size, "direction": "up"})
            base_price += brick_size
    elif diff <= -brick_size:
        num_bricks = int(abs(diff) // brick_size)
        for _ in range(num_bricks):
            bricks.append({"open": base_price, "close": base_price - brick_size, "direction": "down"})
            base_price -= brick_size

# Prepare data for Highcharts columnrange
bullish_series_data = []
bearish_series_data = []

for i, brick in enumerate(bricks):
    if brick["direction"] == "up":
        bullish_series_data.append([i, brick["open"], brick["close"]])
    else:
        bearish_series_data.append([i, brick["close"], brick["open"]])

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "columnrange",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 280,
    "marginLeft": 250,
    "marginTop": 200,
    "marginRight": 100,
}

# Title
chart.options.title = {
    "text": "renko-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "56px", "fontWeight": "bold"},
    "y": 50,
}

# Subtitle
chart.options.subtitle = {
    "text": f"Stock Price Movement | Brick Size: ${brick_size:.0f}",
    "style": {"fontSize": "36px", "color": "#666666"},
    "y": 100,
}

# X-axis
chart.options.x_axis = {
    "title": {"text": "Brick Index", "style": {"fontSize": "40px"}, "margin": 25},
    "labels": {"style": {"fontSize": "32px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
    "tickInterval": 5,
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Price ($)", "style": {"fontSize": "40px"}, "margin": 25},
    "labels": {"style": {"fontSize": "32px"}, "format": "${value}"},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.15)",
}

# Legend - positioned at top right for visibility
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 150,
    "itemStyle": {"fontSize": "32px"},
    "symbolHeight": 24,
    "symbolWidth": 50,
    "itemMarginBottom": 15,
    "backgroundColor": "rgba(255, 255, 255, 0.9)",
    "borderWidth": 1,
    "borderColor": "#cccccc",
    "padding": 15,
}

# Plot options for column range
chart.options.plot_options = {
    "columnrange": {"borderWidth": 2, "borderColor": "#333333", "pointPadding": 0.05, "groupPadding": 0}
}

# Series data - using colorblind-safe blue/orange palette
chart.options.series = [
    {
        "type": "columnrange",
        "name": "Bullish (Up)",
        "data": bullish_series_data,
        "color": "#2563eb",  # Blue - colorblind safe
        "borderColor": "#1e40af",
        "borderWidth": 2,
    },
    {
        "type": "columnrange",
        "name": "Bearish (Down)",
        "data": bearish_series_data,
        "color": "#ea580c",  # Orange - colorblind safe
        "borderColor": "#c2410c",
        "borderWidth": 2,
    },
]

# Tooltip configuration - Highcharts distinctive feature
chart.options.tooltip = {
    "enabled": True,
    "headerFormat": '<span style="font-size: 28px">Brick {point.x}</span><br/>',
    "pointFormat": '<span style="font-size: 24px; color:{point.color}">●</span> {series.name}: <b>${point.low:.2f} - ${point.high:.2f}</b><br/>',
    "style": {"fontSize": "24px"},
    "backgroundColor": "rgba(255, 255, 255, 0.95)",
    "borderWidth": 2,
}

# Credits - Highcharts distinctive feature
chart.options.credits = {"enabled": False}

# Exporting options - Highcharts distinctive feature
chart.options.exporting = {"enabled": False}

# Note: Animation is enabled by default in Highcharts

# Responsive rules - Highcharts distinctive feature
chart.options.responsive = {
    "rules": [
        {
            "condition": {"maxWidth": 2400},
            "chartOptions": {"legend": {"itemStyle": {"fontSize": "18px"}}, "title": {"style": {"fontSize": "32px"}}},
        }
    ]
}

# Download Highcharts JS (required for headless Chrome)
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Download highcharts-more.js for columnrange
highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Generate HTML with INLINE scripts
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

# Also save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)
