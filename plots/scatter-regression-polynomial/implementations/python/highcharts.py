""" anyplot.ai
scatter-regression-polynomial: Scatter Plot with Polynomial Regression
Library: highcharts unknown | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-07
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.scatter import ScatterSeries
from highcharts_core.options.series.spline import SplineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"

# Data - Simulating diminishing returns (e.g., advertising spend vs revenue)
np.random.seed(42)
n_points = 80
x = np.linspace(1, 20, n_points)
# Quadratic relationship with diminishing returns: y = -0.3x² + 10x + 5
y_true = -0.3 * x**2 + 10 * x + 5
noise = np.random.normal(0, 5, n_points)
y = y_true + noise

# Fit polynomial regression (degree 2)
coeffs = np.polyfit(x, y, 2)
poly = np.poly1d(coeffs)
x_fit = np.linspace(x.min(), x.max(), 200)
y_fit = poly(x_fit)

# Calculate R² value
y_pred = poly(x)
ss_res = np.sum((y - y_pred) ** 2)
ss_tot = np.sum((y - np.mean(y)) ** 2)
r_squared = 1 - (ss_res / ss_tot)

# Format equation
a, b, c = coeffs
equation = f"y = {a:.3f}x² + {b:.3f}x + {c:.3f}"

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "spacingBottom": 80,
    "spacingTop": 80,
    "spacingLeft": 80,
    "spacingRight": 80,
}

# Title with spec-id format
chart.options.title = {
    "text": "scatter-regression-polynomial · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK},
}

# Subtitle showing equation and R²
chart.options.subtitle = {
    "text": f"{equation} | R² = {r_squared:.4f}",
    "style": {"fontSize": "22px", "color": INK_SOFT},
}

# X-axis
chart.options.x_axis = {
    "title": {"text": "Advertising Spend ($k)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Revenue ($k)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

# Legend
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -60,
    "y": 100,
    "floating": True,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "itemMarginTop": 10,
    "itemMarginBottom": 10,
}

# Tooltip
chart.options.tooltip = {
    "style": {"fontSize": "18px"},
    "headerFormat": "",
    "pointFormat": "Spend: ${point.x:.1f}k<br/>Revenue: ${point.y:.1f}k",
}

# Scatter series (data points)
scatter_series = ScatterSeries()
scatter_series.data = [[float(xi), float(yi)] for xi, yi in zip(x, y, strict=True)]
scatter_series.name = "Data Points"
scatter_series.color = BRAND
scatter_series.marker = {"radius": 8, "fillColor": BRAND, "lineWidth": 1, "lineColor": PAGE_BG}
scatter_series.pointPadding = 0
scatter_series.opacity = 0.65

# Regression curve (spline for smooth curve)
regression_series = SplineSeries()
regression_series.data = [[float(xi), float(yi)] for xi, yi in zip(x_fit, y_fit, strict=True)]
regression_series.name = f"Polynomial Fit (R² = {r_squared:.3f})"
regression_series.color = "#C475FD"
regression_series.lineWidth = 3
regression_series.marker = {"enabled": False}

# Add series
chart.add_series(scatter_series)
chart.add_series(regression_series)

# Color palette
chart.options.colors = [BRAND, "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Download Highcharts JS from alternative CDN
highcharts_urls = [
    "https://cdn.jsdelivr.net/npm/highcharts@12/highcharts.js",
    "https://code.highcharts.com/highcharts.js",
]
highcharts_js = None
for highcharts_url in highcharts_urls:
    for attempt in range(2):
        try:
            req = urllib.request.Request(
                highcharts_url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                highcharts_js = response.read().decode("utf-8")
            break
        except Exception:
            if attempt == 0:
                time.sleep(2)
            continue
    if highcharts_js:
        break

if not highcharts_js:
    raise RuntimeError("Failed to download Highcharts from all CDNs")

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

# Save HTML for interactive version
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Selenium screenshot
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
