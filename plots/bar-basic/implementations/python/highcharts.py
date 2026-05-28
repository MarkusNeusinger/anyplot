""" anyplot.ai
bar-basic: Basic Bar Chart
Library: highcharts unknown | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-28
"""

import os
import re
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import ColumnSeries
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
ANYPLOT_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

ANYPLOT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = ANYPLOT_PALETTE[0]

# Data — product sales by category, sorted descending
categories = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books", "Toys"]
values = [4800, 3100, 2200, 1700, 950, 480]
avg_sales = sum(values) / len(values)

title = "bar-basic · python · highcharts · anyplot.ai"  # 44 chars — no scaling

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "column",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "marginBottom": 220,
    "marginTop": 100,
    "marginLeft": 220,
    "marginRight": 80,
    "style": {"fontFamily": "Arial, Helvetica, sans-serif"},
}

chart.options.title = {"text": title, "style": {"fontSize": "66px", "fontWeight": "bold", "color": INK}, "margin": 36}

chart.options.subtitle = {
    "text": "Electronics dominates with 4,800 units — 10× more than Toys",
    "style": {"fontSize": "44px", "color": INK_SOFT, "fontWeight": "normal"},
    "margin": 24,
}

chart.options.x_axis = {
    "categories": categories,
    "title": {"text": "Product Category", "style": {"fontSize": "56px", "color": INK}, "margin": 20},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "tickLength": 8,
    "gridLineColor": GRID,
}

chart.options.y_axis = {
    "title": {"text": "Sales (Units)", "style": {"fontSize": "56px", "color": INK}, "margin": 15},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}, "format": "{value:,.0f}"},
    "max": 5200,
    "endOnTick": False,
    "tickInterval": 1000,
    "gridLineColor": GRID,
    "gridLineWidth": 1,
    "plotLines": [
        {
            "value": avg_sales,
            "color": INK_SOFT,
            "width": 3,
            "dashStyle": "LongDash",
            "zIndex": 5,
            "label": {
                "text": f"Avg: {avg_sales:,.0f} units",
                "align": "right",
                "x": -12,
                "y": -14,
                "style": {"fontSize": "40px", "color": INK_SOFT, "fontWeight": "bold"},
            },
        }
    ],
}

chart.options.tooltip = {
    "headerFormat": '<span style="font-size:44px;font-weight:bold">{point.key}</span><br/>',
    "pointFormat": '<span style="font-size:40px">Sales: <b>{point.y:,.0f}</b> units</span>',
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderRadius": 6,
    "borderWidth": 1,
}

chart.options.plot_options = {
    "column": {"pointPadding": 0.12, "borderWidth": 0, "groupPadding": 0.08, "borderRadius": 4}
}

# Top performer in brand green; remaining bars in muted neutral
data_points = [{"y": values[0], "color": BRAND}]
for v in values[1:]:
    data_points.append({"y": v, "color": ANYPLOT_MUTED})

series = ColumnSeries.from_dict(
    {
        "data": data_points,
        "name": "Sales",
        "type": "column",
        "dataLabels": {
            "enabled": True,
            "format": "{y:,.0f}",
            "style": {"fontSize": "44px", "fontWeight": "bold", "color": INK, "textOutline": f"2px {PAGE_BG}"},
            "y": -8,
        },
    }
)
chart.add_series(series)

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}

# Download Highcharts JS for inline embedding (required for headless Chrome)
req = urllib.request.Request(
    "https://code.highcharts.com/highcharts.js",
    headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.highcharts.com/"},
)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

chart_js = chart.to_js_literal()
# Wrap bare Highcharts format templates in single quotes (to_js_literal may omit them)
chart_js = re.sub(r"format: (\{[^}]+\})", r"format: '\1'", chart_js)

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{chart_js}</script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and capture PNG via headless Chrome
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
# CDP override is authoritative — --window-size alone loses ~139 px to Chrome chrome
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin to exact 3200×1800 to satisfy the post-render gate
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
