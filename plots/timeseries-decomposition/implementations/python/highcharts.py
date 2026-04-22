""" pyplots.ai
timeseries-decomposition: Time Series Decomposition Plot
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import base64
import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from statsmodels.tsa.seasonal import seasonal_decompose


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

# Colors - colorblind-safe palette
primary_blue = "#306998"
secondary_yellow = "#FFD43B"
purple = "#9467BD"
teal = "#17BECF"

# Chart dimensions - single output image
chart_width = 4800
total_height = 2700
subplot_height = total_height // 4  # 675px each

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")


def create_chart_config(
    container_id, title_text, subtitle_text, y_title, data, color, series_name, is_first=False, is_last=False
):
    """Create a Highcharts chart configuration using highcharts-core."""
    chart = Chart(container=container_id)
    chart.options = HighchartsOptions()

    # Set options via highcharts-core
    chart.options.chart = {
        "type": "line",
        "width": chart_width,
        "height": subplot_height,
        "backgroundColor": "#ffffff",
        "marginLeft": 150,
        "marginRight": 100,
        "marginTop": 100 if is_first else 60,
        "marginBottom": 100 if is_last else 50,
    }

    if is_first:
        chart.options.title = {"text": title_text, "style": {"fontSize": "40px", "fontWeight": "bold"}}
        chart.options.subtitle = {"text": subtitle_text, "style": {"fontSize": "34px"}}
    else:
        chart.options.title = {"text": subtitle_text, "style": {"fontSize": "34px", "fontWeight": "bold"}}

    chart.options.x_axis = {
        "type": "datetime",
        "labels": {"style": {"fontSize": "20px"}, "format": "{value:%Y-%m}"},
        "title": {"text": "Date", "style": {"fontSize": "24px", "fontWeight": "bold"}} if is_last else {"text": None},
        "gridLineWidth": 1,
        "gridLineColor": "rgba(0,0,0,0.1)",
        "lineWidth": 2,
    }

    chart.options.y_axis = {
        "title": {"text": y_title, "style": {"fontSize": "24px", "fontWeight": "bold"}},
        "labels": {"style": {"fontSize": "20px"}},
        "gridLineWidth": 1,
        "gridLineColor": "rgba(0,0,0,0.15)",
        "lineWidth": 2,
    }

    # Enable minimal legend showing component name
    chart.options.legend = {
        "enabled": True,
        "align": "right",
        "verticalAlign": "top",
        "layout": "horizontal",
        "floating": True,
        "x": -50,
        "y": 15 if is_first else 5,
        "itemStyle": {"fontSize": "22px", "fontWeight": "normal"},
    }

    chart.options.credits = {"enabled": False}

    # Add series using highcharts-core LineSeries
    series = LineSeries()
    series.data = data
    series.name = series_name
    series.color = color
    series.line_width = 4
    series.marker = {"enabled": False}
    chart.add_series(series)

    # Return config dict for manual JS generation (more reliable for multi-chart)
    return {
        "container": container_id,
        "options": {
            "chart": {
                "type": "line",
                "width": chart_width,
                "height": subplot_height,
                "backgroundColor": "#ffffff",
                "marginLeft": 150,
                "marginRight": 100,
                "marginTop": 100 if is_first else 60,
                "marginBottom": 100 if is_last else 50,
            },
            "title": {"text": title_text, "style": {"fontSize": "40px", "fontWeight": "bold"}}
            if is_first
            else {"text": subtitle_text, "style": {"fontSize": "34px", "fontWeight": "bold"}},
            "subtitle": {"text": subtitle_text, "style": {"fontSize": "34px"}} if is_first else None,
            "xAxis": {
                "type": "datetime",
                "labels": {"style": {"fontSize": "20px"}, "format": "{value:%Y-%m}"},
                "title": {"text": "Date", "style": {"fontSize": "24px", "fontWeight": "bold"}}
                if is_last
                else {"text": None},
                "gridLineWidth": 1,
                "gridLineColor": "rgba(0,0,0,0.1)",
                "lineWidth": 2,
            },
            "yAxis": {
                "title": {"text": y_title, "style": {"fontSize": "24px", "fontWeight": "bold"}},
                "labels": {"style": {"fontSize": "20px"}},
                "gridLineWidth": 1,
                "gridLineColor": "rgba(0,0,0,0.15)",
                "lineWidth": 2,
            },
            "legend": {
                "enabled": True,
                "align": "right",
                "verticalAlign": "top",
                "layout": "horizontal",
                "floating": True,
                "x": -50,
                "y": 15 if is_first else 5,
                "itemStyle": {"fontSize": "22px", "fontWeight": "normal"},
            },
            "credits": {"enabled": False},
            "series": [
                {"name": series_name, "data": data, "color": color, "lineWidth": 4, "marker": {"enabled": False}}
            ],
        },
    }


# Create all four chart configurations using highcharts-core
chart_configs = [
    create_chart_config(
        "container1",
        "timeseries-decomposition · highcharts · pyplots.ai",
        "Original Series",
        "Passengers (thousands)",
        observed_data,
        primary_blue,
        "Original",
        is_first=True,
    ),
    create_chart_config(
        "container2", "", "Trend Component", "Trend (thousands)", trend_data, secondary_yellow, "Trend"
    ),
    create_chart_config(
        "container3", "", "Seasonal Component", "Seasonal Effect (thousands)", seasonal_data, purple, "Seasonal"
    ),
    create_chart_config(
        "container4", "", "Residual Component", "Residual (thousands)", residual_data, teal, "Residual", is_last=True
    ),
]

# Build HTML with all 4 charts stacked vertically
containers_html = "\n".join(
    [
        f'<div id="{cfg["container"]}" style="width: {chart_width}px; height: {subplot_height}px;"></div>'
        for cfg in chart_configs
    ]
)

# Build direct JavaScript calls (no DOMContentLoaded wrapper for headless)
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
        html, body {{ width: {chart_width}px; height: {total_height}px; background-color: #ffffff; overflow: hidden; }}
    </style>
</head>
<body>
    {containers_html}
    <script>
    {scripts_js}
    </script>
</body>
</html>"""

# Save and screenshot using CDP for full page capture
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
time.sleep(6)  # Wait for all charts to render

# Use CDP to capture full page screenshot at exact dimensions
screenshot_config = {
    "captureBeyondViewport": True,
    "clip": {"x": 0, "y": 0, "width": chart_width, "height": total_height, "scale": 1},
}
result = driver.execute_cdp_cmd("Page.captureScreenshot", screenshot_config)
screenshot_data = base64.b64decode(result["data"])

with open("plot.png", "wb") as f:
    f.write(screenshot_data)

driver.quit()
Path(temp_path).unlink()

# Also save interactive HTML
with open("plot.html", "w", encoding="utf-8") as f:
    html_portable = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background-color: #ffffff; }}
    </style>
</head>
<body>
    {containers_html}
    <script>
    {scripts_js}
    </script>
</body>
</html>"""
    f.write(html_portable)
