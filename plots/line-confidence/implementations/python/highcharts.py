"""anyplot.ai
line-confidence: Line Plot with Confidence Interval
Library: highcharts | Python 3.13
Quality: pending | Created: 2025-12-26
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaRangeSeries, LineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data: Simulated model predictions with 95% confidence interval
np.random.seed(42)
x = np.arange(1, 51)  # 50 data points (days 1-50)
base_trend = 100 + 2.5 * x + 15 * np.sin(x * 0.3)  # Trend with oscillation
noise = np.random.randn(50) * 5  # Random noise
y = base_trend + noise  # Central line (predictions)
uncertainty = 8 + 0.15 * x  # Uncertainty grows over time
y_lower = y - 1.96 * uncertainty  # Lower 95% CI
y_upper = y + 1.96 * uncertainty  # Upper 95% CI

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "style": {"fontFamily": "Arial, sans-serif", "color": INK},
    "marginBottom": 250,
    "spacingBottom": 60,
}

# Title
chart.options.title = {"text": "line-confidence · highcharts · anyplot.ai", "style": {"fontSize": "28px", "color": INK}}

# Subtitle for context
chart.options.subtitle = {
    "text": "Model Predictions with 95% Confidence Interval",
    "style": {"fontSize": "22px", "color": INK_SOFT},
}

# X-axis configuration
chart.options.x_axis = {
    "title": {"text": "Day", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "tickInterval": 5,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineWidth": 2,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

# Y-axis configuration
chart.options.y_axis = {
    "title": {"text": "Predicted Value", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

# Legend configuration
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 100,
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "itemMarginBottom": 15,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}

# Plot options
chart.options.plot_options = {
    "series": {"animation": False},
    "line": {"lineWidth": 3, "marker": {"enabled": False}},
    "arearange": {"fillOpacity": 0.3, "lineWidth": 0, "marker": {"enabled": False}},
}

# Add confidence band (arearange series)
confidence_data = [[int(x[i]), float(y_lower[i]), float(y_upper[i])] for i in range(len(x))]
confidence_series = AreaRangeSeries()
confidence_series.data = confidence_data
confidence_series.name = "95% Confidence Interval"
confidence_series.color = BRAND
confidence_series.fill_opacity = 0.3

# Add central line
line_data = [[int(x[i]), float(y[i])] for i in range(len(x))]
line_series = LineSeries()
line_series.data = line_data
line_series.name = "Prediction"
line_series.color = BRAND

# Add series (confidence band first, then line on top)
chart.add_series(confidence_series)
chart.add_series(line_series)

# Download Highcharts JS modules
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js"
req = urllib.request.Request(
    highcharts_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

highcharts_more_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts-more.js"
req_more = urllib.request.Request(
    highcharts_more_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
)
with urllib.request.urlopen(req_more, timeout=30) as response:
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
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write HTML file for interactive viewing
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Configure Chrome for headless screenshot
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
