""" anyplot.ai
timeseries-decomposition: Time Series Decomposition Plot
Library: highcharts unknown | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-14
"""

import base64
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
from statsmodels.tsa.seasonal import seasonal_decompose


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette for decomposition components
COLORS = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]
COMPONENT_NAMES = ["Original", "Trend", "Seasonal", "Residual"]

# Data - Monthly airline passengers (classic time series dataset)
np.random.seed(42)
dates = pd.date_range(start="2018-01-01", periods=120, freq="MS")  # 10 years monthly

# Generate realistic airline passenger data with trend, seasonality, and noise
trend = np.linspace(100, 300, 120)  # Upward trend over time
seasonal = 40 * np.sin(2 * np.pi * np.arange(120) / 12)  # Annual seasonality
noise = np.random.normal(0, 15, 120)  # Random noise
passengers = trend + seasonal + noise

# Create time series and decompose
ts = pd.Series(passengers, index=dates)
decomposition = seasonal_decompose(ts, model="additive", period=12)

# Extract components
observed = decomposition.observed
trend_comp = decomposition.trend
seasonal_comp = decomposition.seasonal
residual = decomposition.resid

# Convert to lists for Highcharts (handle NaN values in trend/residual)
timestamps = [int(d.timestamp() * 1000) for d in dates]
observed_data = [[t, float(v)] for t, v in zip(timestamps, observed, strict=True)]
trend_data = [[t, float(v) if not np.isnan(v) else None] for t, v in zip(timestamps, trend_comp, strict=True)]
seasonal_data = [[t, float(v)] for t, v in zip(timestamps, seasonal_comp, strict=True)]
residual_data = [[t, float(v) if not np.isnan(v) else None] for t, v in zip(timestamps, residual, strict=True)]

# Chart dimensions
chart_width = 4800
total_height = 2700
subplot_height = total_height // 4

# Download Highcharts JS
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Build chart configurations for each component
component_data = [
    (observed_data, "Passengers (thousands)"),
    (trend_data, "Trend (thousands)"),
    (seasonal_data, "Seasonal Effect (thousands)"),
    (residual_data, "Residual (thousands)"),
]

chart_configs = []
for i, (data, y_label) in enumerate(component_data):
    is_first = i == 0
    is_last = i == 3

    config = {
        "container": f"container{i + 1}",
        "options": {
            "chart": {
                "type": "line",
                "width": chart_width,
                "height": subplot_height,
                "backgroundColor": PAGE_BG,
                "marginLeft": 160,
                "marginRight": 120,
                "marginTop": 120 if is_first else 80,
                "marginBottom": 120 if is_last else 80,
            },
            "title": {
                "text": "timeseries-decomposition · highcharts · anyplot.ai" if is_first else COMPONENT_NAMES[i],
                "style": {"fontSize": "28px", "color": INK, "fontWeight": "normal"},
            },
            "subtitle": {"text": COMPONENT_NAMES[i], "style": {"fontSize": "24px", "color": INK_SOFT}}
            if is_first
            else {"text": None},
            "xAxis": {
                "type": "datetime",
                "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}, "format": "{value:%Y-%m}"},
                "title": {"text": "Date" if is_last else None, "style": {"fontSize": "22px", "color": INK}},
                "gridLineWidth": 1,
                "gridLineColor": GRID,
                "lineColor": INK_SOFT,
                "tickColor": INK_SOFT,
            },
            "yAxis": {
                "title": {"text": y_label, "style": {"fontSize": "22px", "color": INK}},
                "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
                "gridLineWidth": 1,
                "gridLineColor": GRID,
                "lineColor": INK_SOFT,
                "tickColor": INK_SOFT,
            },
            "legend": {
                "enabled": True,
                "align": "right",
                "verticalAlign": "top",
                "layout": "vertical",
                "floating": True,
                "x": -30,
                "y": 20,
                "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
                "backgroundColor": ELEVATED_BG,
                "borderColor": INK_SOFT,
                "borderWidth": 1,
                "borderRadius": 4,
                "padding": 12,
            },
            "credits": {"enabled": False},
            "series": [
                {
                    "name": COMPONENT_NAMES[i],
                    "data": data,
                    "color": COLORS[i],
                    "lineWidth": 5,
                    "marker": {"enabled": False},
                }
            ],
        },
    }
    chart_configs.append(config)

# Build HTML with all 4 charts stacked vertically
containers_html = "\n".join(
    [
        f'<div id="{cfg["container"]}" style="width: {chart_width}px; height: {subplot_height}px;"></div>'
        for cfg in chart_configs
    ]
)

# Build JavaScript calls
scripts_js = "\n".join(
    [f"Highcharts.chart('{cfg['container']}', {json.dumps(cfg['options'])});" for cfg in chart_configs]
)

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html, body {{ width: {chart_width}px; height: {total_height}px; background-color: {PAGE_BG}; overflow: hidden; }}
    </style>
</head>
<body>
    {containers_html}
    <script>
    {scripts_js}
    </script>
</body>
</html>"""

# Save and screenshot using Selenium
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(6)

# Capture screenshot at exact dimensions
screenshot_config = {
    "captureBeyondViewport": True,
    "clip": {"x": 0, "y": 0, "width": chart_width, "height": total_height, "scale": 1},
}
result = driver.execute_cdp_cmd("Page.captureScreenshot", screenshot_config)
screenshot_data = base64.b64decode(result["data"])

with open(f"plot-{THEME}.png", "wb") as f:
    f.write(screenshot_data)

driver.quit()
Path(temp_path).unlink()

# Save interactive HTML with CDN script (for web viewing)
html_portable = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background-color: {PAGE_BG}; }}
    </style>
</head>
<body>
    {containers_html}
    <script>
    {scripts_js}
    </script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_portable)
