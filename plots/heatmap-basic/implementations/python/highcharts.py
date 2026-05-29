""" anyplot.ai
heatmap-basic: Basic Heatmap
Library: highcharts unknown | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-28
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme-adaptive chrome tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Canvas: 2400×2400 (square — heatmaps are grid-based symmetric plots)
W, H = 2400, 2400

# Data — website traffic by day and time of day (8×7 matrix)
np.random.seed(42)
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
time_slots = ["6–9 AM", "9 AM–Noon", "Noon–3 PM", "3–6 PM", "6–9 PM", "9 PM–Mid", "Mid–3 AM", "3–6 AM"]

base = np.random.randint(15, 55, size=(len(time_slots), len(days))).astype(float)
multipliers = np.array([1.3, 2.0, 2.0, 2.0, 1.0, 0.6, 0.25, 0.25]).reshape(-1, 1)
base *= multipliers
base[0:4, 5:7] *= 0.5  # weekend daytime quieter
base[4:6, 5:7] *= 1.5  # weekend evenings busier
traffic = np.clip(base, 0, 100).astype(int)

heatmap_data = [
    [x_idx, y_idx, int(traffic[y_idx, x_idx])] for y_idx in range(len(time_slots)) for x_idx in range(len(days))
]

# Title font scaling (67-char baseline)
title = "Website Traffic · heatmap-basic · python · highcharts · anyplot.ai"
n = len(title)
ratio = 67 / n if n > 67 else 1.0
title_px = max(44, round(66 * ratio))

chart_options = {
    "chart": {
        "type": "heatmap",
        "width": W,
        "height": H,
        "backgroundColor": PAGE_BG,
        "marginTop": 155,
        "marginBottom": 160,
        "marginRight": 290,
        "marginLeft": 300,
        "style": {"fontFamily": "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"},
    },
    "title": {"text": title, "style": {"fontSize": f"{title_px}px", "fontWeight": "600", "color": INK}, "y": 28},
    "subtitle": {
        "text": "Visits per hour — weekday business hours show peak activity",
        "style": {"fontSize": "34px", "fontWeight": "normal", "color": INK_MUTED},
        "y": 76,
    },
    "xAxis": {
        "categories": days,
        "title": {
            "text": "Day of Week",
            "style": {"fontSize": "46px", "fontWeight": "600", "color": INK},
            "margin": 14,
        },
        "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
        "lineWidth": 0,
        "tickLength": 0,
    },
    "yAxis": {
        "categories": time_slots,
        "title": {
            "text": "Time of Day",
            "style": {"fontSize": "46px", "fontWeight": "600", "color": INK},
            "margin": 14,
        },
        "labels": {"style": {"fontSize": "38px", "color": INK_SOFT}},
        "reversed": True,
        "lineWidth": 0,
        "gridLineWidth": 0,
    },
    # Imprint sequential colormap: brand green (low) → blue (high)
    "colorAxis": {
        "min": 0,
        "max": 100,
        "minColor": "#009E73",
        "maxColor": "#4467A3",
        "stops": [[0, "#009E73"], [1, "#4467A3"]],
        "labels": {"style": {"fontSize": "36px", "color": INK_SOFT}},
    },
    "legend": {
        "title": {"text": "Visits / hr", "style": {"fontSize": "36px", "fontWeight": "600", "color": INK}},
        "align": "right",
        "layout": "vertical",
        "verticalAlign": "middle",
        "symbolHeight": 700,
        "symbolWidth": 36,
        "itemStyle": {"fontSize": "34px", "color": INK_SOFT},
        "x": -50,
        "margin": 40,
        "backgroundColor": ELEVATED_BG,
        "borderColor": INK_SOFT,
        "borderWidth": 1,
    },
    "tooltip": {
        "style": {"fontSize": "32px"},
        "headerFormat": "",
        "pointFormat": (
            "<b>{series.yAxis.categories.(point.y)}</b><br>"
            "<b>{series.xAxis.categories.(point.x)}</b><br>"
            "Visits/hr: <b>{point.value}</b>"
        ),
    },
    "credits": {"enabled": False},
    "plotOptions": {"heatmap": {"colsize": 1, "rowsize": 1}},
    "series": [
        {
            "type": "heatmap",
            "name": "Website Traffic",
            "data": heatmap_data,
            "borderWidth": 3,
            "borderColor": PAGE_BG,
            "dataLabels": {"enabled": True, "style": {"fontSize": "32px", "fontWeight": "bold", "textOutline": "none"}},
        }
    ],
}

# Download Highcharts JS + heatmap module (inline required for headless Chrome)
highcharts_url = "https://code.highcharts.com/highcharts.js"
heatmap_url = "https://code.highcharts.com/modules/heatmap.js"

_headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.highcharts.com/"}

req = urllib.request.Request(highcharts_url, headers=_headers)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

req = urllib.request.Request(heatmap_url, headers=_headers)
with urllib.request.urlopen(req, timeout=30) as response:
    heatmap_js = response.read().decode("utf-8")

options_json = json.dumps(chart_options)

# Both Imprint seq endpoints are dark → off-white labels read well on all cells
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="margin:0; padding:0; overflow:hidden; background:{PAGE_BG};">
    <div id="container" style="width:{W}px; height:{H}px;"></div>
    <script>
        var opts = {options_json};
        opts.series[0].dataLabels.formatter = function() {{
            var v = this.point.value;
            return '<span style="color:#F0EFE8;font-size:32px;font-weight:bold">' + v + '</span>';
        }};
        opts.series[0].dataLabels.useHTML = true;
        Highcharts.chart('container', opts);
    </script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via headless Chrome with CDP viewport override
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument(f"--window-size={W},{H}")

driver = webdriver.Chrome(options=chrome_options)
# CDP override is authoritative; --window-size alone loses ~139 px to Chrome chrome
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin to exact canvas dims (belt-and-braces against ±1–2 px CDP rounding)
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (W, H):
    _norm = Image.new("RGB", (W, H), PAGE_BG)
    _norm.paste(_img, ((W - _img.size[0]) // 2, (H - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
