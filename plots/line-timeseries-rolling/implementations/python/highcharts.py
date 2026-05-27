""" anyplot.ai
line-timeseries-rolling: Time Series with Rolling Average Overlay
Library: highcharts unknown | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-13
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme setup
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
BRAND = "#009E73"  # Position 1
ACCENT = "#C475FD"  # Position 2
BRAND_SEMI = "rgba(0, 158, 115, 0.5)"

# Data - Daily temperature readings with 7-day rolling average
np.random.seed(42)
n_days = 180

# Generate dates
dates = pd.date_range("2024-01-01", periods=n_days, freq="D")

# Generate temperature data with seasonal trend and noise
day_of_year = np.arange(n_days)
seasonal_trend = 15 + 12 * np.sin(2 * np.pi * (day_of_year - 30) / 365)
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
        "backgroundColor": PAGE_BG,
        "style": {"fontFamily": "Arial, sans-serif", "color": INK},
        "spacingBottom": 120,
        "spacingLeft": 50,
    },
    "title": {
        "text": "Time Series with 7-Day Rolling Average",
        "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK},
    },
    "subtitle": {"text": "Daily Temperature with Rolling Average", "style": {"fontSize": "20px", "color": INK_SOFT}},
    "xAxis": {
        "type": "datetime",
        "title": {"text": "Date", "style": {"fontSize": "22px", "color": INK}},
        "labels": {
            "style": {"fontSize": "18px", "color": INK_SOFT},
            "format": "{value:%b %d}",
            "rotation": 315,
            "align": "right",
        },
        "gridLineWidth": 1,
        "gridLineColor": GRID,
        "tickInterval": 14 * 24 * 3600 * 1000,
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
    },
    "yAxis": {
        "title": {"text": "Temperature (°C)", "style": {"fontSize": "22px", "color": INK}},
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
        "gridLineWidth": 1,
        "gridLineColor": GRID,
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
    },
    "legend": {
        "enabled": True,
        "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
        "align": "right",
        "verticalAlign": "top",
        "layout": "vertical",
        "backgroundColor": ELEVATED_BG,
        "borderColor": INK_SOFT,
        "borderWidth": 1,
        "x": -50,
        "y": 80,
    },
    "plotOptions": {"line": {"lineWidth": 3, "marker": {"enabled": False}}, "series": {"animation": False}},
    "series": [
        {
            "name": "Raw Temperature",
            "data": raw_data,
            "color": BRAND_SEMI,
            "lineWidth": 3,
            "marker": {"enabled": False},
        },
        {
            "name": "7-Day Rolling Average",
            "data": rolling_data,
            "color": ACCENT,
            "lineWidth": 5,
            "marker": {"enabled": False},
        },
    ],
    "credits": {"enabled": False},
}

# Download Highcharts JS for headless rendering
highcharts_url = "https://code.highcharts.com/highcharts.js"
try:
    with urllib.request.urlopen(highcharts_url, timeout=60) as response:
        highcharts_js = response.read().decode("utf-8")
except Exception as e:
    # Fallback: use CDN with different host
    time.sleep(2)
    try:
        highcharts_url_alt = "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.4.3/highcharts.min.js"
        with urllib.request.urlopen(highcharts_url_alt, timeout=60) as response:
            highcharts_js = response.read().decode("utf-8")
    except Exception as e2:
        raise RuntimeError(f"Failed to download Highcharts from both URLs: {e}") from e2

# Generate HTML with inline scripts and proper Highcharts initialization
options_json = json.dumps(options)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        Highcharts.chart('container', {options_json});
    </script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot
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
