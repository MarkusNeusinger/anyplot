""" pyplots.ai
survival-kaplan-meier: Kaplan-Meier Survival Plot
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-29
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaRangeSeries, LineSeries
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Generate synthetic clinical trial survival data
np.random.seed(42)
n_patients = 120

# Group A: Standard treatment - Weibull distribution
times_a = np.random.weibull(1.5, n_patients // 2) * 24
events_a = np.random.binomial(1, 0.7, n_patients // 2)  # 70% event rate
max_time = 36
times_a = np.minimum(times_a, max_time)  # Censored at study end

# Group B: New treatment - better survival
times_b = np.random.weibull(1.8, n_patients // 2) * 30
events_b = np.random.binomial(1, 0.55, n_patients // 2)  # 55% event rate
times_b = np.minimum(times_b, max_time)

# Kaplan-Meier calculation for Group A (inline, no function)
sorted_idx_a = np.argsort(times_a)
times_a_sorted = times_a[sorted_idx_a]
events_a_sorted = events_a[sorted_idx_a]
unique_times_a = np.unique(times_a_sorted)
n_at_risk_a = len(times_a_sorted)
survival_a = 1.0
var_sum_a = 0.0
km_times_a = [0.0]
km_survival_a = [1.0]
km_lower_a = [1.0]
km_upper_a = [1.0]
censored_times_a = []
censored_survival_a = []

for t in unique_times_a:
    mask = times_a_sorted == t
    d = events_a_sorted[mask].sum()
    c = (~events_a_sorted[mask].astype(bool)).sum()
    if d > 0:
        survival_a *= 1 - d / n_at_risk_a
        if n_at_risk_a > d:
            var_sum_a += d / (n_at_risk_a * (n_at_risk_a - d))
    se = survival_a * np.sqrt(var_sum_a) if var_sum_a > 0 else 0
    lower = max(0, survival_a - 1.96 * se)
    upper = min(1, survival_a + 1.96 * se)
    km_times_a.append(float(t))
    km_survival_a.append(float(survival_a))
    km_lower_a.append(float(lower))
    km_upper_a.append(float(upper))
    if c > 0:
        censored_times_a.append(float(t))
        censored_survival_a.append(float(survival_a))
    n_at_risk_a -= d + c

# Kaplan-Meier calculation for Group B (inline, no function)
sorted_idx_b = np.argsort(times_b)
times_b_sorted = times_b[sorted_idx_b]
events_b_sorted = events_b[sorted_idx_b]
unique_times_b = np.unique(times_b_sorted)
n_at_risk_b = len(times_b_sorted)
survival_b = 1.0
var_sum_b = 0.0
km_times_b = [0.0]
km_survival_b = [1.0]
km_lower_b = [1.0]
km_upper_b = [1.0]
censored_times_b = []
censored_survival_b = []

for t in unique_times_b:
    mask = times_b_sorted == t
    d = events_b_sorted[mask].sum()
    c = (~events_b_sorted[mask].astype(bool)).sum()
    if d > 0:
        survival_b *= 1 - d / n_at_risk_b
        if n_at_risk_b > d:
            var_sum_b += d / (n_at_risk_b * (n_at_risk_b - d))
    se = survival_b * np.sqrt(var_sum_b) if var_sum_b > 0 else 0
    lower = max(0, survival_b - 1.96 * se)
    upper = min(1, survival_b + 1.96 * se)
    km_times_b.append(float(t))
    km_survival_b.append(float(survival_b))
    km_lower_b.append(float(lower))
    km_upper_b.append(float(upper))
    if c > 0:
        censored_times_b.append(float(t))
        censored_survival_b.append(float(survival_b))
    n_at_risk_b -= d + c

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 250,
    "marginLeft": 220,
    "marginRight": 150,
}

# Title
chart.options.title = {
    "text": "survival-kaplan-meier · highcharts · pyplots.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold"},
}

# Subtitle
chart.options.subtitle = {
    "text": "Clinical Trial: Survival Probability Over Time",
    "style": {"fontSize": "42px", "color": "#666666"},
}

# X-axis configuration
chart.options.x_axis = {
    "title": {"text": "Time (Months)", "style": {"fontSize": "48px"}, "margin": 30},
    "labels": {"style": {"fontSize": "36px"}, "y": 40},
    "min": 0,
    "max": 40,
    "tickInterval": 6,
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "gridLineDashStyle": "Dash",
    "lineWidth": 2,
    "lineColor": "#333333",
}

# Y-axis configuration
chart.options.y_axis = {
    "title": {"text": "Survival Probability", "style": {"fontSize": "48px"}},
    "labels": {"style": {"fontSize": "36px"}},
    "min": 0,
    "max": 1.0,
    "tickInterval": 0.2,
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "gridLineDashStyle": "Dash",
}

# Legend configuration - positioned closer to the data (left side, middle)
chart.options.legend = {
    "enabled": True,
    "align": "left",
    "verticalAlign": "middle",
    "layout": "vertical",
    "x": 250,
    "y": -200,
    "itemStyle": {"fontSize": "36px"},
    "itemMarginBottom": 20,
    "backgroundColor": "rgba(255, 255, 255, 0.85)",
    "borderRadius": 5,
    "padding": 15,
}

# Colors
color_a = "#306998"  # Python Blue
color_b = "#FFD43B"  # Python Yellow

# Plot options for step function
chart.options.plot_options = {
    "series": {"animation": False},
    "line": {"step": "left", "lineWidth": 5, "marker": {"enabled": False}},
    "arearange": {"step": "left", "fillOpacity": 0.2, "lineWidth": 0, "marker": {"enabled": False}},
    "scatter": {"marker": {"symbol": "diamond", "radius": 8, "enabled": True}, "enableMouseTracking": True},
}

# --- Group A: Confidence Interval ---
ci_data_a = [[km_times_a[i], km_lower_a[i], km_upper_a[i]] for i in range(len(km_times_a))]
ci_series_a = AreaRangeSeries()
ci_series_a.data = ci_data_a
ci_series_a.name = "95% CI (Standard)"
ci_series_a.color = color_a
ci_series_a.show_in_legend = False
chart.add_series(ci_series_a)

# --- Group A: Survival Curve ---
curve_data_a = [[km_times_a[i], km_survival_a[i]] for i in range(len(km_times_a))]
curve_series_a = LineSeries()
curve_series_a.data = curve_data_a
curve_series_a.name = "Standard Treatment"
curve_series_a.color = color_a
chart.add_series(curve_series_a)

# --- Group A: Censored Marks (tick marks on curve) ---
if censored_times_a:
    censor_data_a = [{"x": censored_times_a[i], "y": censored_survival_a[i]} for i in range(len(censored_times_a))]
    censor_series_a = ScatterSeries()
    censor_series_a.data = censor_data_a
    censor_series_a.name = "Censored (Standard)"
    censor_series_a.color = color_a
    censor_series_a.marker = {
        "symbol": "diamond",
        "lineWidth": 3,
        "lineColor": color_a,
        "fillColor": "#ffffff",
        "radius": 8,
    }
    censor_series_a.show_in_legend = False
    chart.add_series(censor_series_a)

# --- Group B: Confidence Interval ---
ci_data_b = [[km_times_b[i], km_lower_b[i], km_upper_b[i]] for i in range(len(km_times_b))]
ci_series_b = AreaRangeSeries()
ci_series_b.data = ci_data_b
ci_series_b.name = "95% CI (New)"
ci_series_b.color = color_b
ci_series_b.show_in_legend = False
chart.add_series(ci_series_b)

# --- Group B: Survival Curve ---
curve_data_b = [[km_times_b[i], km_survival_b[i]] for i in range(len(km_times_b))]
curve_series_b = LineSeries()
curve_series_b.data = curve_data_b
curve_series_b.name = "New Treatment"
curve_series_b.color = color_b
chart.add_series(curve_series_b)

# --- Group B: Censored Marks (tick marks on curve) ---
if censored_times_b:
    censor_data_b = [{"x": censored_times_b[i], "y": censored_survival_b[i]} for i in range(len(censored_times_b))]
    censor_series_b = ScatterSeries()
    censor_series_b.data = censor_data_b
    censor_series_b.name = "Censored (New)"
    censor_series_b.color = color_b
    censor_series_b.marker = {
        "symbol": "diamond",
        "lineWidth": 3,
        "lineColor": color_b,
        "fillColor": "#ffffff",
        "radius": 8,
    }
    censor_series_b.show_in_legend = False
    chart.add_series(censor_series_b)

# Download Highcharts JS modules
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
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
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML file for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
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
chrome_options.add_argument("--window-size=4800,2900")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
