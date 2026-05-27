""" anyplot.ai
cat-box-strip: Box Plot with Strip Overlay
Library: highcharts unknown | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-13
"""

import os
import tempfile
import time
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.boxplot import BoxPlotSeries
from highcharts_core.options.series.scatter import ScatterSeries
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
BRAND = "#009E73"  # Position 1 — always first series
OI_SECONDARY = "#C475FD"  # Position 2

# Data - Plant growth measurements under different light conditions
np.random.seed(42)
categories = ["Low Light", "Medium Light", "High Light", "Full Sun"]

# Generate realistic plant growth data (cm) with different distributions
data_by_category = {
    "Low Light": np.random.normal(12, 3, 40),
    "Medium Light": np.random.normal(22, 4, 45),
    "High Light": np.random.normal(35, 5, 50),
    "Full Sun": np.concatenate([np.random.normal(42, 4, 45), np.array([20, 22, 58, 60])]),
}

# Calculate box plot statistics for each category
box_data = []
for cat in categories:
    values = data_by_category[cat]
    q1 = np.percentile(values, 25)
    median = np.percentile(values, 50)
    q3 = np.percentile(values, 75)
    iqr = q3 - q1
    whisker_low = max(values.min(), q1 - 1.5 * iqr)
    whisker_high = min(values.max(), q3 + 1.5 * iqr)
    box_data.append([whisker_low, q1, median, q3, whisker_high])

# Prepare scatter data with jitter for strip overlay
scatter_data = []
for i, cat in enumerate(categories):
    values = data_by_category[cat]
    for val in values:
        jitter = np.random.uniform(-0.2, 0.2)
        scatter_data.append([i + jitter, float(val)])

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "boxplot",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 200,
    "spacingBottom": 50,
    "style": {"fontFamily": "Arial, sans-serif", "color": INK},
}

# Title
chart.options.title = {
    "text": "cat-box-strip · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK},
}

# X-axis
chart.options.x_axis = {
    "categories": categories,
    "title": {"text": "Light Condition", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Plant Growth (cm)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "gridLineWidth": 1,
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 100,
}

# Plot options with Okabe-Ito colors
chart.options.plot_options = {
    "boxplot": {
        "fillColor": "rgba(0, 158, 115, 0.15)",
        "color": BRAND,
        "lineWidth": 3,
        "medianWidth": 5,
        "medianColor": OI_SECONDARY,
        "stemWidth": 3,
        "stemColor": BRAND,
        "whiskerWidth": 4,
        "whiskerColor": BRAND,
        "whiskerLength": "50%",
    },
    "scatter": {"marker": {"radius": 8, "symbol": "circle", "fillColor": BRAND, "lineWidth": 1, "lineColor": PAGE_BG}},
}

# Add box plot series
box_series = BoxPlotSeries()
box_series.name = "Distribution Statistics"
box_series.data = box_data
box_series.color = BRAND
chart.add_series(box_series)

# Add scatter series for strip plot
scatter_series = ScatterSeries()
scatter_series.name = "Individual Measurements"
scatter_series.data = scatter_data
scatter_series.color = BRAND
chart.add_series(scatter_series)

# Load Highcharts JS files from npm installation
with open("/tmp/node_modules/highcharts/highcharts.js", "r", encoding="utf-8") as f:
    highcharts_js = f.read()

with open("/tmp/node_modules/highcharts/highcharts-more.js", "r", encoding="utf-8") as f:
    highcharts_more_js = f.read()

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

# Write HTML file
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Setup Chrome for screenshot
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
