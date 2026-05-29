"""anyplot.ai
bullet-basic: Basic Bullet Chart
Library: highcharts | Python 3.14.3
Quality: 90/100 | Updated: 2026-05-29
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens — read ANYPLOT_THEME from environment
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette — semantic exception: green=exceeds target, red=below target
IMPRINT_GREEN = "#009E73"  # position 1 — good / pass / exceed
IMPRINT_RED = "#AE3030"  # position 5 — bad / fail / below (semantic anchor)

# Qualitative range bands — grayscale per spec, theme-adaptive
RANGE_COLORS = ["#e0ded8", "#b4b2ac", "#848280"] if THEME == "light" else ["#2e2e2a", "#484844", "#62625e"]

# Data — Q4 KPI dashboard: 4 metrics, mixed above/below target
metrics = [
    {"name": "Revenue", "actual": 275, "target": 250, "max": 300, "label": "$275K"},
    {"name": "Profit", "actual": 22, "target": 27, "max": 35, "label": "22%"},
    {"name": "Customers", "actual": 1650, "target": 1500, "max": 2000, "label": "1,650"},
    {"name": "Satisfaction", "actual": 4.5, "target": 4.7, "max": 5.0, "label": "4.5/5"},
]

# Normalize to 0-100% scale for a shared axis
series_data = []
for m in metrics:
    series_data.append(
        {
            "y": round(m["actual"] / m["max"] * 100, 1),
            "target": round(m["target"] / m["max"] * 100, 1),
            "label": m["label"],
            "color": IMPRINT_GREEN if m["actual"] >= m["target"] else IMPRINT_RED,
        }
    )

categories = [m["name"] for m in metrics]

# Title — adaptive font sizing (67-char baseline → 66px per highcharts.md)
TITLE = "Q4 KPI Dashboard · bullet-basic · python · highcharts · anyplot.ai"
_n = len(TITLE)
_ratio = 67 / _n if _n > 67 else 1.0
TITLE_PX = f"{max(44, round(66 * _ratio))}px"

FONT = "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"

# Chart configuration — 3200×1800 landscape
chart_options = {
    "chart": {
        "type": "bullet",
        "width": 3200,
        "height": 1800,
        "backgroundColor": PAGE_BG,
        "inverted": True,
        "marginLeft": 320,
        "marginRight": 80,
        "marginTop": 140,
        "marginBottom": 130,
        "style": {"fontFamily": FONT},
    },
    "title": {"text": TITLE, "style": {"fontSize": TITLE_PX, "fontWeight": "bold", "color": INK, "fontFamily": FONT}},
    "subtitle": {
        "text": (
            f'<span style="font-size:40px; color:{INK_SOFT}; font-family:{FONT};">'
            "Actual performance vs targets — green exceeds target, red falls short"
            "</span>"
        ),
        "useHTML": True,
    },
    "xAxis": {
        "categories": categories,
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "labels": {"style": {"fontSize": "44px", "fontWeight": "600", "color": INK_SOFT, "fontFamily": FONT}},
    },
    "yAxis": {
        "gridLineColor": GRID,
        "gridLineWidth": 1,
        "min": 0,
        "max": 100,
        "title": {"text": "% of Maximum", "style": {"fontSize": "56px", "color": INK, "fontFamily": FONT}},
        "tickInterval": 25,
        "labels": {"format": "{value}%", "style": {"fontSize": "44px", "color": INK_SOFT, "fontFamily": FONT}},
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "plotBands": [
            {"from": 0, "to": 50, "color": RANGE_COLORS[0]},
            {"from": 50, "to": 75, "color": RANGE_COLORS[1]},
            {"from": 75, "to": 100, "color": RANGE_COLORS[2]},
        ],
    },
    "legend": {"enabled": False},
    "plotOptions": {
        "bullet": {
            "pointPadding": 0.15,
            "borderWidth": 0,
            "groupPadding": 0.05,
            "targetOptions": {"width": "200%", "height": 8, "borderWidth": 0, "color": INK},
            "dataLabels": {
                "enabled": True,
                "format": "{point.label}",
                "style": {
                    "fontSize": "36px",
                    "fontWeight": "bold",
                    "color": "#ffffff",
                    "fontFamily": FONT,
                    "textOutline": "none",
                },
                "inside": True,
                "align": "right",
            },
        }
    },
    "series": [{"name": "Performance", "data": series_data}],
    "tooltip": {
        "headerFormat": f'<span style="font-size:36px; font-weight:bold; color:{INK};">{{point.key}}</span><br/>',
        "pointFormat": (
            f'<span style="font-size:32px; color:{INK_SOFT};">'
            f"Actual: <b>{{point.label}}</b> ({{point.y}}%)<br/>"
            f"Target: {{point.target}}%"
            f"</span>"
        ),
        "backgroundColor": ELEVATED_BG,
        "borderColor": INK_SOFT,
        "style": {"color": INK},
    },
    "credits": {"enabled": False},
}

# Download Highcharts JS files for inline embedding (headless Chrome cannot load CDN)
cdn_base = "https://cdn.jsdelivr.net/npm/highcharts@11.4"
js_modules = {}
for name, path in [("highcharts", "/highcharts.js"), ("more", "/highcharts-more.js"), ("bullet", "/modules/bullet.js")]:
    url = cdn_base + path
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        js_modules[name] = response.read().decode("utf-8")

# Build HTML with inline scripts
chart_json = json.dumps(chart_options)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{js_modules["highcharts"]}</script>
    <script>{js_modules["more"]}</script>
    <script>{js_modules["bullet"]}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            Highcharts.chart('container', {chart_json});
        }});
    </script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML for screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Screenshot with headless Chrome — CDP override ensures exact 3200×1800 viewport
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

# PIL safety net — pin to exact 3200×1800 in case of ±1-2 px rounding
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
