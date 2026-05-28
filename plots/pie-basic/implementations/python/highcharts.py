""" anyplot.ai
pie-basic: Basic Pie Chart
Library: highcharts unknown | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-28
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.pie import PieSeries
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

ANYPLOT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data — Cloud infrastructure market share, 2024
categories = ["AWS", "Azure", "Google Cloud", "Alibaba", "Others"]
values = [31, 25, 11, 4, 29]
# First 4 use anyplot categorical positions 1-4; "Others" uses muted anchor (other/rest role)
colors = [ANYPLOT_PALETTE[0], ANYPLOT_PALETTE[1], ANYPLOT_PALETTE[2], ANYPLOT_PALETTE[3], INK_MUTED]

# Compute subtitle insights
top3_share = sum(values[:3])

# Title — compute fontsize scaled for length
title = "Cloud Infrastructure Market Share · pie-basic · python · highcharts · anyplot.ai"
n = len(title)
title_fontsize = max(44, round(66 * 67 / n)) if n > 67 else 66

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "pie",
    "width": 2400,
    "height": 2400,
    "backgroundColor": PAGE_BG,
    "spacingTop": 10,
    "spacingBottom": 25,
    "spacingLeft": 60,
    "spacingRight": 60,
    "style": {"fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif", "color": INK},
}

chart.options.title = {
    "text": title,
    "style": {"fontSize": f"{title_fontsize}px", "fontWeight": "bold", "color": INK},
    "margin": 8,
}

chart.options.subtitle = {
    "text": (
        f"Global cloud spending by provider, 2024 — Top 3 providers control {top3_share}% of the market"
        f'<br><span style="font-style: italic; color: {INK}; font-weight: 600;">'
        "AWS leads with nearly ⅓ of global cloud revenue</span>"
    ),
    "useHTML": True,
    "margin": 8,
    "style": {"fontSize": "34px", "color": INK_SOFT, "fontWeight": "normal", "textAlign": "center"},
}

chart.options.colors = colors
chart.options.credits = {"enabled": False}

chart.options.plot_options = {
    "pie": {
        "allowPointSelect": True,
        "cursor": "pointer",
        "borderWidth": 2,
        "borderColor": PAGE_BG,
        "shadow": {"color": "rgba(0,0,0,0.12)", "offsetX": 3, "offsetY": 3, "width": 8},
        "dataLabels": {
            "enabled": True,
            "format": "<b>{point.name}</b><br>{point.percentage:.1f}%",
            "style": {"fontSize": "38px", "textOutline": "none", "fontWeight": "normal", "color": INK},
            "distance": 65,
            "connectorWidth": 2,
            "connectorColor": INK_SOFT,
            "softConnector": True,
            "connectorShape": "crookedLine",
        },
        "showInLegend": True,
        "slicedOffset": 40,
        "size": "78%",
        "center": ["50%", "54%"],
        "startAngle": -135,
        "innerSize": "0%",
        "states": {"hover": {"halo": {"size": 15, "opacity": 0.25}}, "inactive": {"opacity": 0.5}},
    }
}

chart.options.legend = {
    "enabled": True,
    "align": "center",
    "verticalAlign": "bottom",
    "layout": "horizontal",
    "itemStyle": {"fontSize": "36px", "fontWeight": "normal", "color": INK_SOFT},
    "itemHoverStyle": {"color": INK},
    "symbolRadius": 6,
    "symbolHeight": 28,
    "symbolWidth": 28,
    "margin": 10,
    "padding": 10,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}

chart.options.tooltip = {
    "pointFormat": "<b>{point.percentage:.1f}%</b> market share",
    "style": {"fontSize": "28px", "color": INK},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderRadius": 8,
    "shadow": {"color": "rgba(0,0,0,0.08)", "offsetX": 1, "offsetY": 1, "width": 3},
}

# Series — largest slice (AWS) exploded for emphasis
series = PieSeries()
series.name = "Market Share"

series_data = []
for i, (cat, val) in enumerate(zip(categories, values, strict=True)):
    point = {"name": cat, "y": val, "sliced": i == 0, "selected": i == 0}
    series_data.append(point)

series.data = series_data
chart.add_series(series)

# Download Highcharts JS for inline embedding (CDN blocked in headless file:// context)
req = urllib.request.Request(
    "https://code.highcharts.com/highcharts.js",
    headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.highcharts.com/"},
)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Build HTML with inline scripts (not CDN links)
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 2400px; height: 2400px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save interactive HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML for screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Screenshot via headless Chrome with CDP viewport override (authoritative for exact dims)
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=2400,2400")

driver = webdriver.Chrome(options=chrome_options)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 2400, "height": 2400, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin to exact 2400×2400 (CDP override can still drift ±1-2 px)
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (2400, 2400):
    _norm = Image.new("RGB", (2400, 2400), PAGE_BG)
    _norm.paste(_img, ((2400 - _img.size[0]) // 2, (2400 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
