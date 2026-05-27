""" anyplot.ai
kagi-basic: Basic Kagi Chart
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
from highcharts_core.options.series.area import LineSeries
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
YANG_COLOR = "#009E73"  # Green (bullish) - first series
YIN_COLOR = "#AE3030"  # imprint red — bearish

# Generate realistic stock price data
np.random.seed(42)

# Simulate 200 days of stock price data with trends and reversals
n_days = 200
base_price = 100
returns = np.random.normal(0.001, 0.02, n_days)

# Add trend patterns to make the Kagi chart interesting
trend_changes = [0, 40, 80, 120, 160, 200]
for i in range(len(trend_changes) - 1):
    start, end = trend_changes[i], trend_changes[i + 1]
    if i % 2 == 0:
        returns[start:end] += 0.003  # Uptrend
    else:
        returns[start:end] -= 0.002  # Downtrend

prices = base_price * np.cumprod(1 + returns)

# Calculate Kagi chart data with 4% reversal threshold
reversal_pct = 0.04
kagi_data = []
direction = 1  # 1 for up (yang), -1 for down (yin)
current_price = prices[0]
high_point = prices[0]
low_point = prices[0]
kagi_x = 0

# Initialize first point
kagi_data.append({"x": kagi_x, "y": round(current_price, 2), "direction": direction})

for price in prices[1:]:
    if direction == 1:  # Currently in uptrend
        if price > high_point:
            high_point = price
            # Update the last point
            kagi_data[-1]["y"] = round(high_point, 2)
        elif price <= high_point * (1 - reversal_pct):
            # Reversal to downtrend
            kagi_x += 1
            direction = -1
            low_point = price
            kagi_data.append({"x": kagi_x, "y": round(price, 2), "direction": direction})
    else:  # Currently in downtrend
        if price < low_point:
            low_point = price
            # Update the last point
            kagi_data[-1]["y"] = round(low_point, 2)
        elif price >= low_point * (1 + reversal_pct):
            # Reversal to uptrend
            kagi_x += 1
            direction = 1
            high_point = price
            kagi_data.append({"x": kagi_x, "y": round(price, 2), "direction": direction})

# Build series data for Highcharts with segment colors
yang_segments = []  # Thick green lines (bullish)
yin_segments = []  # Thin vermillion lines (bearish)

for i in range(len(kagi_data) - 1):
    p1 = kagi_data[i]
    p2 = kagi_data[i + 1]

    # Vertical segment
    if p2["direction"] == 1:  # Yang (up)
        yang_segments.extend([[p1["x"], p1["y"]], [p1["x"], p2["y"]], None])
    else:  # Yin (down)
        yin_segments.extend([[p1["x"], p1["y"]], [p1["x"], p2["y"]], None])

    # Horizontal segment (shoulder or waist)
    if i < len(kagi_data) - 2:
        if p2["direction"] == 1:
            yang_segments.extend([[p1["x"], p2["y"]], [p2["x"], p2["y"]], None])
        else:
            yin_segments.extend([[p1["x"], p2["y"]], [p2["x"], p2["y"]], None])

# Create chart using highcharts-core Python library
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "spacingBottom": 100,
    "spacingTop": 80,
}

# Title
chart.options.title = {
    "text": "kagi-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK},
    "margin": 40,
}

chart.options.subtitle = {
    "text": "Stock Price Analysis with 4% Reversal Threshold",
    "style": {"fontSize": "22px", "color": INK_SOFT},
}

# X-axis
chart.options.x_axis = {
    "title": {"text": "Kagi Line Index", "style": {"fontSize": "22px", "color": INK}, "margin": 20},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Price ($)", "style": {"fontSize": "22px", "color": INK}, "margin": 20},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}, "format": "${value}"},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

# Legend
chart.options.legend = {
    "enabled": True,
    "align": "center",
    "verticalAlign": "bottom",
    "layout": "horizontal",
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "symbolWidth": 50,
    "itemDistance": 60,
    "margin": 30,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}

# Plot options
chart.options.plot_options = {"line": {"marker": {"enabled": False}, "connectNulls": False}}

# Credits
chart.options.credits = {"enabled": False}

# Create Yang (Bullish) series - green
yang_series = LineSeries()
yang_series.name = "Yang (Bullish)"
yang_series.data = yang_segments
yang_series.color = YANG_COLOR
yang_series.line_width = 8
yang_series.z_index = 2

# Create Yin (Bearish) series - vermillion
yin_series = LineSeries()
yin_series.name = "Yin (Bearish)"
yin_series.data = yin_segments
yin_series.color = YIN_COLOR
yin_series.line_width = 4
yin_series.z_index = 1

# Add series to chart
chart.add_series(yang_series)
chart.add_series(yin_series)

# Download Highcharts JS for rendering
highcharts_url = "https://code.highcharts.com/highcharts.js"
req = urllib.request.Request(highcharts_url)
req.add_header("User-Agent", "Mozilla/5.0 (X11; Linux x86_64)")
req.add_header("Referer", "http://localhost")
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with chart using highcharts-core
chart_js = chart.to_js_literal()

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; padding:0; overflow:hidden; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px; margin:0; padding:0;"></div>
    <script>{chart_js}</script>
</body>
</html>"""

# Save HTML artifact for interactive viewing
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
chrome_options.add_argument("--window-size=4900,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render

driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
