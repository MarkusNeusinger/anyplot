""" pyplots.ai
heatmap-cohort-retention: Cohort Retention Heatmap
Library: highcharts unknown | Python 3.14.3
Quality: 90/100 | Created: 2026-03-16
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Monthly signup cohorts with realistic retention variation
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

# Cohort sizes - varied to reflect marketing pushes
cohort_sizes = [1240, 1385, 1520, 1190, 1450, 1680, 1310, 1575, 1420, 1290]

# Generate differentiated retention curves to tell a story:
# - Jun 2024 (idx 5): best cohort — new onboarding flow launched
# - Apr 2024 (idx 3): worst cohort — buggy release hurt retention
# - Others vary moderately
retention = np.zeros((num_cohorts, num_periods))
retention[:, 0] = 100.0

base_decay = np.array([1.0, 0.58, 0.45, 0.38, 0.33, 0.30, 0.27, 0.25, 0.23, 0.21])

# Per-cohort quality multipliers for storytelling
cohort_multipliers = [1.0, 0.98, 1.04, 0.82, 0.95, 1.18, 1.06, 1.02, 1.10, 1.05]

for i in range(num_cohorts):
    noise = np.random.normal(0, 0.015, num_periods)
    curve = base_decay * cohort_multipliers[i] + noise
    curve[0] = 1.0
    curve = np.clip(curve, 0.05, 1.0)
    retention[i, :] = np.round(curve * 100, 1)

# Triangular shape: recent cohorts have fewer periods
heatmap_data = []
for row in range(num_cohorts):
    max_periods = num_periods - row
    for col in range(max_periods):
        heatmap_data.append([col, row, float(retention[row, col])])

# Y-axis labels with cohort sizes
y_labels = [f"{cohort} ({size:,})" for cohort, size in zip(cohorts, cohort_sizes, strict=True)]
x_labels = [f"Month {i}" for i in range(num_periods)]

# Find best and worst cohorts for storytelling emphasis
best_cohort_idx = 5  # Jun 2024 - new onboarding
worst_cohort_idx = 3  # Apr 2024 - buggy release

# Chart configuration
chart_options = {
    "chart": {
        "type": "heatmap",
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#fafafa",
        "marginTop": 260,
        "marginBottom": 100,
        "marginLeft": 400,
        "marginRight": 280,
        "style": {"fontFamily": "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"},
    },
    "title": {
        "text": "heatmap-cohort-retention \u00b7 highcharts \u00b7 pyplots.ai",
        "style": {"fontSize": "48px", "fontWeight": "700", "color": "#1a2634"},
        "y": 28,
    },
    "subtitle": {
        "text": "Monthly cohort retention rates \u2014 percentage of users returning each month after signup<br/>"
        '<span style="font-size:22px;color:#084594;">\u2605 Best: Jun 2024 (new onboarding)</span>'
        "&nbsp;&nbsp;&nbsp;"
        '<span style="font-size:22px;color:#c0392b;">Apr 2024: lowest retention (buggy release)</span>',
        "style": {"fontSize": "26px", "fontWeight": "normal", "color": "#7f8c8d"},
        "useHTML": True,
        "y": 78,
    },
    "xAxis": {
        "categories": x_labels,
        "title": {
            "text": "Months Since Signup",
            "style": {"fontSize": "28px", "fontWeight": "600", "color": "#34495e"},
            "margin": 20,
            "y": -8,
        },
        "labels": {"style": {"fontSize": "26px", "color": "#34495e"}, "y": 32},
        "lineWidth": 0,
        "tickLength": 0,
        "opposite": True,
        "offset": 30,
    },
    "yAxis": {
        "categories": y_labels,
        "title": {
            "text": "Signup Cohort (Users)",
            "style": {"fontSize": "28px", "fontWeight": "600", "color": "#34495e"},
            "margin": 20,
        },
        "labels": {"style": {"fontSize": "24px", "color": "#34495e"}},
        "reversed": False,
        "lineWidth": 0,
        "gridLineWidth": 0,
    },
    "colorAxis": {
        "min": 0,
        "max": 100,
        "stops": [
            [0, "#f7fbff"],
            [0.12, "#deebf7"],
            [0.25, "#9ecae1"],
            [0.40, "#4292c6"],
            [0.55, "#2171b5"],
            [0.70, "#08519c"],
            [0.85, "#084594"],
            [1, "#042a5e"],
        ],
        "labels": {"style": {"fontSize": "22px", "color": "#34495e"}, "format": "{value}%"},
    },
    "legend": {
        "title": {"text": "Retention %", "style": {"fontSize": "24px", "fontWeight": "600", "color": "#34495e"}},
        "align": "right",
        "layout": "vertical",
        "verticalAlign": "middle",
        "symbolHeight": 700,
        "symbolWidth": 28,
        "itemStyle": {"fontSize": "20px", "color": "#34495e"},
        "x": -20,
        "margin": 20,
    },
    "tooltip": {
        "style": {"fontSize": "26px"},
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
        // Adaptive data label colors based on cell value
        opts.series[0].dataLabels.formatter = function() {{
            var v = this.point.value;
            var color = v > 45 ? '#ffffff' : '#1a1a1a';
            return '<span style="color:' + color + ';font-size:24px;font-weight:bold">' + v.toFixed(1) + '%</span>';
        }};
        opts.series[0].dataLabels.useHTML = true;
        // Highlight best/worst cohort y-axis labels
        opts.yAxis.labels.formatter = function() {{
            var val = this.value;
            if (this.pos === {best_cohort_idx}) {{
                return '<span style="color:#084594;font-weight:bold;font-size:26px">\u2605 ' + val + '</span>';
            }} else if (this.pos === {worst_cohort_idx}) {{
                return '<span style="color:#c0392b;font-size:24px">' + val + '</span>';
            }}
            return '<span style="font-size:24px">' + val + '</span>';
        }};
        opts.yAxis.labels.useHTML = true;
        // Add plotBands for best/worst cohort rows
        opts.yAxis.plotBands = [
            {{from: {best_cohort_idx} - 0.5, to: {best_cohort_idx} + 0.5, color: 'rgba(8,69,148,0.06)'}},
            {{from: {worst_cohort_idx} - 0.5, to: {worst_cohort_idx} + 0.5, color: 'rgba(192,57,43,0.06)'}}
        ];
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
