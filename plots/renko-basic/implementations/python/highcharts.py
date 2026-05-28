""" anyplot.ai
renko-basic: Basic Renko Chart
Library: highcharts unknown | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-17
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
BRAND = "#009E73"  # Bullish (position 1)
BEARISH = "#AE3030"  # imprint red — bearish

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

# Plot
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "columnrange",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 280,
    "marginLeft": 250,
    "marginTop": 200,
    "marginRight": 100,
}

# Title
chart.options.title = {
    "text": "renko-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "medium", "color": INK},
    "y": 50,
}

# Subtitle
chart.options.subtitle = {
    "text": f"Stock Price Movement | Brick Size: ${brick_size:.0f}",
    "style": {"fontSize": "22px", "color": INK_SOFT},
    "y": 100,
}

# X-axis
chart.options.x_axis = {
    "title": {"text": "Brick Index", "style": {"fontSize": "22px", "color": INK}, "margin": 25},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "tickInterval": 5,
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Price ($)", "style": {"fontSize": "22px", "color": INK}, "margin": 25},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}, "format": "${value}"},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
}

# Legend - positioned at top right for visibility
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 150,
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "symbolHeight": 24,
    "symbolWidth": 50,
    "itemMarginBottom": 15,
    "backgroundColor": ELEVATED_BG,
    "borderWidth": 1,
    "borderColor": INK_SOFT,
    "padding": 15,
}

# Plot options for column range
chart.options.plot_options = {
    "columnrange": {"borderWidth": 2, "borderColor": INK_SOFT, "pointPadding": 0.05, "groupPadding": 0}
}

# Series data - using Okabe-Ito palette
chart.options.series = [
    {
        "type": "columnrange",
        "name": "Bullish (Up)",
        "data": bullish_series_data,
        "color": BRAND,
        "borderColor": BRAND,
        "borderWidth": 2,
    },
    {
        "type": "columnrange",
        "name": "Bearish (Down)",
        "data": bearish_series_data,
        "color": BEARISH,
        "borderColor": BEARISH,
        "borderWidth": 2,
    },
]

# Tooltip configuration
chart.options.tooltip = {
    "enabled": True,
    "headerFormat": '<span style="font-size: 18px; color: ' + INK + '">Brick {point.x}</span><br/>',
    "pointFormat": '<span style="font-size: 18px; color:{point.color}">●</span> {series.name}: <b style="color: '
    + INK
    + '">${point.low:.2f} - ${point.high:.2f}</b><br/>',
    "style": {"fontSize": "18px", "color": INK},
    "backgroundColor": ELEVATED_BG,
    "borderWidth": 1,
    "borderColor": INK_SOFT,
}

# Credits and exporting
chart.options.credits = {"enabled": False}
chart.options.exporting = {"enabled": False}

# Download Highcharts JS (required for headless Chrome)
highcharts_url = "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.4.8/highcharts.js"
highcharts_more_url = "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.4.8/highcharts-more.min.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

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
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML artifact for the site
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

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
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
