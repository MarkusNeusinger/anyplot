""" anyplot.ai
bubble-basic: Basic Bubble Chart
Library: highcharts unknown | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-28
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
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
PALETTE_RGBA = [
    "rgba(0,158,115,0.65)",
    "rgba(196,117,253,0.65)",
    "rgba(68,103,163,0.65)",
    "rgba(189,130,51,0.65)",
    "rgba(174,48,48,0.65)",
]

# Data — 50 tech companies by sector (Revenue vs Growth Rate, Market Cap as bubble size)
np.random.seed(42)

sector_names = ["Cloud & SaaS", "E-Commerce", "Semiconductors", "Social & Media", "Fintech"]
# Base revenues: 10 companies per sector spanning startups to mega-caps
revenues_base = [
    [8, 18, 35, 58, 85, 130, 195, 280, 380, 500],
    [15, 40, 80, 140, 230, 340, 460, 560, 600, 650],
    [5, 20, 50, 100, 165, 240, 340, 440, 540, 620],
    [6, 25, 60, 110, 175, 240, 310, 400, 510, 610],
    [10, 35, 70, 120, 190, 280, 370, 460, 540, 590],
]
# Growth rates: high for small companies, declining with scale (inverse relationship)
growth_base = [
    [54, 46, 40, 34, 28, 22, 17, 13, 10, 7],
    [44, 35, 27, 20, 15, 11, 9, 7, 6, 4],
    [58, 44, 35, 27, 20, 15, 12, 9, 7, 5],
    [60, 50, 38, 30, 23, 17, 13, 10, 8, 5],
    [48, 38, 30, 22, 16, 11, 9, 7, 6, 5],
]

all_series = []
all_rev_flat = []
all_grw_flat = []

for i, sector_name in enumerate(sector_names):
    n = len(revenues_base[i])
    rev = np.array(revenues_base[i], dtype=float) + np.random.uniform(-3, 3, n)
    grw = np.array(growth_base[i], dtype=float) + np.random.uniform(-2, 2, n)
    cap = rev * (1 + grw / 100) * np.random.uniform(2.5, 7, n)

    all_rev_flat.extend(revenues_base[i])
    all_grw_flat.extend(growth_base[i])

    data = [
        {"x": round(float(rev[j]), 1), "y": round(float(grw[j]), 1), "z": round(float(cap[j]), 1)} for j in range(n)
    ]

    s = BubbleSeries()
    s.name = sector_name
    s.data = data
    s.color = PALETTE_RGBA[i]
    s.marker = {"lineWidth": 2, "lineColor": ANYPLOT_PALETTE[i]}
    all_series.append(s)

# Power regression across all sectors: growth = a * revenue^b (b < 0 → inverse)
arr_x = np.array(all_rev_flat, dtype=float)
arr_y = np.array(all_grw_flat, dtype=float)
b_coef, log_a = np.polyfit(np.log(arr_x), np.log(arr_y), 1)
a_coef = np.exp(log_a)
trend_x = np.linspace(5, 660, 100)
trend_y = np.clip(a_coef * trend_x**b_coef, 0, 70)

trend = LineSeries()
trend.name = "Trend: revenue ↑ → growth ↓"
trend.data = list(zip(trend_x.tolist(), trend_y.tolist(), strict=True))
trend.color = INK_SOFT
trend.dash_style = "LongDash"
trend.line_width = 4
trend.enable_mouse_tracking = False
trend.marker = {"enabled": False}

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
    "text": "Bubble size = Market Cap — dashed trend confirms inverse revenue–growth relationship",
    "style": {"fontSize": "44px", "color": INK_SOFT},
}

chart.options.x_axis = {
    "title": {"text": "Revenue (Billion USD)", "style": {"fontSize": "56px", "color": INK}, "margin": 20},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "gridLineWidth": 0,
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
chart.add_series(trend)

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
