""" anyplot.ai
scatter-regression-linear: Scatter Plot with Linear Regression
Library: highcharts unknown | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-06
"""

import os
import tempfile
import time
from pathlib import Path

import numpy as np
import requests
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaRangeSeries, LineSeries
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
IMPRINT = [
    "#009E73",  # Brand green (primary)
    "#C475FD",  # Vermillion
    "#4467A3",  # Blue
    "#BD8233",  # Reddish purple
    "#AE3030",  # Orange
    "#2ABCCD",  # Sky blue
]

# Data: Advertising spend vs sales revenue
np.random.seed(42)
n_points = 80
x = np.random.uniform(10, 100, n_points)
noise = np.random.normal(0, 8, n_points)
y = 2.5 * x + 15 + noise  # True relationship: y = 2.5x + 15

# Linear regression calculation
x_mean = np.mean(x)
y_mean = np.mean(y)
slope = np.sum((x - x_mean) * (y - y_mean)) / np.sum((x - x_mean) ** 2)
intercept = y_mean - slope * x_mean

# Calculate R²
y_pred = slope * x + intercept
ss_res = np.sum((y - y_pred) ** 2)
ss_tot = np.sum((y - y_mean) ** 2)
r_squared = 1 - (ss_res / ss_tot)

# Calculate 95% confidence interval for the regression line
n = len(x)
se = np.sqrt(ss_res / (n - 2))  # Standard error of the estimate
x_sorted = np.linspace(x.min(), x.max(), 100)
y_fit = slope * x_sorted + intercept

# Standard error of the regression line at each x
se_fit = se * np.sqrt(1 / n + (x_sorted - x_mean) ** 2 / np.sum((x - x_mean) ** 2))
t_value = 1.96  # Approx for 95% CI
ci_upper = y_fit + t_value * se_fit
ci_lower = y_fit - t_value * se_fit

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart settings with theme-adaptive colors
chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "style": {"fontFamily": "Arial, sans-serif", "color": INK},
    "spacingBottom": 150,
    "spacingLeft": 60,
}

# Title with theme-adaptive styling
chart.options.title = {
    "text": "scatter-regression-linear · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK},
}

# Subtitle with regression equation and R²
equation = f"y = {slope:.2f}x + {intercept:.2f}"
r2_text = f"R² = {r_squared:.3f}"
chart.options.subtitle = {"text": f"{equation}  |  {r2_text}", "style": {"fontSize": "22px", "color": INK_SOFT}}

# Axes with theme-adaptive colors
chart.options.x_axis = {
    "title": {"text": "Advertising Spend ($K)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
}

chart.options.y_axis = {
    "title": {"text": "Sales Revenue ($K)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
}

# Legend with theme-adaptive styling
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
    "scatter": {"marker": {"radius": 8}},
    "line": {"lineWidth": 3, "marker": {"enabled": False}},
    "arearange": {"lineWidth": 0, "marker": {"enabled": False}},
}

# Series 1: Confidence interval band (add first so it's behind other elements)
ci_color_alpha = "rgba(0, 158, 115, 0.15)"  # Okabe-Ito green with low alpha
ci_data = [[float(x_sorted[i]), float(ci_lower[i]), float(ci_upper[i])] for i in range(len(x_sorted))]
ci_series = AreaRangeSeries()
ci_series.data = ci_data
ci_series.name = "95% Confidence Interval"
ci_series.color = ci_color_alpha
ci_series.fill_opacity = 0.15
chart.add_series(ci_series)

# Series 2: Regression line (using Okabe-Ito blue for contrast)
line_data = [[float(x_sorted[i]), float(y_fit[i])] for i in range(len(x_sorted))]
line_series = LineSeries()
line_series.data = line_data
line_series.name = "Regression Line"
line_series.color = IMPRINT[2]  # Blue
chart.add_series(line_series)

# Series 3: Scatter points (using brand green)
scatter_data = [[float(x[i]), float(y[i])] for i in range(n_points)]
scatter_series = ScatterSeries()
scatter_series.data = scatter_data
scatter_series.name = "Data Points"
scatter_series.color = IMPRINT[0]  # Brand green
chart.add_series(scatter_series)

# Set colors for the chart
chart.options.colors = IMPRINT

# Credits
chart.options.credits = {"enabled": False}


# Download Highcharts JS via jsDelivr CDN (official CDN is Cloudflare-protected)
def download_js(url):
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception:
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
            else:
                raise


# Use jsDelivr which is not blocked by Cloudflare
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js"
highcharts_js = download_js(highcharts_url)

highcharts_more_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts-more.js"
highcharts_more_js = download_js(highcharts_more_url)

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

# Save HTML file with theme suffix
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with Selenium
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
time.sleep(5)  # Wait for chart to render
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
