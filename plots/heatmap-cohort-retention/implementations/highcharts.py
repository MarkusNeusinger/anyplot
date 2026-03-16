""" pyplots.ai
heatmap-cohort-retention: Cohort Retention Heatmap
Library: highcharts unknown | Python 3.14.3
Quality: 85/100 | Created: 2026-03-16
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Monthly signup cohorts with weekly retention
np.random.seed(42)
cohorts = [
    "Jan 2024",
    "Feb 2024",
    "Mar 2024",
    "Apr 2024",
    "May 2024",
    "Jun 2024",
    "Jul 2024",
    "Aug 2024",
    "Sep 2024",
    "Oct 2024",
]
num_cohorts = len(cohorts)
num_periods = 10

# Cohort sizes (number of signups per month)
cohort_sizes = [1240, 1385, 1520, 1190, 1450, 1680, 1310, 1575, 1420, 1290]

# Generate realistic retention curves with natural decay
# Period 0 is always 100%, then exponential-ish decay with noise
retention = np.zeros((num_cohorts, num_periods))
retention[:, 0] = 100.0

base_decay = np.array([1.0, 0.58, 0.45, 0.38, 0.33, 0.30, 0.27, 0.25, 0.23, 0.21])

for i in range(num_cohorts):
    cohort_quality = 1.0 + np.random.uniform(-0.08, 0.08)
    noise = np.random.normal(0, 0.02, num_periods)
    curve = base_decay * cohort_quality + noise
    curve[0] = 1.0
    curve = np.clip(curve, 0.05, 1.0)
    retention[i, :] = np.round(curve * 100, 1)

# Triangular shape: recent cohorts have fewer periods
# Cohort i (0-indexed) can have at most (num_periods - i) periods
heatmap_data = []
for row in range(num_cohorts):
    max_periods = num_periods - row
    for col in range(max_periods):
        heatmap_data.append([col, row, float(retention[row, col])])

# Y-axis labels with cohort sizes
y_labels = [f"{cohort} ({size:,})" for cohort, size in zip(cohorts, cohort_sizes, strict=True)]
x_labels = [f"Month {i}" for i in range(num_periods)]

# Chart configuration
chart_options = {
    "chart": {
        "type": "heatmap",
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#fafafa",
        "marginTop": 160,
        "marginBottom": 140,
        "marginLeft": 380,
        "marginRight": 340,
        "style": {"fontFamily": "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"},
    },
    "title": {
        "text": "heatmap-cohort-retention \u00b7 highcharts \u00b7 pyplots.ai",
        "style": {"fontSize": "48px", "fontWeight": "600", "color": "#2c3e50"},
        "y": 30,
    },
    "subtitle": {
        "text": "Monthly cohort retention rates \u2014 percentage of users returning each month after signup",
        "style": {"fontSize": "28px", "fontWeight": "normal", "color": "#7f8c8d"},
        "y": 72,
    },
    "xAxis": {
        "categories": x_labels,
        "title": {
            "text": "Months Since Signup",
            "style": {"fontSize": "30px", "fontWeight": "600", "color": "#34495e"},
            "margin": 16,
        },
        "labels": {"style": {"fontSize": "28px", "color": "#34495e"}, "y": 36},
        "lineWidth": 0,
        "tickLength": 0,
        "opposite": True,
    },
    "yAxis": {
        "categories": y_labels,
        "title": {
            "text": "Signup Cohort (Users)",
            "style": {"fontSize": "30px", "fontWeight": "600", "color": "#34495e"},
            "margin": 20,
        },
        "labels": {"style": {"fontSize": "26px", "color": "#34495e"}},
        "reversed": False,
        "lineWidth": 0,
        "gridLineWidth": 0,
    },
    "colorAxis": {
        "min": 0,
        "max": 100,
        "stops": [
            [0, "#f7fbff"],
            [0.15, "#d2e3f3"],
            [0.30, "#9ecae1"],
            [0.50, "#4292c6"],
            [0.70, "#2171b5"],
            [0.85, "#084594"],
            [1, "#042a5e"],
        ],
        "labels": {"style": {"fontSize": "24px", "color": "#34495e"}, "format": "{value}%"},
    },
    "legend": {
        "title": {"text": "Retention %", "style": {"fontSize": "26px", "fontWeight": "600", "color": "#34495e"}},
        "align": "right",
        "layout": "vertical",
        "verticalAlign": "middle",
        "symbolHeight": 800,
        "symbolWidth": 32,
        "itemStyle": {"fontSize": "22px", "color": "#34495e"},
        "x": -40,
        "margin": 30,
    },
    "tooltip": {
        "style": {"fontSize": "28px"},
        "headerFormat": "",
        "pointFormat": (
            "<b>{series.yAxis.categories.(point.y)}</b><br>{series.xAxis.categories.(point.x)}: <b>{point.value}%</b>"
        ),
    },
    "credits": {"enabled": False},
    "series": [
        {
            "type": "heatmap",
            "name": "Retention",
            "data": heatmap_data,
            "borderWidth": 3,
            "borderColor": "#fafafa",
            "dataLabels": {"enabled": True, "style": {"fontSize": "24px", "fontWeight": "bold", "textOutline": "none"}},
            "nullColor": "transparent",
        }
    ],
}

# Download Highcharts JS and heatmap module
js_urls = [
    ("https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"),
    ("https://code.highcharts.com/modules/heatmap.js", "https://cdn.jsdelivr.net/npm/highcharts@11/modules/heatmap.js"),
]
js_parts = []
for primary, fallback in js_urls:
    for url in (primary, fallback):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                js_parts.append(response.read().decode("utf-8"))
            break
        except Exception:
            continue
all_js = "\n".join(js_parts)

# Convert options to JSON
options_json = json.dumps(chart_options)

# Generate HTML with inline scripts and adaptive label colors
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{all_js}</script>
</head>
<body style="margin:0; padding:0; overflow:hidden; background:#fafafa;">
    <div id="container" style="width:4800px; height:2700px;"></div>
    <script>
        var opts = {options_json};
        opts.series[0].dataLabels.formatter = function() {{
            var v = this.point.value;
            var color = v > 45 ? '#ffffff' : '#1a1a1a';
            return '<span style="color:' + color + ';font-size:24px;font-weight:bold">' + v.toFixed(1) + '%</span>';
        }};
        opts.series[0].dataLabels.useHTML = true;
        Highcharts.chart('container', opts);
    </script>
</body>
</html>"""

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot using headless Chrome
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2840")
chrome_options.add_argument("--force-device-scale-factor=1")
chrome_options.add_argument("--hide-scrollbars")

driver = webdriver.Chrome(options=chrome_options)
driver.set_window_size(4800, 2840)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
