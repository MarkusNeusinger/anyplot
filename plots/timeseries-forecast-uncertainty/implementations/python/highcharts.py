""" anyplot.ai
timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
Library: highcharts unknown | Python 3.13.13
Quality: 81/100 | Updated: 2026-05-19
"""

import os
import tempfile
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaRangeSeries, LineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette: first series is always #009E73
BRAND = "#009E73"  # Historical data
FORECAST_COLOR = "#D55E00"  # Forecast (second color in palette)

# Data - Monthly product demand with forecast
np.random.seed(42)

# Historical data: 36 months (3 years)
n_historical = 36
n_forecast = 12

# Create dates
start_date = datetime(2022, 1, 1)
historical_dates = [start_date + timedelta(days=30 * i) for i in range(n_historical)]
forecast_dates = [historical_dates[-1] + timedelta(days=30 * (i + 1)) for i in range(n_forecast)]
all_dates = historical_dates + forecast_dates

# Generate historical data with trend and seasonality
trend = np.linspace(100, 150, n_historical)
seasonality = 20 * np.sin(np.linspace(0, 6 * np.pi, n_historical))
noise = np.random.normal(0, 8, n_historical)
historical_values = trend + seasonality + noise

# Generate forecast with increasing uncertainty
last_value = historical_values[-1]
forecast_trend = np.linspace(last_value, last_value + 20, n_forecast)
forecast_seasonality = 20 * np.sin(np.linspace(6 * np.pi, 8 * np.pi, n_forecast))
forecast_values = forecast_trend + forecast_seasonality

# Confidence intervals widen over time
time_factor = np.linspace(1, 3, n_forecast)
ci_80 = 10 * time_factor
ci_95 = 18 * time_factor

lower_80 = forecast_values - ci_80
upper_80 = forecast_values + ci_80
lower_95 = forecast_values - ci_95
upper_95 = forecast_values + ci_95

# Convert dates to timestamps (milliseconds for Highcharts)
historical_timestamps = [int(d.timestamp() * 1000) for d in historical_dates]
forecast_timestamps = [int(d.timestamp() * 1000) for d in forecast_dates]
forecast_start_ts = forecast_timestamps[0]

# Download Highcharts JS from CDN with fallbacks
cdn_urls = [
    "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.min.js",
    "https://unpkg.com/highcharts@11/highcharts.js",
    "https://code.highcharts.com/highcharts.js",
]

highcharts_js = None
for url in cdn_urls:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"})
    max_retries = 2
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                highcharts_js = response.read().decode("utf-8")
                break
        except (urllib.error.URLError, urllib.error.HTTPError):
            if attempt < max_retries - 1:
                time.sleep(1)
    if highcharts_js:
        break

if not highcharts_js:
    raise RuntimeError("Could not download Highcharts from any CDN")

# Download Highcharts More for arearange
cdn_more_urls = [
    "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts-more.min.js",
    "https://unpkg.com/highcharts@11/highcharts-more.js",
    "https://code.highcharts.com/highcharts-more.js",
]

highcharts_more_js = None
for url in cdn_more_urls:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"})
    max_retries = 2
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                highcharts_more_js = response.read().decode("utf-8")
                break
        except (urllib.error.URLError, urllib.error.HTTPError):
            if attempt < max_retries - 1:
                time.sleep(1)
    if highcharts_more_js:
        break

if not highcharts_more_js:
    raise RuntimeError("Could not download Highcharts More from any CDN")

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "spacingTop": 60,
    "spacingBottom": 120,
    "spacingLeft": 100,
    "spacingRight": 120,
}

# Title
chart.options.title = {
    "text": "timeseries-forecast-uncertainty · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "medium", "color": INK},
    "margin": 40,
}

# X-axis (datetime)
chart.options.x_axis = {
    "type": "datetime",
    "title": {"text": "Date", "style": {"fontSize": "22px", "color": INK}, "margin": 25},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "dateTimeLabelFormats": {"month": "%b %Y"},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "plotLines": [
        {
            "value": forecast_start_ts,
            "color": INK_SOFT,
            "width": 3,
            "dashStyle": "Dash",
            "label": {
                "text": "Forecast Start",
                "style": {"fontSize": "18px", "color": INK_SOFT, "fontWeight": "normal"},
                "rotation": 0,
                "y": -15,
            },
            "zIndex": 5,
        }
    ],
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Product Demand (Units)", "style": {"fontSize": "22px", "color": INK}, "margin": 25},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

# Legend with larger symbols
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "symbolWidth": 40,
    "symbolHeight": 24,
    "symbolRadius": 3,
    "margin": 30,
}

# Tooltip
chart.options.tooltip = {
    "shared": True,
    "style": {"fontSize": "16px", "color": INK},
    "xDateFormat": "%B %Y",
    "valueDecimals": 1,
}

# Plot options for line width
chart.options.plot_options = {"line": {"lineWidth": 4, "marker": {"radius": 6}}, "arearange": {"lineWidth": 0}}

# 95% confidence band (lighter blue-green, behind 80%)
ci_95_series = AreaRangeSeries()
ci_95_series.name = "95% Confidence Interval"
ci_95_series.data = [
    {"x": forecast_timestamps[i], "low": float(lower_95[i]), "high": float(upper_95[i])} for i in range(n_forecast)
]
ci_95_series.color = "#56B4E9" if THEME == "light" else "#87CEEB"
ci_95_series.fill_opacity = 0.15
ci_95_series.line_width = 0
ci_95_series.marker = {"enabled": False}
ci_95_series.z_index = 0

# 80% confidence band (darker blue-green, in front of 95%)
ci_80_series = AreaRangeSeries()
ci_80_series.name = "80% Confidence Interval"
ci_80_series.data = [
    {"x": forecast_timestamps[i], "low": float(lower_80[i]), "high": float(upper_80[i])} for i in range(n_forecast)
]
ci_80_series.color = "#0072B2"
ci_80_series.fill_opacity = 0.25
ci_80_series.line_width = 0
ci_80_series.marker = {"enabled": False}
ci_80_series.z_index = 1

# Historical data series (Okabe-Ito position 1: brand green)
historical_series = LineSeries()
historical_series.name = "Historical (Actual)"
historical_series.data = [
    {"x": historical_timestamps[i], "y": float(historical_values[i])} for i in range(n_historical)
]
historical_series.color = BRAND
historical_series.line_width = 4
historical_series.marker = {"enabled": True, "radius": 5, "symbol": "circle"}
historical_series.z_index = 3

# Forecast series (Okabe-Ito position 2: vermillion)
forecast_series = LineSeries()
forecast_series.name = "Forecast"
forecast_series.data = [{"x": forecast_timestamps[i], "y": float(forecast_values[i])} for i in range(n_forecast)]
forecast_series.color = FORECAST_COLOR
forecast_series.line_width = 4
forecast_series.dash_style = "Dash"
forecast_series.marker = {"enabled": True, "radius": 5, "symbol": "diamond"}
forecast_series.z_index = 4

# Add series in order (back to front)
chart.add_series(ci_95_series)
chart.add_series(ci_80_series)
chart.add_series(historical_series)
chart.add_series(forecast_series)

# Disable credits
chart.options.credits = {"enabled": False}

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

# Save HTML artifact with theme-suffixed filename
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot for PNG artifact
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
