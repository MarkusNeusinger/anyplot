""" pyplots.ai
timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
Library: highcharts unknown | Python 3.13.11
Quality: 93/100 | Created: 2026-01-07
"""

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

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Download Highcharts More for arearange
highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "spacingTop": 60,
    "spacingBottom": 120,
    "spacingLeft": 100,
    "spacingRight": 120,
}

# Title
chart.options.title = {
    "text": "timeseries-forecast-uncertainty \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "56px", "fontWeight": "bold"},
    "margin": 40,
}

chart.options.subtitle = {
    "text": "Monthly Product Demand with 80% and 95% Confidence Intervals",
    "style": {"fontSize": "36px", "color": "#666666"},
}

# X-axis (datetime)
chart.options.x_axis = {
    "type": "datetime",
    "title": {"text": "Date", "style": {"fontSize": "36px"}, "margin": 25},
    "labels": {"style": {"fontSize": "28px"}},
    "dateTimeLabelFormats": {"month": "%b %Y"},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
    "plotLines": [
        {
            "value": forecast_start_ts,
            "color": "#666666",
            "width": 4,
            "dashStyle": "Dash",
            "label": {
                "text": "Forecast Start",
                "style": {"fontSize": "28px", "color": "#555555", "fontWeight": "bold"},
                "rotation": 0,
                "y": -15,
            },
            "zIndex": 5,
        }
    ],
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Product Demand (Units)", "style": {"fontSize": "36px"}, "margin": 25},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "32px"},
    "symbolWidth": 50,
    "symbolHeight": 24,
    "margin": 30,
}

# Tooltip
chart.options.tooltip = {"shared": True, "style": {"fontSize": "28px"}, "xDateFormat": "%B %Y", "valueDecimals": 1}

# Plot options for line width
chart.options.plot_options = {"line": {"lineWidth": 5, "marker": {"radius": 8}}, "arearange": {"lineWidth": 0}}

# 95% confidence band (lighter, behind 80%)
ci_95_series = AreaRangeSeries()
ci_95_series.name = "95% Confidence Interval"
ci_95_series.data = [
    {"x": forecast_timestamps[i], "low": float(lower_95[i]), "high": float(upper_95[i])} for i in range(n_forecast)
]
ci_95_series.color = "rgba(255, 212, 59, 0.25)"
ci_95_series.fill_opacity = 0.25
ci_95_series.line_width = 0
ci_95_series.marker = {"enabled": False}
ci_95_series.z_index = 0

# 80% confidence band (darker)
ci_80_series = AreaRangeSeries()
ci_80_series.name = "80% Confidence Interval"
ci_80_series.data = [
    {"x": forecast_timestamps[i], "low": float(lower_80[i]), "high": float(upper_80[i])} for i in range(n_forecast)
]
ci_80_series.color = "rgba(255, 212, 59, 0.45)"
ci_80_series.fill_opacity = 0.45
ci_80_series.line_width = 0
ci_80_series.marker = {"enabled": False}
ci_80_series.z_index = 1

# Historical data series
historical_series = LineSeries()
historical_series.name = "Historical (Actual)"
historical_series.data = [
    {"x": historical_timestamps[i], "y": float(historical_values[i])} for i in range(n_historical)
]
historical_series.color = "#306998"
historical_series.line_width = 4
historical_series.marker = {"enabled": True, "radius": 6, "symbol": "circle"}
historical_series.z_index = 3

# Forecast series
forecast_series = LineSeries()
forecast_series.name = "Forecast"
forecast_series.data = [{"x": forecast_timestamps[i], "y": float(forecast_values[i])} for i in range(n_forecast)]
forecast_series.color = "#E67E22"
forecast_series.line_width = 4
forecast_series.dash_style = "Dash"
forecast_series.marker = {"enabled": True, "radius": 6, "symbol": "diamond"}
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
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML version for interactive viewing (uses CDN for portability)
cdn_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/highcharts-more.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 600px;"></div>
    <script>{html_str}</script>
</body>
</html>"""
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(cdn_html)

# Take screenshot with Selenium
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=5000,3000")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

# Screenshot the chart container element for exact dimensions
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
