"""anyplot.ai
bubble-basic: Basic Bubble Chart
Library: highcharts 1.10.3 | Python 3.14.3
Quality: 91/100 | Updated: 2026-05-28
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bubble import BubbleSeries
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

# anyplot categorical palette positions 1–5
ANYPLOT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]
# Semi-transparent fills for bubble areas (alpha 0.65)
PALETTE_RGBA = [
    "rgba(0,158,115,0.65)",
    "rgba(196,117,253,0.65)",
    "rgba(68,103,163,0.65)",
    "rgba(189,130,51,0.65)",
    "rgba(174,48,48,0.65)",
]

# Data - Tech companies by sector (Revenue vs Growth Rate, Market Cap as bubble size)
np.random.seed(42)

sector_names = ["Cloud & SaaS", "E-Commerce", "Semiconductors", "Social & Media", "Fintech"]
revenues = [
    [12, 38, 68, 125, 200, 330, 500],
    [25, 75, 155, 270, 420, 600],
    [5, 45, 95, 170, 300, 460],
    [8, 52, 110, 185, 245, 390, 550],
    [15, 82, 140, 220],
]
growth_base = [
    [48, 35, 42, 28, 22, 15, 10],
    [40, 30, 18, 14, 12, 6],
    [52, 33, 25, 20, 16, 8],
    [55, 38, 30, 22, 18, 12, 7],
    [45, 28, 20, 15],
]

# Build series with realistic variation
all_series = []
for i, sector_name in enumerate(sector_names):
    n = len(revenues[i])
    rev = np.array(revenues[i], dtype=float) + np.random.uniform(-3, 3, n)
    grw = np.array(growth_base[i], dtype=float) + np.random.uniform(-2, 2, n)
    cap = rev * (1 + grw / 100) * np.random.uniform(2.5, 7, n)

    data = [
        {"x": round(float(rev[j]), 1), "y": round(float(grw[j]), 1), "z": round(float(cap[j]), 1)} for j in range(n)
    ]

    s = BubbleSeries()
    s.name = sector_name
    s.data = data
    s.color = PALETTE_RGBA[i]
    s.marker = {"lineWidth": 2, "lineColor": ANYPLOT_PALETTE[i]}
    all_series.append(s)

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "bubble",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "spacing": [30, 40, 40, 40],
    "style": {"fontFamily": "'Segoe UI', Arial, sans-serif", "color": INK},
}

chart.options.title = {
    "text": "bubble-basic · python · highcharts · anyplot.ai",
    "style": {"fontSize": "66px", "fontWeight": "bold", "color": INK},
}

chart.options.subtitle = {
    "text": "Bubble size represents Market Capitalization — Tech companies by sector",
    "style": {"fontSize": "44px", "color": INK_SOFT},
}

chart.options.x_axis = {
    "title": {"text": "Revenue (Billion USD)", "style": {"fontSize": "56px", "color": INK}, "margin": 20},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "gridLineDashStyle": "Dot",
    "lineColor": INK_SOFT,
    "lineWidth": 1,
    "tickColor": INK_SOFT,
    "min": 0,
    "tickInterval": 100,
}

chart.options.y_axis = {
    "title": {"text": "Growth Rate (%)", "style": {"fontSize": "56px", "color": INK}, "margin": 20},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "gridLineDashStyle": "Dot",
    "lineColor": INK_SOFT,
    "lineWidth": 1,
    "min": 0,
    "tickInterval": 10,
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -20,
    "y": 80,
    "floating": True,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "borderRadius": 8,
    "padding": 16,
    "itemStyle": {"fontSize": "44px", "fontWeight": "normal", "color": INK_SOFT},
    "itemMarginBottom": 8,
    "symbolRadius": 6,
    "bubbleLegend": {
        "enabled": True,
        "borderColor": INK_SOFT,
        "borderWidth": 2,
        "color": ELEVATED_BG,
        "connectorColor": INK_SOFT,
        "connectorWidth": 2,
        "labels": {"style": {"fontSize": "36px", "color": INK_SOFT}, "format": "{value:.0f}B"},
        "minSize": 14,
        "maxSize": 50,
    },
}

chart.options.tooltip = {
    "useHTML": True,
    "headerFormat": '<span style="font-size: 28px; font-weight: bold; color: {series.color}">{series.name}</span><br/>',
    "pointFormat": (
        '<span style="font-size: 24px">'
        "Revenue: <b>${point.x:.1f}B</b><br/>"
        "Growth: <b>{point.y:.1f}%</b><br/>"
        "Market Cap: <b>${point.z:.0f}B</b>"
        "</span>"
    ),
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderRadius": 8,
    "style": {"color": INK},
    "shadow": {"color": "rgba(0,0,0,0.12)", "offsetX": 2, "offsetY": 2, "width": 4},
}

chart.options.plot_options = {
    "bubble": {"minSize": 20, "maxSize": 120, "sizeBy": "area", "dataLabels": {"enabled": False}, "zMin": 0}
}

for s in all_series:
    chart.add_series(s)

# Download Highcharts JS files (inline required for headless Chrome file:// URLs)
req = urllib.request.Request(
    "https://code.highcharts.com/highcharts.js",
    headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.highcharts.com/"},
)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

req_more = urllib.request.Request(
    "https://code.highcharts.com/highcharts-more.js",
    headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.highcharts.com/"},
)
with urllib.request.urlopen(req_more, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Build HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
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
# CDP override makes viewport authoritative — --window-size alone loses ~139px to Chrome chrome
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin to exact canvas dims — absorbs any ±1–2 px rounding from the CDP override
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
