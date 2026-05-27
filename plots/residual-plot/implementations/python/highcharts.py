""" anyplot.ai
residual-plot: Residual Plot
Library: highcharts unknown | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-10
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
BRAND = "#009E73"  # bluish green — ALWAYS first series
ACCENT_1 = "#C475FD"  # vermillion

# Data: Linear regression example with housing price predictions
np.random.seed(42)

# Generate realistic housing data
n_points = 120
square_feet = np.random.uniform(800, 3500, n_points)
base_price = 50000 + 150 * square_feet
noise = np.random.normal(0, 30000, n_points)
y_true = base_price + noise

# Simulate a fitted linear regression
slope = 148
intercept = 52000
y_pred = intercept + slope * square_feet

# Calculate residuals
residuals = y_true - y_pred

# Identify outliers (beyond ±2 std)
std_residual = np.std(residuals)
mean_residual = np.mean(residuals)
outlier_threshold = 2 * std_residual
is_outlier = np.abs(residuals - mean_residual) > outlier_threshold

# Prepare data for regular points and outliers
regular_data = [[float(y_pred[i]), float(residuals[i])] for i in range(n_points) if not is_outlier[i]]
outlier_data = [[float(y_pred[i]), float(residuals[i])] for i in range(n_points) if is_outlier[i]]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 280,
    "marginLeft": 280,
    "marginTop": 150,
    "marginRight": 220,
    "spacingBottom": 50,
}

# Title
chart.options.title = {
    "text": "residual-plot · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "normal", "color": INK},
}

# X-axis (Fitted Values)
x_min = float(min(y_pred))
x_max = float(max(y_pred))
chart.options.x_axis = {
    "title": {"text": "Fitted Values ($)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "min": x_min - 10000,
    "max": x_max + 10000,
    "tickInterval": 50000,
}

# Y-axis (Residuals)
y_min = float(min(residuals))
y_max = float(max(residuals))
y_axis_min = y_min * 1.1
y_axis_max = y_max * 1.1
chart.options.y_axis = {
    "title": {"text": "Residuals ($)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "min": y_axis_min,
    "max": y_axis_max,
    "tickInterval": 20000,
    "endOnTick": False,
    "startOnTick": False,
    "plotLines": [
        {
            "value": 0,
            "color": BRAND,
            "width": 3,
            "zIndex": 5,
            "label": {"text": "Zero Line", "align": "right", "x": -15, "style": {"fontSize": "18px", "color": BRAND}},
        },
        {
            "value": float(outlier_threshold),
            "color": ACCENT_1,
            "width": 2,
            "dashStyle": "Dash",
            "zIndex": 4,
            "label": {"text": "+2σ", "align": "right", "x": -15, "style": {"fontSize": "18px", "color": ACCENT_1}},
        },
        {
            "value": float(-outlier_threshold),
            "color": ACCENT_1,
            "width": 2,
            "dashStyle": "Dash",
            "zIndex": 4,
            "label": {"text": "-2σ", "align": "right", "x": -15, "style": {"fontSize": "18px", "color": ACCENT_1}},
        },
    ],
}

# Legend
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -60,
    "y": 100,
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "padding": 20,
}

# Plot options
chart.options.plot_options = {
    "scatter": {"marker": {"radius": 8}, "states": {"hover": {"enabled": True, "lineWidthPlus": 0}}}
}

# Regular points series (BRAND color as primary)
regular_series = ScatterSeries()
regular_series.name = "Residuals"
regular_series.data = regular_data
regular_series.color = BRAND
regular_series.marker = {"radius": 8, "fillColor": BRAND, "lineWidth": 1, "lineColor": PAGE_BG}
chart.add_series(regular_series)

# Outlier points series
if outlier_data:
    outlier_series = ScatterSeries()
    outlier_series.name = "Outliers (>2σ)"
    outlier_series.data = outlier_data
    outlier_series.color = ACCENT_1
    outlier_series.marker = {
        "radius": 10,
        "fillColor": ACCENT_1,
        "lineWidth": 1,
        "lineColor": PAGE_BG,
        "symbol": "diamond",
    }
    chart.add_series(outlier_series)

# Download Highcharts JS with retry
highcharts_url = "https://code.highcharts.com/highcharts.js"
highcharts_js = None

for attempt in range(3):
    try:
        request = urllib.request.Request(
            highcharts_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            highcharts_js = response.read().decode("utf-8")
        break
    except urllib.error.HTTPError as e:
        if attempt < 2:
            time.sleep(2)
        elif attempt == 2:
            # Fallback for network issues (e.g., in restricted environments)
            # Use minified Highcharts from jsDelivr
            try:
                jsdelivr_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.min.js"
                request2 = urllib.request.Request(jsdelivr_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(request2, timeout=60) as response:
                    highcharts_js = response.read().decode("utf-8")
            except Exception as fallback_err:
                raise Exception(f"Failed to download Highcharts from both CDN endpoints: {e}") from fallback_err
    except Exception:
        if attempt == 2:
            raise
        time.sleep(2)

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

# Write temp HTML for screenshot
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

# Cleanup
Path(temp_path).unlink()
