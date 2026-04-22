""" pyplots.ai
line-timeseries-rolling: Time Series with Rolling Average Overlay
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Daily temperature readings with 7-day rolling average
np.random.seed(42)
n_days = 180

# Generate dates
dates = pd.date_range("2024-01-01", periods=n_days, freq="D")

# Generate temperature data with seasonal trend and noise
day_of_year = np.arange(n_days)
seasonal_trend = 15 + 12 * np.sin(2 * np.pi * (day_of_year - 30) / 365)  # Peak around day 180
daily_noise = np.random.normal(0, 3, n_days)
temperatures = seasonal_trend + daily_noise

# Calculate 7-day rolling average
df = pd.DataFrame({"date": dates, "temperature": temperatures})
df["rolling_avg"] = df["temperature"].rolling(window=7, center=True).mean()

# Prepare data for Highcharts (timestamps in milliseconds)
timestamps = [int(d.timestamp() * 1000) for d in df["date"]]
raw_data = [[ts, round(float(temp), 1)] for ts, temp in zip(timestamps, df["temperature"], strict=False)]
rolling_data = [
    [ts, round(float(avg), 1)] for ts, avg in zip(timestamps, df["rolling_avg"], strict=False) if pd.notna(avg)
]

# Build Highcharts options as dictionary
options = {
    "chart": {
        "type": "line",
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "style": {"fontFamily": "Arial, sans-serif"},
        "spacingBottom": 120,
        "spacingLeft": 50,
    },
    "title": {
        "text": "line-timeseries-rolling · highcharts · pyplots.ai",
        "style": {"fontSize": "56px", "fontWeight": "bold"},
    },
    "subtitle": {"text": "Daily Temperature with 7-Day Rolling Average", "style": {"fontSize": "40px"}},
    "xAxis": {
        "type": "datetime",
        "title": {"text": "Date", "style": {"fontSize": "40px"}},
        "labels": {"style": {"fontSize": "32px"}, "format": "{value:%b %d}", "rotation": -45, "align": "right"},
        "gridLineWidth": 1,
        "gridLineColor": "rgba(0, 0, 0, 0.1)",
        "tickInterval": 14 * 24 * 3600 * 1000,  # Every 2 weeks
    },
    "yAxis": {
        "title": {"text": "Temperature (°C)", "style": {"fontSize": "40px"}},
        "labels": {"style": {"fontSize": "32px"}},
        "gridLineWidth": 1,
        "gridLineColor": "rgba(0, 0, 0, 0.3)",
    },
    "legend": {
        "enabled": True,
        "itemStyle": {"fontSize": "36px"},
        "align": "right",
        "verticalAlign": "top",
        "layout": "vertical",
        "x": -80,
        "y": 120,
    },
    "plotOptions": {"line": {"lineWidth": 4, "marker": {"enabled": False}}, "series": {"animation": False}},
    "series": [
        {
            "name": "Raw Temperature",
            "data": raw_data,
            "color": "rgba(48, 105, 152, 0.5)",
            "lineWidth": 3,
            "marker": {"enabled": False},
        },
        {
            "name": "7-Day Rolling Average",
            "data": rolling_data,
            "color": "#FFD43B",
            "lineWidth": 6,
            "marker": {"enabled": False},
        },
    ],
    "credits": {"enabled": False},
}

# Download Highcharts JS for headless rendering
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts and proper Highcharts initialization
options_json = json.dumps(options)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        Highcharts.chart('container', {options_json});
    </script>
</body>
</html>"""

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2900")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render

# Get the chart container and take element screenshot for full chart capture
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file

# Also save HTML for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)
