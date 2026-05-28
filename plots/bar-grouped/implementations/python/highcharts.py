""" anyplot.ai
bar-grouped: Grouped Bar Chart
Library: highcharts unknown | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-06
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import ColumnSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme-adaptive colors
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette - first series is always #009E73
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Data - Quarterly revenue by product line (realistic business scenario)
categories = ["Q1", "Q2", "Q3", "Q4"]
products = {
    "Electronics": [245, 312, 287, 398],
    "Clothing": [189, 215, 243, 275],
    "Home & Garden": [156, 178, 195, 224],
}

# Create chart with container specified
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for 4800x2700 px
chart.options.chart = {
    "type": "column",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 280,
    "style": {"fontFamily": "Arial, sans-serif", "color": INK},
}

# Title
chart.options.title = {
    "text": "bar-grouped · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "color": INK, "fontWeight": "bold"},
}

# Subtitle for context
chart.options.subtitle = {
    "text": "Quarterly Revenue by Product Line (in thousands USD)",
    "style": {"fontSize": "22px", "color": INK_SOFT},
}

# X-axis configuration
chart.options.x_axis = {
    "categories": categories,
    "title": {"text": "Quarter", "style": {"fontSize": "22px", "color": INK, "fontWeight": "bold"}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
}

# Y-axis configuration
chart.options.y_axis = {
    "min": 0,
    "title": {"text": "Revenue (thousands USD)", "style": {"fontSize": "22px", "color": INK, "fontWeight": "bold"}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}, "format": "${value}K"},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
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
    "backgroundColor": ELEVATED_BG,
    "borderWidth": 1,
    "borderColor": INK_SOFT,
    "shadow": False,
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT, "fontWeight": "normal"},
    "symbolHeight": 16,
    "symbolWidth": 24,
    "symbolRadius": 4,
    "itemMarginBottom": 8,
}

# Plot options for grouped bars
chart.options.plot_options = {
    "column": {
        "groupPadding": 0.15,
        "pointPadding": 0.05,
        "borderWidth": 2,
        "borderColor": PAGE_BG,
        "dataLabels": {
            "enabled": True,
            "format": "${y}K",
            "style": {"fontSize": "16px", "fontWeight": "bold", "color": INK},
        },
    }
}

# Add series for each product
for i, (product_name, values) in enumerate(products.items()):
    series = ColumnSeries()
    series.name = product_name
    series.data = values
    series.color = IMPRINT[i]
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
<body style="margin:0; padding:0; background:{PAGE_BG};">
    <div id="container" style="width:4800px; height:2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save interactive HTML version
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
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
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
