""" anyplot.ai
histogram-stacked: Stacked Histogram
Library: highcharts unknown | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-12
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import ColumnSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette (first color always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data: Generate three groups with different distributions
np.random.seed(42)
group_a = np.random.normal(loc=45, scale=12, size=150)
group_b = np.random.normal(loc=55, scale=10, size=120)
group_c = np.random.normal(loc=65, scale=15, size=100)

# Combine all data to determine common bin edges
all_data = np.concatenate([group_a, group_b, group_c])
bin_edges = np.histogram_bin_edges(all_data, bins=15)
bin_centers = [(bin_edges[i] + bin_edges[i + 1]) / 2 for i in range(len(bin_edges) - 1)]
bin_labels = [f"{bin_edges[i]:.0f}-{bin_edges[i + 1]:.0f}" for i in range(len(bin_edges) - 1)]

# Calculate histogram counts for each group
counts_a, _ = np.histogram(group_a, bins=bin_edges)
counts_b, _ = np.histogram(group_b, bins=bin_edges)
counts_c, _ = np.histogram(group_c, bins=bin_edges)

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart options
chart.options.chart = {
    "type": "column",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 100,
    "marginLeft": 100,
    "marginRight": 100,
    "marginTop": 100,
}

# Title
chart.options.title = {
    "text": "histogram-stacked · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "normal", "color": INK},
    "margin": 30,
}

# X-axis (categories for bins)
chart.options.x_axis = {
    "categories": bin_labels,
    "title": {"text": "Measurement Range (units)", "style": {"fontSize": "22px", "color": INK}, "margin": 20},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Frequency (count)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
}

# Plot options for stacking
chart.options.plot_options = {"column": {"stacking": "normal", "borderWidth": 0, "dataLabels": {"enabled": False}}}

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
    "x": -20,
    "y": 20,
}

# Add series for each group
series_a = ColumnSeries()
series_a.data = [int(c) for c in counts_a]
series_a.name = "Group A"
series_a.color = IMPRINT[0]

series_b = ColumnSeries()
series_b.data = [int(c) for c in counts_b]
series_b.name = "Group B"
series_b.color = IMPRINT[1]

series_c = ColumnSeries()
series_c.data = [int(c) for c in counts_c]
series_c.name = "Group C"
series_c.color = IMPRINT[2]

chart.add_series(series_a)
chart.add_series(series_b)
chart.add_series(series_c)

# Export to PNG via Selenium
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js"
req = urllib.request.Request(
    highcharts_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML artifact
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
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
