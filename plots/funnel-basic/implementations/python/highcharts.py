"""anyplot.ai
funnel-basic: Basic Funnel Chart
Library: highcharts unknown | Python 3.14.4
Quality: 91/100 | Updated: 2026-04-26
"""

import base64
import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito categorical palette (first series is always #009E73)
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00"]

# Sales funnel: visitors progressing from initial awareness through purchase.
stages = ["Awareness", "Interest", "Consideration", "Intent", "Purchase"]
values = [1000, 600, 400, 200, 100]

funnel_data = [
    {"name": stage, "y": value, "color": OKABE_ITO[i]}
    for i, (stage, value) in enumerate(zip(stages, values, strict=True))
]

chart_options = {
    "chart": {
        "type": "funnel",
        "width": 4800,
        "height": 2700,
        "backgroundColor": PAGE_BG,
        "marginTop": 260,
        "marginBottom": 160,
        "spacingLeft": 80,
        "spacingRight": 80,
        "style": {"fontFamily": "Arial, sans-serif", "color": INK},
    },
    "title": {
        "text": "funnel-basic · highcharts · anyplot.ai",
        "align": "left",
        "x": 80,
        "y": 80,
        "style": {"fontSize": "56px", "fontWeight": "500", "color": INK},
    },
    "subtitle": {
        "text": "Sales funnel: visitor progression from awareness to purchase",
        "align": "left",
        "x": 80,
        "y": 150,
        "style": {"fontSize": "30px", "color": INK_SOFT},
    },
    "legend": {"enabled": False},
    "credits": {"enabled": False},
    "tooltip": {
        "useHTML": True,
        "backgroundColor": ELEVATED_BG,
        "borderColor": GRID,
        "borderRadius": 8,
        "style": {"color": INK, "fontSize": "22px"},
        "headerFormat": "",
        "pointFormat": (
            "<span style='color:{point.color}; font-size:28px'>●</span> "
            "<b>{point.name}</b><br/>"
            "Value: <b>{point.y:,.0f}</b><br/>"
            "Share: <b>{point.percentage:.1f}%</b>"
        ),
    },
    "plotOptions": {
        "funnel": {
            "neckWidth": "30%",
            "neckHeight": "25%",
            "width": "55%",
            "height": "78%",
            "center": ["42%", "55%"],
            "borderColor": PAGE_BG,
            "borderWidth": 6,
            "states": {"hover": {"brightness": 0.08, "halo": {"size": 0}}},
            "dataLabels": {
                "enabled": True,
                "softConnector": True,
                "distance": 60,
                "connectorWidth": 3,
                "connectorColor": INK_SOFT,
                "format": "<b>{point.name}</b><br/><span style='font-weight:400'>{point.y:,.0f} ({point.percentage:.1f}%)</span>",
                "style": {"fontSize": "36px", "color": INK, "textOutline": "none"},
            },
        }
    },
    "series": [{"type": "funnel", "name": "Sales funnel", "data": funnel_data}],
}

# Highcharts core + funnel module.
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@12/highcharts.js"
funnel_url = "https://cdn.jsdelivr.net/npm/highcharts@12/modules/funnel.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")
with urllib.request.urlopen(funnel_url, timeout=30) as response:
    funnel_js = response.read().decode("utf-8")

chart_options_json = json.dumps(chart_options)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{funnel_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        Highcharts.chart('container', {chart_options_json});
    </script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 4800, "height": 2700, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)

result = driver.execute_cdp_cmd(
    "Page.captureScreenshot",
    {
        "captureBeyondViewport": True,
        "clip": {"x": 0, "y": 0, "width": 4800, "height": 2700, "scale": 1},
        "format": "png",
    },
)
with open(f"plot-{THEME}.png", "wb") as f:
    f.write(base64.b64decode(result["data"]))

driver.quit()

Path(temp_path).unlink()
