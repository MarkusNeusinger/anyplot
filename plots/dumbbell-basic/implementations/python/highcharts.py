""" anyplot.ai
dumbbell-basic: Basic Dumbbell Chart
Library: highcharts unknown | Python 3.14.4
Quality: 85/100 | Updated: 2026-04-26
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
CONNECTOR = "rgba(26,26,23,0.40)" if THEME == "light" else "rgba(240,239,232,0.40)"

BEFORE_COLOR = "#009E73"  # Okabe-Ito 1 — brand
AFTER_COLOR = "#D55E00"  # Okabe-Ito 2

# Employee satisfaction scores (0-100) before and after policy changes.
# Mix of strong gains, modest gains, and two declines for full coverage.
categories = [
    "Engineering",
    "Sales",
    "Marketing",
    "Customer Support",
    "Human Resources",
    "Finance",
    "Operations",
    "Research & Dev",
    "Legal",
    "IT Support",
]
before_scores = [65, 58, 72, 45, 68, 61, 53, 70, 76, 64]
after_scores = [82, 75, 85, 78, 80, 73, 71, 88, 68, 59]

# Sort by improvement (descending): biggest gains on top, declines at bottom.
changes = [a - b for b, a in zip(before_scores, after_scores, strict=True)]
order = sorted(range(len(categories)), key=lambda i: changes[i], reverse=True)
categories = [categories[i] for i in order]
before_scores = [before_scores[i] for i in order]
after_scores = [after_scores[i] for i in order]
changes = [changes[i] for i in order]

# Build dumbbell points. To keep the green=before / orange=after semantics
# stable even when satisfaction drops (low marker is the smaller value, so
# "after" lands on it), we override per-point colors when before > after.
dumbbell_data = []
for i, (before, after) in enumerate(zip(before_scores, after_scores, strict=True)):
    low = min(before, after)
    high = max(before, after)
    if before <= after:
        dumbbell_data.append({"x": i, "low": low, "high": high})
    else:
        dumbbell_data.append(
            {
                "x": i,
                "low": low,
                "high": high,
                "lowColor": AFTER_COLOR,  # smaller value here is "after"
                "color": BEFORE_COLOR,  # larger value here is "before"
            }
        )

chart_options = {
    "chart": {
        "type": "dumbbell",
        "inverted": True,
        "width": 4800,
        "height": 2700,
        "backgroundColor": PAGE_BG,
        "marginLeft": 520,
        "marginRight": 220,
        "marginTop": 320,
        "marginBottom": 200,
        "spacingTop": 60,
        "style": {"fontFamily": "Arial, sans-serif", "color": INK},
    },
    "title": {
        "text": "dumbbell-basic · highcharts · anyplot.ai",
        "align": "left",
        "x": 80,
        "style": {"fontSize": "56px", "fontWeight": "500", "color": INK},
    },
    "subtitle": {
        "text": "Employee satisfaction scores before and after policy changes (by department)",
        "align": "left",
        "x": 80,
        "style": {"fontSize": "30px", "color": INK_SOFT},
    },
    "xAxis": {
        "categories": categories,
        "title": {"text": None},
        "labels": {"style": {"fontSize": "32px", "color": INK}},
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "tickWidth": 0,
        "gridLineWidth": 0,
        "minPadding": 0.05,
        "maxPadding": 0.05,
        "startOnTick": False,
        "endOnTick": False,
    },
    "yAxis": {
        "min": 35,
        "max": 95,
        "tickInterval": 10,
        "title": {"text": "Satisfaction Score (0–100)", "style": {"fontSize": "36px", "color": INK}, "margin": 50},
        "labels": {"style": {"fontSize": "30px", "color": INK_SOFT}},
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "gridLineColor": GRID,
        "gridLineWidth": 1,
        "opposite": False,
    },
    "legend": {
        "enabled": True,
        "align": "right",
        "verticalAlign": "top",
        "layout": "horizontal",
        "x": -20,
        "y": 80,
        "itemStyle": {"fontSize": "32px", "color": INK, "fontWeight": "500"},
        "itemDistance": 70,
        "backgroundColor": ELEVATED_BG,
        "borderColor": GRID,
        "borderWidth": 1,
        "borderRadius": 6,
        "padding": 22,
        "symbolHeight": 30,
        "symbolWidth": 30,
        "symbolRadius": 15,
    },
    "plotOptions": {
        "dumbbell": {
            "connectorWidth": 6,
            "connectorColor": CONNECTOR,
            "lowColor": BEFORE_COLOR,
            "color": AFTER_COLOR,
            "marker": {"radius": 24, "lineWidth": 3, "lineColor": PAGE_BG},
            "lowMarker": {"radius": 24, "lineWidth": 3, "lineColor": PAGE_BG},
            "dataLabels": [
                {
                    "enabled": True,
                    "format": "{point.high}",
                    "align": "left",
                    "x": 38,
                    "verticalAlign": "middle",
                    "style": {"fontSize": "28px", "color": INK_SOFT, "fontWeight": "500", "textOutline": "none"},
                },
                {
                    "enabled": True,
                    "format": "{point.low}",
                    "align": "right",
                    "x": -38,
                    "verticalAlign": "middle",
                    "style": {"fontSize": "28px", "color": INK_SOFT, "fontWeight": "500", "textOutline": "none"},
                },
            ],
        },
        "scatter": {"marker": {"radius": 18, "lineWidth": 2, "lineColor": PAGE_BG, "symbol": "circle"}},
    },
    "series": [
        {
            "type": "scatter",
            "name": "Before",
            "color": BEFORE_COLOR,
            "data": [],
            "showInLegend": True,
            "marker": {"radius": 18, "symbol": "circle"},
            "enableMouseTracking": False,
        },
        {
            "type": "scatter",
            "name": "After",
            "color": AFTER_COLOR,
            "data": [],
            "showInLegend": True,
            "marker": {"radius": 18, "symbol": "circle"},
            "enableMouseTracking": False,
        },
        {
            "type": "dumbbell",
            "name": "Satisfaction change",
            "data": dumbbell_data,
            "lowColor": BEFORE_COLOR,
            "color": AFTER_COLOR,
            "showInLegend": False,
        },
    ],
    "credits": {"enabled": False},
    "tooltip": {
        "shared": False,
        "useHTML": True,
        "backgroundColor": ELEVATED_BG,
        "borderColor": GRID,
        "style": {"color": INK, "fontSize": "20px"},
        "headerFormat": "<b>{point.key}</b><br/>",
        "pointFormat": (
            f"<span style='color:{BEFORE_COLOR}'>●</span> Before: <b>{{point.low}}</b><br/>"
            f"<span style='color:{AFTER_COLOR}'>●</span> After: <b>{{point.high}}</b>"
        ),
    },
}

# Highcharts core + dumbbell module + highcharts-more (required by dumbbell).
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@12/highcharts.js"
highcharts_more_url = "https://cdn.jsdelivr.net/npm/highcharts@12/highcharts-more.js"
dumbbell_url = "https://cdn.jsdelivr.net/npm/highcharts@12/modules/dumbbell.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")
with urllib.request.urlopen(dumbbell_url, timeout=30) as response:
    dumbbell_js = response.read().decode("utf-8")

chart_options_json = json.dumps(chart_options)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
    <script>{dumbbell_js}</script>
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

# Full-page CDP capture so the y-axis title at the bottom is not clipped
# by Chrome's reduced rendering viewport.
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
