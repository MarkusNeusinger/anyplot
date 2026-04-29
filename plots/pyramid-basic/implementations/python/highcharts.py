""" anyplot.ai
pyramid-basic: Basic Pyramid Chart
Library: highcharts unknown | Python 3.13.13
Quality: 87/100 | Updated: 2026-04-29
"""

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
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Data - Population pyramid by age group (typical demographic data)
age_groups = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]
male_values = [-50, -62, -75, -68, -58, -52, -42, -28, -12]
female_values = [48, 60, 72, 70, 62, 55, 48, 35, 18]

max_val = max(max(abs(v) for v in male_values), max(female_values))
axis_max = int(max_val * 1.1)

chart_options = {
    "chart": {
        "type": "bar",
        "width": 4800,
        "height": 2700,
        "backgroundColor": PAGE_BG,
        "marginLeft": 200,
        "marginRight": 200,
        "marginBottom": 220,
        "style": {"fontFamily": "Arial, sans-serif", "color": INK},
    },
    "title": {
        "text": "Population by Age Group · pyramid-basic · highcharts · anyplot.ai",
        "style": {"fontSize": "48px", "fontWeight": "bold", "color": INK},
    },
    "subtitle": {
        "text": "Male (left) vs Female (right) - Population in Millions",
        "style": {"fontSize": "32px", "color": INK_SOFT},
    },
    "xAxis": [
        {
            "categories": age_groups,
            "reversed": False,
            "title": {"text": "Age Group", "style": {"fontSize": "36px", "color": INK}},
            "labels": {"style": {"fontSize": "28px", "color": INK_SOFT}},
            "lineColor": INK_SOFT,
            "tickColor": INK_SOFT,
        }
    ],
    "yAxis": {
        "title": {"text": "Population (Millions)", "style": {"fontSize": "36px", "color": INK}},
        "labels": {"style": {"fontSize": "28px", "color": INK_SOFT}, "formatter": "__FORMATTER_PLACEHOLDER__"},
        "min": -axis_max,
        "max": axis_max,
        "gridLineColor": GRID,
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "plotLines": [{"color": INK_SOFT, "width": 2, "value": 0, "zIndex": 5}],
    },
    "legend": {
        "enabled": True,
        "layout": "horizontal",
        "align": "center",
        "verticalAlign": "top",
        "y": 10,
        "itemStyle": {"fontSize": "28px", "color": INK_SOFT, "fontWeight": "normal"},
        "backgroundColor": ELEVATED_BG,
        "borderColor": INK_SOFT,
        "borderWidth": 1,
        "padding": 16,
        "itemMarginTop": 8,
        "itemMarginBottom": 8,
    },
    "tooltip": {
        "formatter": "__TOOLTIP_FORMATTER__",
        "style": {"fontSize": "24px"},
        "backgroundColor": ELEVATED_BG,
        "borderColor": INK_SOFT,
    },
    "plotOptions": {
        "bar": {
            "pointPadding": 0.1,
            "borderWidth": 0,
            "groupPadding": 0.1,
            "dataLabels": {
                "enabled": True,
                "style": {"fontSize": "22px", "fontWeight": "bold", "color": INK, "textOutline": "none"},
                "formatter": "__DATALABEL_FORMATTER__",
            },
        }
    },
    "series": [
        {
            "name": "Male",
            "data": male_values,
            "color": "#009E73",  # Okabe-Ito position 1
        },
        {
            "name": "Female",
            "data": female_values,
            "color": "#D55E00",  # Okabe-Ito position 2
        },
    ],
    "credits": {"enabled": False},
}

# Download Highcharts JS for inline embedding (required for headless Chrome)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
req = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

chart_options_json = json.dumps(chart_options)

chart_options_json = chart_options_json.replace(
    '"__FORMATTER_PLACEHOLDER__"', "function() { return Math.abs(this.value); }"
)
chart_options_json = chart_options_json.replace(
    '"__TOOLTIP_FORMATTER__"',
    """function() {
        return '<b>' + this.series.name + ', Age ' + this.point.category + '</b><br/>' +
               'Population: ' + Highcharts.numberFormat(Math.abs(this.point.y), 0) + ' Million';
    }""",
)
chart_options_json = chart_options_json.replace('"__DATALABEL_FORMATTER__"', "function() { return Math.abs(this.y); }")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
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
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
