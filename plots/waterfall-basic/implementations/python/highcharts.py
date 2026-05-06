"""anyplot.ai
waterfall-basic: Basic Waterfall Chart
Library: highcharts | Python 3.13
Quality: pending | Created: 2025-12-24
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette: positive = brand green, negative = vermillion
POSITIVE_COLOR = "#009E73"  # Okabe-Ito position 1 (brand green)
NEGATIVE_COLOR = "#D55E00"  # Okabe-Ito position 2 (vermillion)
TOTAL_COLOR = "#0072B2"  # Okabe-Ito position 3 (blue) for start/end totals

# Data - Quarterly financial breakdown from revenue to net income
categories = [
    "Revenue",
    "Product Costs",
    "Operating Expenses",
    "Marketing",
    "R&D",
    "Other Income",
    "Taxes",
    "Net Income",
]

# Values: positive = increase, negative = decrease
values = [
    {"y": 500000, "color": TOTAL_COLOR},  # Revenue - starting total
    {"y": -150000, "color": NEGATIVE_COLOR},  # Product Costs
    {"y": -80000, "color": NEGATIVE_COLOR},  # Operating Expenses
    {"y": -45000, "color": NEGATIVE_COLOR},  # Marketing
    {"y": -35000, "color": NEGATIVE_COLOR},  # R&D
    {"y": 20000, "color": POSITIVE_COLOR},  # Other Income
    {"y": -52000, "color": NEGATIVE_COLOR},  # Taxes
    {"isSum": True, "color": TOTAL_COLOR},  # Net Income - ending total
]

# Chart options for Highcharts waterfall
chart_options = {
    "chart": {
        "type": "waterfall",
        "width": 4800,
        "height": 2700,
        "backgroundColor": PAGE_BG,
        "marginBottom": 280,
        "style": {"fontFamily": "Arial, sans-serif", "color": INK},
    },
    "title": {
        "text": "waterfall-basic · highcharts · anyplot.ai",
        "style": {"fontSize": "28px", "fontWeight": "normal", "color": INK},
    },
    "xAxis": {
        "categories": categories,
        "title": {"text": "", "style": {"fontSize": "22px", "color": INK}},
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "gridLineColor": GRID,
    },
    "yAxis": {
        "title": {"text": "Amount ($)", "style": {"fontSize": "22px", "color": INK}},
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}, "formatter": "__FORMATTER_PLACEHOLDER__"},
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "gridLineColor": GRID,
    },
    "legend": {"enabled": False},
    "tooltip": {
        "pointFormat": "<b>${point.y:,.0f}</b>",
        "headerFormat": "<b>{point.key}</b><br>",
        "style": {"fontSize": "18px"},
    },
    "plotOptions": {
        "waterfall": {
            "lineWidth": 2,
            "lineColor": INK_SOFT,
            "borderWidth": 0,
            "pointPadding": 0.15,
            "dataLabels": {
                "enabled": True,
                "formatter": "__DATALABEL_FORMATTER_PLACEHOLDER__",
                "style": {"fontSize": "18px", "fontWeight": "bold", "color": INK, "textOutline": "none"},
            },
        }
    },
    "series": [{"name": "Financial Breakdown", "data": values}],
}

# Generate chart options JSON and add custom formatters
chart_options_json = json.dumps(chart_options)

# Replace placeholder with actual JavaScript formatter function for y-axis labels
y_axis_formatter = """function() {
    return '$' + Highcharts.numberFormat(this.value, 0, '.', ',');
}"""
chart_options_json = chart_options_json.replace('"__FORMATTER_PLACEHOLDER__"', y_axis_formatter)

# Replace placeholder with actual JavaScript formatter function for data labels
data_label_formatter = """function() {
    var val = this.y;
    var prefix = val >= 0 ? '+$' : '-$';
    if (this.point.isSum) {
        prefix = '$';
    }
    return prefix + Highcharts.numberFormat(Math.abs(val), 0, '.', ',');
}"""
chart_options_json = chart_options_json.replace('"__DATALABEL_FORMATTER_PLACEHOLDER__"', data_label_formatter)

# Try to download JS, fallback to CDN links if network unavailable
highcharts_js = ""
highcharts_more_js = ""

try:
    highcharts_url = "https://code.highcharts.com/highcharts.js"
    req = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as response:
        highcharts_js = response.read().decode("utf-8")
except Exception:
    highcharts_js = None

try:
    highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
    req = urllib.request.Request(highcharts_more_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as response:
        highcharts_more_js = response.read().decode("utf-8")
except Exception:
    highcharts_more_js = None

# Generate HTML content based on whether we downloaded the scripts
if highcharts_js and highcharts_more_js:
    # Use inline scripts
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
        document.addEventListener('DOMContentLoaded', function() {{
            Highcharts.chart('container', {chart_options_json});
        }});
    </script>
</body>
</html>"""
else:
    # Fallback to CDN script tags
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/highcharts-more.js"></script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        window.addEventListener('load', function() {{
            if (typeof Highcharts !== 'undefined') {{
                Highcharts.chart('container', {chart_options_json});
            }}
        }});
    </script>
</body>
</html>"""

# Write HTML artifact for the site (both themes)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot for the PNG artifact
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")
chrome_options.add_argument("--disable-web-resources")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")

try:
    # Wait for either Highcharts to be available or max timeout
    WebDriverWait(driver, 15).until(lambda d: d.execute_script("return typeof Highcharts !== 'undefined'"))
except Exception:
    pass

time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
