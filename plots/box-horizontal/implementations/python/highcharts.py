"""anyplot.ai
box-horizontal: Horizontal Box Plot
Library: highcharts | Python 3.13
Quality: pending | Created: 2025-12-30
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.boxplot import BoxPlotSeries
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

# Data - Response times by service type with explicit outliers
np.random.seed(42)

categories = ["API Gateway", "Database Query", "File Upload", "Authentication", "Payment Processing"]

# Generate data with different distributions for each service
# Include explicit outliers to better demonstrate box plot capabilities
data = []
for cat in categories:
    if cat == "API Gateway":
        values = np.random.normal(50, 15, 200)
    elif cat == "Database Query":
        values = np.random.normal(120, 40, 200)
    elif cat == "File Upload":
        values = np.random.normal(250, 80, 200)
    elif cat == "Authentication":
        values = np.random.normal(30, 8, 200)
    else:  # Payment Processing
        values = np.random.normal(180, 50, 200)

    # Ensure positive values
    values = np.maximum(values, 5)

    # Add explicit outliers to better demonstrate box plot
    outlier_indices = np.random.choice(len(values), size=3, replace=False)
    if cat == "API Gateway":
        values[outlier_indices] = [150, 160, 170]
    elif cat == "Database Query":
        values[outlier_indices] = [320, 350, 380]
    elif cat == "File Upload":
        values[outlier_indices] = [600, 620, 640]
    elif cat == "Authentication":
        values[outlier_indices] = [120, 130, 140]
    else:  # Payment Processing
        values[outlier_indices] = [450, 480, 510]

    # Calculate quartiles
    q1, median, q3 = np.percentile(values, [25, 50, 75])
    iqr = q3 - q1
    low = max(values.min(), q1 - 1.5 * iqr)
    high = min(values.max(), q3 + 1.5 * iqr)

    # Data as list format for Highcharts boxplot: [low, q1, median, q3, high]
    data.append([round(low, 1), round(q1, 1), round(median, 1), round(q3, 1), round(high, 1)])

# Create chart with container specified
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration - use full 4800x2700 with proper margins
chart.options.chart = {
    "type": "boxplot",
    "inverted": True,
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginLeft": 450,
    "marginBottom": 220,
    "marginTop": 180,
    "marginRight": 120,
}

# Title
chart.options.title = {
    "text": "box-horizontal · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "600", "color": INK},
    "y": 40,
}

# Subtitle for context
chart.options.subtitle = {
    "text": "Response Time Distribution by Service Type",
    "style": {"fontSize": "22px", "color": INK_SOFT},
    "y": 90,
}

# X-axis (categories - shown on left due to inverted)
chart.options.x_axis = {
    "categories": categories,
    "title": {"text": "Service Type", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

# Y-axis (values - shown on bottom due to inverted)
chart.options.y_axis = {
    "title": {"text": "Response Time (ms)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "gridLineColor": GRID,
    "gridLineWidth": 1,
    "min": 0,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

# Legend
chart.options.legend = {"enabled": False}

# Plot options for boxplot styling using Okabe-Ito palette
chart.options.plot_options = {
    "boxplot": {
        "fillColor": BRAND,
        "color": BRAND,
        "lineWidth": 3,
        "medianColor": INK,
        "medianWidth": 4,
        "stemColor": BRAND,
        "stemWidth": 2,
        "whiskerColor": BRAND,
        "whiskerLength": "40%",
        "whiskerWidth": 2,
        "pointWidth": 70,
    }
}

# Create box plot series
series = BoxPlotSeries()
series.name = "Response Time"
series.data = data

chart.add_series(series)

# Download Highcharts JS files (required for headless Chrome)
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Accept": "text/javascript",
    "Referer": "https://www.highcharts.com/",
}

highcharts_url = "https://code.highcharts.com/highcharts.js"
highcharts_req = urllib.request.Request(highcharts_url, headers=headers)
with urllib.request.urlopen(highcharts_req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# BoxPlot requires highcharts-more.js
highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
highcharts_more_req = urllib.request.Request(highcharts_more_url, headers=headers)
with urllib.request.urlopen(highcharts_more_req, timeout=30) as response:
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
<body style="margin:0; padding:0; overflow:hidden; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write HTML for interactive version (theme-suffixed)
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
chrome_options.add_argument("--force-device-scale-factor=1")

driver = webdriver.Chrome(options=chrome_options)
driver.set_window_size(4800, 2700)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
