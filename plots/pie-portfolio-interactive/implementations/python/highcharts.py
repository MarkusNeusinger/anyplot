"""anyplot.ai
pie-portfolio-interactive: Interactive Portfolio Allocation Chart
Library: highcharts | Python 3.13
Quality: pending | Created: 2026-05-27
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

# anyplot categorical palette — 8 hues, hybrid-v3 sort order
ANYPLOT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

title = "pie-portfolio-interactive · python · highcharts · anyplot.ai"

# Data — portfolio allocation with drill-down structure
portfolio_data = [
    {"name": "Equities", "y": 55.0, "drilldown": "equities", "color": ANYPLOT_PALETTE[0]},
    {"name": "Fixed Income", "y": 25.0, "drilldown": "fixed-income", "color": ANYPLOT_PALETTE[1]},
    {"name": "Alternatives", "y": 12.0, "drilldown": "alternatives", "color": ANYPLOT_PALETTE[2]},
    {"name": "Cash", "y": 8.0, "drilldown": "cash", "color": ANYPLOT_PALETTE[3]},
]

# Drill-down data — sub-holdings within each asset class
drilldown_series = [
    {
        "type": "pie",
        "id": "equities",
        "name": "Equities",
        "data": [
            ["Apple Inc.", 12.0],
            ["Microsoft Corp.", 10.0],
            ["Amazon.com", 8.0],
            ["Alphabet Inc.", 7.0],
            ["Tesla Inc.", 6.0],
            ["NVIDIA Corp.", 5.0],
            ["Other Equities", 7.0],
        ],
    },
    {
        "type": "pie",
        "id": "fixed-income",
        "name": "Fixed Income",
        "data": [
            ["US Treasury 10Y", 10.0],
            ["Corporate Bonds AAA", 7.0],
            ["Municipal Bonds", 5.0],
            ["High Yield Bonds", 3.0],
        ],
    },
    {
        "type": "pie",
        "id": "alternatives",
        "name": "Alternatives",
        "data": [["Real Estate (REITs)", 5.0], ["Commodities (Gold)", 4.0], ["Private Equity", 3.0]],
    },
    {"type": "pie", "id": "cash", "name": "Cash", "data": [["Money Market Fund", 5.0], ["Savings Account", 3.0]]},
]

# Chart — 2400×2400 square canvas for pie/donut
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "pie",
    "width": 2400,
    "height": 2400,
    "backgroundColor": PAGE_BG,
    "style": {"color": INK},
    "marginBottom": 160,
}

chart.options.title = {"text": title, "style": {"fontSize": "66px", "fontWeight": "bold", "color": INK}}

chart.options.subtitle = {
    "text": "Click slices to explore individual holdings",
    "style": {"fontSize": "44px", "color": INK_SOFT},
}

chart.options.tooltip = {
    "headerFormat": '<span style="font-size: 44px">{series.name}</span><br>',
    "pointFormat": '<span style="color:{point.color}">&#9679;</span> {point.name}: <b>{point.y:.1f}%</b><br/>',
    "style": {"fontSize": "40px"},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}

chart.options.accessibility = {"announceNewData": {"enabled": True}, "point": {"valueSuffix": "%"}}

chart.options.plot_options = {
    "pie": {
        "allowPointSelect": True,
        "cursor": "pointer",
        "innerSize": "50%",
        "dataLabels": {
            "enabled": True,
            "format": "<b>{point.name}</b>: {point.percentage:.1f}%",
            "style": {"fontSize": "38px", "fontWeight": "normal", "color": INK},
            "distance": 40,
        },
        "showInLegend": True,
    }
}

# Legend centered at bottom — fixes previous right-edge visual imbalance
chart.options.legend = {
    "enabled": True,
    "layout": "horizontal",
    "align": "center",
    "verticalAlign": "bottom",
    "itemStyle": {"fontSize": "44px", "color": INK_SOFT, "fontWeight": "normal"},
    "itemMarginBottom": 10,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "padding": 16,
}

chart.options.drilldown = {
    "activeAxisLabelStyle": {"textDecoration": "none", "fontStyle": "normal"},
    "activeDataLabelStyle": {"textDecoration": "none", "fontStyle": "normal", "color": INK},
    "breadcrumbs": {"position": {"align": "right"}, "style": {"fontSize": "38px", "color": INK_SOFT}},
    "series": drilldown_series,
}

series = PieSeries()
series.name = "Asset Classes"
series.data = portfolio_data
series.color_by_point = True
chart.add_series(series)

# Download Highcharts JS modules inline (CDN blocked in headless file:// context)
_headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.highcharts.com/"}

req = urllib.request.Request("https://code.highcharts.com/highcharts.js", headers=_headers)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

req = urllib.request.Request("https://code.highcharts.com/modules/drilldown.js", headers=_headers)
with urllib.request.urlopen(req, timeout=30) as response:
    drilldown_js = response.read().decode("utf-8")

req = urllib.request.Request("https://code.highcharts.com/modules/accessibility.js", headers=_headers)
with urllib.request.urlopen(req, timeout=30) as response:
    accessibility_js = response.read().decode("utf-8")

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{drilldown_js}</script>
    <script>{accessibility_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 2400px; height: 2400px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML artifact for the site
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and screenshot for PNG artifact
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=2400,2400")

driver = webdriver.Chrome(options=chrome_options)
# CDP override makes the viewport authoritative (--window-size alone loses ~139 px to Chrome chrome)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 2400, "height": 2400, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin to exact 2400×2400 so post-render gate passes
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (2400, 2400):
    _norm = Image.new("RGB", (2400, 2400), PAGE_BG)
    _norm.paste(_img, ((2400 - _img.size[0]) // 2, (2400 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
