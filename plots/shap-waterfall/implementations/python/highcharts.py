""" anyplot.ai
shap-waterfall: SHAP Waterfall Plot for Feature Attribution
Library: highcharts unknown | Python 3.13.13
Quality: 86/100 | Created: 2026-05-07
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


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

BRAND = "#009E73"  # Okabe-Ito pos 1 — baseline & prediction bars
POSITIVE_COLOR = "#AE3030"  # imprint red — positive SHAP (pushes risk up)
NEGATIVE_COLOR = "#4467A3"  # Okabe-Ito pos 3 — negative SHAP (pushes risk down)

# Data — credit scoring model explaining a single loan application
# Features sorted by absolute SHAP value (largest contribution first = top of chart)
BASE_VALUE = 0.35  # Expected probability of default across all applicants

features = [
    "Credit Score",
    "Debt-to-Income",
    "Annual Income",
    "Loan Amount",
    "Employment Years",
    "Payment History",
    "Open Accounts",
    "Credit Inquiries",
    "Credit Age",
    "Savings Balance",
]
shap_values = [-0.18, +0.15, -0.12, +0.09, -0.07, -0.05, +0.04, +0.03, -0.02, -0.02]
FINAL_VALUE = round(BASE_VALUE + sum(shap_values), 4)

# Build waterfall data: base bar → feature deltas → isSum final
categories = ["E[f(x)] Baseline", *features, "f(x) Prediction"]

data_points = [{"y": BASE_VALUE, "color": BRAND}]
for sv in shap_values:
    data_points.append({"y": sv, "color": POSITIVE_COLOR if sv > 0 else NEGATIVE_COLOR})
data_points.append({"isSum": True, "color": BRAND})

# Chart configuration (JSON-serializable; JS functions injected via string replace)
chart_config = {
    "chart": {
        "type": "waterfall",
        "inverted": True,
        "width": 4800,
        "height": 2700,
        "backgroundColor": PAGE_BG,
        "marginLeft": 340,
        "marginRight": 220,
        "marginTop": 130,
        "marginBottom": 220,
        "style": {"fontFamily": "Arial, sans-serif", "color": INK},
    },
    "title": {
        "text": "Credit Default Risk · shap-waterfall · highcharts · anyplot.ai",
        "style": {"fontSize": "28px", "fontWeight": "normal", "color": INK},
        "align": "left",
        "x": 340,
    },
    "xAxis": {
        "categories": categories,
        "title": {"text": "Feature", "style": {"fontSize": "22px", "color": INK}},
        "labels": {"style": {"fontSize": "20px", "color": INK_SOFT}},
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "gridLineColor": GRID,
    },
    "yAxis": {
        "title": {"text": "Probability of Default", "style": {"fontSize": "22px", "color": INK}},
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}, "formatter": "__YAXIS_FORMATTER__"},
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "gridLineColor": GRID,
        "gridLineWidth": 1,
        "min": -0.02,
        "max": 0.50,
        "plotLines": [
            {
                "value": BASE_VALUE,
                "color": INK_SOFT,
                "width": 2,
                "dashStyle": "Dash",
                "zIndex": 2,
                "label": {
                    "text": f"Baseline {BASE_VALUE:.2f}",
                    "align": "right",
                    "rotation": 0,
                    "x": -6,
                    "y": -12,
                    "style": {"fontSize": "16px", "color": INK_SOFT},
                },
            },
            {
                "value": FINAL_VALUE,
                "color": BRAND,
                "width": 2,
                "dashStyle": "ShortDot",
                "zIndex": 2,
                "label": {
                    "text": f"Prediction {FINAL_VALUE:.2f}",
                    "align": "right",
                    "rotation": 0,
                    "x": -6,
                    "y": -12,
                    "style": {"fontSize": "16px", "color": BRAND},
                },
            },
        ],
    },
    "legend": {"enabled": False},
    "tooltip": {"enabled": False},
    "plotOptions": {
        "waterfall": {
            "lineWidth": 2,
            "lineColor": INK_SOFT,
            "borderWidth": 0,
            "groupPadding": 0.05,
            "pointPadding": 0.08,
            "dataLabels": {
                "enabled": True,
                "formatter": "__DATA_LABEL_FORMATTER__",
                "style": {"fontSize": "18px", "fontWeight": "bold", "color": INK, "textOutline": "none"},
                "inside": False,
            },
        }
    },
    "series": [{"name": "SHAP Attribution", "data": data_points}],
}

# Inject JavaScript formatter functions (not JSON-serializable, so replace placeholders)
config_json = json.dumps(chart_config)

yaxis_formatter = """function() {
    return Highcharts.numberFormat(this.value, 2);
}"""
config_json = config_json.replace('"__YAXIS_FORMATTER__"', yaxis_formatter)

data_label_formatter = """function() {
    if (this.point.isSum) {
        return 'f(x) = ' + Highcharts.numberFormat(this.y, 2);
    }
    if (this.point.index === 0) {
        return 'E[f(x)] = ' + Highcharts.numberFormat(this.y, 2);
    }
    var sign = this.y > 0 ? '+' : '';
    return sign + Highcharts.numberFormat(this.y, 3);
}"""
config_json = config_json.replace('"__DATA_LABEL_FORMATTER__"', data_label_formatter)


# Download Highcharts JS with multiple CDN fallbacks
def download_js(paths, timeout=15):
    cdn_bases = [
        "https://cdn.jsdelivr.net/npm/highcharts@11/",
        "https://unpkg.com/highcharts@11/",
        "https://code.highcharts.com/",
    ]
    for path in paths:
        for base in cdn_bases:
            url = base + path
            for attempt in range(2):
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=timeout) as resp:
                        return resp.read().decode("utf-8")
                except Exception:
                    if attempt == 0:
                        time.sleep(1)
    return None


highcharts_js = download_js(["highcharts.js"])
if highcharts_js is None:
    raise RuntimeError("Failed to download highcharts.js from all CDNs")

# Waterfall chart type lives in highcharts-more.js
highcharts_more_js = download_js(["highcharts-more.js"])
if highcharts_more_js is None:
    raise RuntimeError("Failed to download highcharts-more.js from all CDNs")

# Generate HTML with inline Highcharts JS (core + more module for waterfall type)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        Highcharts.chart('container', {config_json});
    </script>
</body>
</html>"""

# Save interactive HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via headless Chrome with CDP for full-resolution capture
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--force-device-scale-factor=1")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

screenshot_config = {"captureBeyondViewport": True, "clip": {"x": 0, "y": 0, "width": 4800, "height": 2700, "scale": 1}}
result = driver.execute_cdp_cmd("Page.captureScreenshot", screenshot_config)
with open(f"plot-{THEME}.png", "wb") as f:
    f.write(base64.b64decode(result["data"]))
driver.quit()

Path(temp_path).unlink()
