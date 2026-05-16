"""anyplot.ai
timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
Library: highcharts | Python 3.13
Quality: pending | Created: 2026-05-16
"""

import os
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

import httpx
import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaRangeSeries, LineSeries
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

# Okabe-Ito palette
BRAND = "#009E73"  # Position 1 — always first series
ACCENT = "#D55E00"  # Position 2

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
response = httpx.get(highcharts_url, timeout=30)
response.raise_for_status()
highcharts_js = response.text

# Download Highcharts More for arearange
highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
response_more = httpx.get(highcharts_more_url, timeout=30)
response_more.raise_for_status()
highcharts_more_js = response_more.text

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
    "style": {"fontSize": "28px", "fontWeight": "normal", "color": INK},
    "margin": 40,
}

# X-axis (datetime)
chart.options.x_axis = {
    "type": "datetime",
    "title": {"text": "Date", "style": {"fontSize": "22px", "color": INK}, "margin": 25},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "dateTimeLabelFormats": {"month": "%b %Y"},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
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
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
}

# Legend with larger symbols
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "symbolWidth": 60,
    "symbolHeight": 28,
    "symbolRadius": 3,
    "margin": 30,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "borderRadius": 4,
}

# Tooltip
chart.options.tooltip = {
    "shared": True,
    "style": {"fontSize": "18px", "color": INK},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "xDateFormat": "%B %Y",
    "valueDecimals": 1,
}

# Plot options for line width
chart.options.plot_options = {"line": {"lineWidth": 3, "marker": {"radius": 6}}, "arearange": {"lineWidth": 0}}

# 95% confidence band (lighter, behind 80%)
ci_95_series = AreaRangeSeries()
ci_95_series.name = "95% Confidence Interval"
ci_95_series.data = [
    {"x": forecast_timestamps[i], "low": float(lower_95[i]), "high": float(upper_95[i])} for i in range(n_forecast)
]
# Use a light tint of the accent color
ci_95_series.color = "#D55E00" if THEME == "light" else "#E8896B"
ci_95_series.fill_opacity = 0.15
ci_95_series.line_width = 0
ci_95_series.marker = {"enabled": False}
ci_95_series.z_index = 0

# 80% confidence band (darker)
ci_80_series = AreaRangeSeries()
ci_80_series.name = "80% Confidence Interval"
ci_80_series.data = [
    {"x": forecast_timestamps[i], "low": float(lower_80[i]), "high": float(upper_80[i])} for i in range(n_forecast)
]
# Use a more opaque version of the accent color
ci_80_series.color = "#D55E00"
ci_80_series.fill_opacity = 0.30
ci_80_series.line_width = 0
ci_80_series.marker = {"enabled": False}
ci_80_series.z_index = 1

# Historical data series (brand green - Okabe-Ito position 1)
historical_series = LineSeries()
historical_series.name = "Historical (Actual)"
historical_series.data = [
    {"x": historical_timestamps[i], "y": float(historical_values[i])} for i in range(n_historical)
]
historical_series.color = BRAND
historical_series.line_width = 3
historical_series.marker = {"enabled": True, "radius": 6, "symbol": "circle"}
historical_series.z_index = 3

# Forecast series (accent orange - Okabe-Ito position 2)
forecast_series = LineSeries()
forecast_series.name = "Forecast"
forecast_series.data = [{"x": forecast_timestamps[i], "y": float(forecast_values[i])} for i in range(n_forecast)]
forecast_series.color = ACCENT
forecast_series.line_width = 3
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
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML version with theme suffix
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
