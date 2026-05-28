""" anyplot.ai
area-basic: Basic Area Chart
Library: highcharts unknown | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-28
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaSeries
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
BRAND = "#009E73"  # anyplot palette position 1 — ALWAYS first series

# Data - Daily website visitors over a month
np.random.seed(42)
days = np.arange(1, 31)
base_traffic = 2000 + days * 50  # Growth trend
weekly_pattern = 300 * np.sin(2 * np.pi * days / 7)  # Weekly cycle
noise = np.random.normal(0, 200, len(days))
visitors = base_traffic + weekly_pattern + noise
visitors = np.clip(visitors, 500, None).astype(int)

peak_day = int(days[np.argmax(visitors)])
peak_visitors = int(np.max(visitors))

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "area",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "marginBottom": 160,
    "marginLeft": 180,
    "marginRight": 100,
    "marginTop": 120,
    "plotBorderWidth": 0,
}

# Title
title = "area-basic · python · highcharts · anyplot.ai"
chart.options.title = {"text": title, "style": {"fontSize": "66px", "color": INK, "fontWeight": "bold"}}

chart.options.subtitle = {
    "text": "Daily Website Visitors Over One Month — Weekend Dips with Steady Growth",
    "style": {"fontSize": "34px", "color": INK_SOFT},
}

# Weekend plotBands with theme-aware tint
band_color = "rgba(0,158,115,0.06)" if THEME == "light" else "rgba(0,158,115,0.22)"
weekend_bands = []
for d in range(1, 31):
    weekday = (d - 1) % 7  # 0=Mon, 5=Sat, 6=Sun
    if weekday in (5, 6):
        weekend_bands.append({"from": d - 0.5, "to": d + 0.5, "color": band_color})

chart.options.x_axis = {
    "title": {"text": "Day of Month", "style": {"fontSize": "56px", "color": INK}, "margin": 20},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineWidth": 0,
    "tickInterval": 5,
    "plotBands": weekend_bands,
}

chart.options.y_axis = {
    "title": {"text": "Daily Visitors", "style": {"fontSize": "56px", "color": INK}},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "min": 1500,
    "max": peak_visitors + 150,
    "startOnTick": False,
    "endOnTick": False,
    "plotLines": [
        {
            "value": peak_visitors,
            "color": "#AE3030",
            "width": 2,
            "dashStyle": "Dot",
            "label": {
                "text": f"▲ Peak: {peak_visitors:,} visitors (Day {peak_day})",
                "align": "left",
                "x": 10,
                "y": -10,
                "style": {"fontSize": "32px", "color": "#AE3030", "fontWeight": "bold"},
            },
            "zIndex": 5,
        }
    ],
}

# Fill gradient using brand color
fill_start = "rgba(0,158,115,0.45)" if THEME == "light" else "rgba(0,158,115,0.35)"
fill_end = "rgba(0,158,115,0.02)"

chart.options.plot_options = {
    "area": {
        "fillColor": {
            "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
            "stops": [[0, fill_start], [1, fill_end]],
        },
        "lineWidth": 3,
        "marker": {"enabled": True, "radius": 9, "fillColor": BRAND, "lineWidth": 2, "lineColor": PAGE_BG},
        "color": BRAND,
    }
}

chart.options.legend = {"enabled": False}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "style": {"fontSize": "30px", "color": INK},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderRadius": 8,
    "headerFormat": "<b>Day {point.x}</b><br/>",
    "pointFormat": "Visitors: {point.y:,.0f}",
}

# Add series
series = AreaSeries()
series.data = [[int(d), int(v)] for d, v in zip(days, visitors, strict=True)]
series.name = "Website Visitors"
chart.add_series(series)

# Download Highcharts JS for inline embedding
_req = urllib.request.Request(
    "https://code.highcharts.com/highcharts.js",
    headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.highcharts.com/"},
)
with urllib.request.urlopen(_req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
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

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and screenshot for PNG
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

# PIL safety net — pin to exact 3200×1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
