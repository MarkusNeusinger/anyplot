""" anyplot.ai
histogram-density: Density Histogram
Library: highcharts unknown | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-11
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaSplineSeries
from highcharts_core.options.series.bar import ColumnSeries
from scipy.special import gamma
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"
IMPRINT = ["#009E73", "#C475FD"]

# Data - Generate right-skewed response time data
np.random.seed(42)
values = np.random.gamma(shape=3, scale=8, size=500)

# Calculate density histogram
n_bins = 20
counts, bin_edges = np.histogram(values, bins=n_bins, density=True)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
bin_width = bin_edges[1] - bin_edges[0]

# Generate theoretical gamma PDF for overlay
x_pdf = np.linspace(values.min() - 2, values.max() + 5, 200)
shape, scale = 3, 8
y_pdf = (x_pdf ** (shape - 1) * np.exp(-x_pdf / scale)) / (scale**shape * gamma(shape))

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "column",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 200,
    "marginLeft": 200,
    "marginRight": 100,
    "marginTop": 150,
    "spacingBottom": 30,
}

# Title
chart.options.title = {
    "text": "histogram-density · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "600", "color": INK},
}

# X-axis
chart.options.x_axis = {
    "title": {"text": "Response Time (milliseconds)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "tickInterval": 10,
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Probability Density", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "gridLineColor": GRID,
    "gridLineWidth": 1,
    "min": 0,
    "tickInterval": 0.01,
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 100,
    "floating": True,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}

# Plot options
chart.options.plot_options = {
    "column": {"groupPadding": 0, "pointPadding": 0, "borderWidth": 0, "pointWidth": bin_width * 35},
    "areaspline": {"fillOpacity": 0.15, "lineWidth": 4, "marker": {"enabled": False}},
}

# Colors
chart.options.colors = IMPRINT

# Add histogram series (using column chart)
histogram_series = ColumnSeries()
histogram_series.name = "Empirical Density"
histogram_series.data = [[float(center), float(count)] for center, count in zip(bin_centers, counts, strict=True)]
histogram_series.color = BRAND

chart.add_series(histogram_series)

# Add theoretical PDF overlay as area spline
pdf_series = AreaSplineSeries()
pdf_series.name = "Gamma PDF"
pdf_series.data = [[float(x), float(y)] for x, y in zip(x_pdf, y_pdf, strict=True)]
pdf_series.color = "#C475FD"

chart.add_series(pdf_series)

# Credits
chart.options.credits = {"enabled": False}

# Download Highcharts JS (with fallback)
hc_urls = ["https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"]
highcharts_js = None
for url in hc_urls:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
        break
    except Exception:
        continue
if highcharts_js is None:
    raise RuntimeError("Failed to download Highcharts JS")

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

# Write temp HTML and take screenshot for PNG
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
