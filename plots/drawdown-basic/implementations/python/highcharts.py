""" anyplot.ai
drawdown-basic: Drawdown Chart
Library: highcharts unknown | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-23
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Drawdown uses red — semantic exception (loss/down) → anyplot palette position 3
DRAWDOWN_COLOR = "#B71D27"

# Data — simulated portfolio (geometric Brownian motion)
np.random.seed(42)
n_days = 500
dates = pd.date_range("2022-01-01", periods=n_days, freq="B")

returns = np.random.normal(0.0003, 0.015, n_days)
prices = 100 * np.cumprod(1 + returns)

# Calculate drawdown
running_max = np.maximum.accumulate(prices)
drawdown = (prices - running_max) / running_max * 100

# Find maximum drawdown
max_dd_idx = np.argmin(drawdown)
max_dd_value = drawdown[max_dd_idx]
max_dd_date = dates[max_dd_idx]
max_dd_timestamp = int(max_dd_date.timestamp() * 1000)

# Find recovery point after maximum drawdown
recovery_indices = np.where(drawdown[max_dd_idx:] == 0)[0]
if len(recovery_indices) > 0:
    recovery_idx = max_dd_idx + recovery_indices[0]
    recovery_date = dates[recovery_idx]
    recovery_days = (recovery_date - max_dd_date).days
else:
    recovery_days = None

# Prepare Highcharts data (timestamp in ms, value)
data_points = [[int(d.timestamp() * 1000), round(float(dd), 2)] for d, dd in zip(dates, drawdown, strict=True)]

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "area",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "style": {"color": INK},
    "spacingTop": 60,
    "spacingBottom": 100,
    "spacingLeft": 80,
    "spacingRight": 80,
}

max_dd_str = f"Max Drawdown: {max_dd_value:.1f}%"
stats_str = f"{max_dd_str} | Recovery: {recovery_days} days" if recovery_days else f"{max_dd_str} | Not Recovered"

chart.options.title = {
    "text": "drawdown-basic · python · highcharts · anyplot.ai",
    "style": {"fontSize": "66px", "fontWeight": "bold", "color": INK},
    "margin": 40,
}

chart.options.subtitle = {"text": stats_str, "style": {"fontSize": "44px", "color": INK_SOFT}}

chart.options.x_axis = {
    "type": "datetime",
    "title": {"text": "Date", "style": {"fontSize": "56px", "color": INK}, "margin": 25},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "tickInterval": 90 * 24 * 3600 * 1000,
    "dateTimeLabelFormats": {"month": "%b %Y"},
    "plotLines": [
        {
            "value": max_dd_timestamp,
            "color": DRAWDOWN_COLOR,
            "dashStyle": "ShortDash",
            "width": 3,
            "zIndex": 5,
            "label": {
                "text": f"Max DD: {max_dd_value:.1f}%",
                "style": {"fontSize": "40px", "color": DRAWDOWN_COLOR, "fontWeight": "bold"},
                "rotation": 0,
                "y": 220,
            },
        }
    ],
}

chart.options.y_axis = {
    "title": {"text": "Drawdown (%)", "style": {"fontSize": "56px", "color": INK}, "margin": 25},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}, "format": "{value}%"},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "max": 5,
    "plotLines": [
        {
            "value": 0,
            "color": INK_SOFT,
            "width": 3,
            "zIndex": 5,
            "label": {
                "text": "Peak (0%)",
                "style": {"fontSize": "40px", "color": INK_SOFT, "fontWeight": "bold"},
                "align": "right",
                "x": -10,
            },
        }
    ],
}

chart.options.legend = {
    "enabled": True,
    "itemStyle": {"color": INK_SOFT, "fontSize": "44px"},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "margin": 30,
}

chart.options.tooltip = {
    "xDateFormat": "%A, %b %d, %Y",
    "valueSuffix": "%",
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "style": {"color": INK, "fontSize": "40px"},
}

chart.options.plot_options = {"area": {"lineWidth": 4, "marker": {"enabled": False}, "threshold": 0}}

chart.options.credits = {"enabled": False}

chart.options.series = [
    {
        "name": "Drawdown",
        "type": "area",
        "data": data_points,
        "color": DRAWDOWN_COLOR,
        "fillColor": {
            "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
            "stops": [[0, "rgba(183, 29, 39, 0.05)"], [1, "rgba(183, 29, 39, 0.55)"]],
        },
        "lineColor": DRAWDOWN_COLOR,
        "lineWidth": 4,
        "threshold": 0,
    }
]

# Export
highcharts_url = "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.4.8/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{html_str}</script>
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

# PIL safety net: pin to exact 3200×1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
