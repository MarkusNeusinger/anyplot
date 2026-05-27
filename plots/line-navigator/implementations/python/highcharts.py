""" anyplot.ai
line-navigator: Line Chart with Mini Navigator
Library: highcharts unknown | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-27
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
BRAND = "#009E73"

# Data — 3 years of daily sensor readings with trend, seasonality, and noise
np.random.seed(42)
n_points = 1100
dates = pd.date_range(start="2022-01-01", periods=n_points, freq="D")
trend = np.linspace(50, 80, n_points)
seasonality = 15 * np.sin(np.linspace(0, 6 * np.pi, n_points))
noise = np.random.randn(n_points) * 5
values = trend + seasonality + noise
timestamps = [int(d.timestamp() * 1000) for d in dates]
series_data = [[t, round(float(v), 2)] for t, v in zip(timestamps, values, strict=True)]

# Build chart using highcharts_core OOP API
chart = Chart(container="container")
chart.options = HighchartsOptions()

title_text = "line-navigator · python · highcharts · anyplot.ai"

chart.options.chart = {
    "type": "line",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "marginBottom": 220,
    "marginLeft": 210,
    "marginRight": 80,
    "marginTop": 160,
    "style": {"fontFamily": "Arial, sans-serif", "color": INK},
}
chart.options.title = {"text": title_text, "style": {"fontSize": "66px", "fontWeight": "bold", "color": INK}, "y": 60}
chart.options.subtitle = {
    "text": "Daily Sensor Readings · 2022–2025",
    "style": {"fontSize": "36px", "color": INK_SOFT},
    "y": 120,
}
chart.options.x_axis = {
    "type": "datetime",
    "title": {"text": "Date", "style": {"fontSize": "56px", "color": INK}, "margin": 25},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}, "format": "{value:%b %Y}", "step": 2, "y": 40},
    "gridLineColor": GRID,
    "gridLineWidth": 1,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "tickLength": 8,
}
chart.options.y_axis = {
    "title": {"text": "Sensor Value (units)", "style": {"fontSize": "56px", "color": INK}, "margin": 25},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}, "format": "{value:.0f}", "x": -15},
    "gridLineColor": GRID,
    "gridLineWidth": 1,
    "lineColor": INK_SOFT,
    "opposite": False,
}
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "44px", "color": INK_SOFT, "fontWeight": "normal"},
    "verticalAlign": "top",
    "y": 80,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}
chart.options.tooltip = {
    "shared": True,
    "valueDecimals": 2,
    "headerFormat": '<span style="font-size:26px">{point.key:%b %d, %Y}</span><br/>',
    "pointFormat": (
        '<span style="font-size:24px;color:{series.color}">&#9679;</span> '
        '<span style="font-size:24px">{series.name}: <b>{point.y:.2f}</b></span><br/>'
    ),
    "style": {"fontSize": "24px"},
}
chart.options.credits = {"enabled": False}

# Series via LineSeries class
line = LineSeries()
line.name = "Sensor Reading"
line.data = series_data
line.color = BRAND
line.line_width = 2.5
line.marker = {"enabled": False}
chart.add_series(line)

# Extract core options dict from highcharts_core
core_options = chart.options.to_dict()

# Stock-specific extensions (navigator, rangeSelector, scrollbar) are not in
# highcharts_core, so they are merged in as raw dicts before serialisation.
stock_extensions = {
    "rangeSelector": {
        "enabled": True,
        "selected": 3,
        "inputEnabled": True,
        "inputStyle": {"fontSize": "24px", "color": INK},
        "inputBoxBorderColor": INK_SOFT,
        "inputBoxWidth": 140,
        "inputBoxHeight": 30,
        "labelStyle": {"fontSize": "24px", "color": INK_SOFT},
        "buttons": [
            {"type": "month", "count": 1, "text": "1M"},
            {"type": "month", "count": 3, "text": "3M"},
            {"type": "month", "count": 6, "text": "6M"},
            {"type": "year", "count": 1, "text": "1Y"},
            {"type": "ytd", "text": "YTD"},
            {"type": "all", "text": "All"},
        ],
        "buttonTheme": {
            "width": 80,
            "height": 36,
            "style": {"fontSize": "24px", "color": INK},
            "states": {"select": {"fill": BRAND, "style": {"color": PAGE_BG}}, "hover": {"fill": ELEVATED_BG}},
        },
        "floating": False,
        "y": 0,
        "height": 50,
    },
    "navigator": {
        "enabled": True,
        "height": 120,
        "margin": 30,
        "series": {"color": BRAND, "lineWidth": 2},
        "xAxis": {"labels": {"style": {"fontSize": "20px", "color": INK_SOFT}}},
        "handles": {"width": 20, "height": 30, "backgroundColor": BRAND, "borderColor": INK},
        "maskFill": "rgba(0,158,115,0.15)",
        "outlineWidth": 1,
        "outlineColor": INK_SOFT,
    },
    "scrollbar": {
        "enabled": True,
        "height": 20,
        "barBackgroundColor": BRAND,
        "barBorderRadius": 5,
        "barBorderWidth": 0,
        "buttonBackgroundColor": ELEVATED_BG,
        "buttonBorderWidth": 0,
        "rifleColor": PAGE_BG,
        "trackBackgroundColor": ELEVATED_BG,
        "trackBorderWidth": 1,
        "trackBorderColor": INK_SOFT,
    },
}

full_options = {**core_options, **stock_extensions}
chart_options_json = json.dumps(full_options)

# Download Highstock JS (required for navigator + rangeSelector)
highstock_url = "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.4.8/highstock.js"
with urllib.request.urlopen(highstock_url, timeout=30) as response:
    highstock_js = response.read().decode("utf-8")

range_selector_css = f"""
    .highcharts-range-selector-buttons .highcharts-button rect {{
        fill: {ELEVATED_BG} !important;
        stroke: {INK_SOFT} !important;
    }}
    .highcharts-range-selector-buttons .highcharts-button text {{
        fill: {INK} !important;
    }}
    .highcharts-range-selector-buttons .highcharts-button-pressed rect {{
        fill: {BRAND} !important;
    }}
    .highcharts-range-selector-buttons .highcharts-button-pressed text {{
        fill: {PAGE_BG} !important;
    }}
    .highcharts-range-input {{
        background: {ELEVATED_BG} !important;
        color: {INK} !important;
        border-color: {INK_SOFT} !important;
    }}
"""

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highstock_js}</script>
    <style>{range_selector_css}</style>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            Highcharts.stockChart('container', {chart_options_json});
        }});
    </script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=3200,1800")

driver = webdriver.Chrome(options=chrome_options)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin to exact canvas dimensions (belt-and-braces against ±1–2 px rounding)
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
