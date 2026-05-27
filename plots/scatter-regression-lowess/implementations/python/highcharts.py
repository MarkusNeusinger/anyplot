""" anyplot.ai
scatter-regression-lowess: Scatter Plot with LOWESS Regression
Library: highcharts unknown | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-14
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


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

BRAND = "#009E73"  # Okabe-Ito position 1
ACCENT = "#C475FD"  # Okabe-Ito position 2 for LOWESS curve


def lowess(x, y, frac=0.3):
    """Simple LOWESS implementation using tricube weighting."""
    n = len(x)
    k = int(np.ceil(frac * n))
    y_smooth = np.zeros(n)
    sorted_idx = np.argsort(x)
    x_sorted = x[sorted_idx]
    y_sorted = y[sorted_idx]

    for i in range(n):
        distances = np.abs(x_sorted - x_sorted[i])
        nearest_idx = np.argsort(distances)[:k]
        max_dist = distances[nearest_idx[-1]]
        if max_dist == 0:
            max_dist = 1.0
        u = distances[nearest_idx] / max_dist
        weights = (1 - u**3) ** 3
        x_local = x_sorted[nearest_idx]
        y_local = y_sorted[nearest_idx]
        w_sum = np.sum(weights)
        wx_sum = np.sum(weights * x_local)
        wy_sum = np.sum(weights * y_local)
        wxx_sum = np.sum(weights * x_local * x_local)
        wxy_sum = np.sum(weights * x_local * y_local)
        denom = w_sum * wxx_sum - wx_sum**2
        if abs(denom) < 1e-10:
            y_smooth[i] = wy_sum / w_sum if w_sum > 0 else y_sorted[i]
        else:
            slope = (w_sum * wxy_sum - wx_sum * wy_sum) / denom
            intercept = (wy_sum - slope * wx_sum) / w_sum
            y_smooth[i] = slope * x_sorted[i] + intercept

    result = np.zeros(n)
    result[sorted_idx] = y_smooth
    return x, result


# Data - Non-linear relationship
np.random.seed(42)
n_points = 200
x = np.linspace(0, 10, n_points)
y = 3 * np.sin(x * 1.2) + 0.3 * x**2 - 0.5 * x + np.random.normal(0, 1.5, n_points)

# Compute LOWESS regression curve
x_lowess, y_lowess = lowess(x, y, frac=0.3)

# Chart setup
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 200,
    "marginLeft": 180,
    "spacingTop": 60,
    "spacingRight": 100,
}

# Title and subtitle
chart.options.title = {
    "text": "scatter-regression-lowess · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK},
}

chart.options.subtitle = {
    "text": "Non-linear Relationship with LOWESS Smoothing",
    "style": {"fontSize": "22px", "color": INK_SOFT},
}

# X-axis configuration
chart.options.x_axis = {
    "title": {"text": "Input Variable", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "gridLineWidth": 1,
}

# Y-axis configuration
chart.options.y_axis = {
    "title": {"text": "Output Variable", "style": {"fontSize": "22px", "color": INK}},
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

# Plot options
chart.options.plot_options = {
    "scatter": {"marker": {"radius": 8, "fillColor": BRAND, "lineWidth": 1, "lineColor": PAGE_BG}},
    "spline": {"marker": {"enabled": False}, "lineWidth": 5},
}

# Add scatter series (data points)
scatter_series = ScatterSeries()
scatter_series.name = "Data Points"
scatter_series.data = [[float(xi), float(yi)] for xi, yi in zip(x, y, strict=False)]
scatter_series.color = BRAND
scatter_series.marker = {"radius": 8, "fillColor": BRAND, "lineWidth": 1, "lineColor": PAGE_BG}
chart.add_series(scatter_series)

# Add LOWESS curve as spline series
lowess_series = SplineSeries()
lowess_series.name = "LOWESS Curve"
lowess_series.data = [[float(xi), float(yi)] for xi, yi in zip(x_lowess, y_lowess, strict=False)]
lowess_series.color = ACCENT
lowess_series.marker = {"enabled": False}
lowess_series.line_width = 5
chart.add_series(lowess_series)

# Download Highcharts JS for inline embedding
highcharts_url = "https://code.highcharts.com/highcharts.js"
req = urllib.request.Request(
    highcharts_url,
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.highcharts.com/",
    },
)
try:
    with urllib.request.urlopen(req, timeout=30) as response:
        highcharts_js = response.read().decode("utf-8")
except urllib.error.HTTPError as e:
    import sys

    print(f"ERROR: Failed to download Highcharts JS: {e}", file=sys.stderr)
    print(f"URL: {highcharts_url}", file=sys.stderr)
    sys.exit(1)

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

# Write HTML artifact
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
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
