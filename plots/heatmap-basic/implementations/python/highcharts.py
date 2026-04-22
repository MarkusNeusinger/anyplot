""" pyplots.ai
heatmap-basic: Basic Heatmap
Library: highcharts 1.10.3 | Python 3.14.3
Quality: 93/100 | Updated: 2026-02-16
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Website traffic by day and time period (8x7 matrix)
np.random.seed(42)
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
time_periods = ["6–9 AM", "9 AM–Noon", "Noon–3 PM", "3–6 PM", "6–9 PM", "9 PM–Mid", "Mid–3 AM", "3–6 AM"]

# Generate realistic traffic patterns (visits per hour)
base = np.random.randint(15, 55, size=(len(time_periods), len(days))).astype(float)

# Shape traffic by time-of-day multipliers applied to all days
multipliers = np.array([1.3, 2.0, 2.0, 2.0, 1.0, 0.6, 0.25, 0.25]).reshape(-1, 1)
base *= multipliers

# Reduce weekday peaks for weekends, boost weekend evenings
base[0:4, 5:7] *= 0.5  # weekend daytime + morning lower
base[4:6, 5:7] *= 1.5  # weekend evenings higher

# Clamp to realistic visit range
traffic = np.clip(base, 0, 100).astype(int)

# Build heatmap data in Highcharts format: [x_index, y_index, value]
heatmap_data = []
for y_idx in range(len(time_periods)):
    for x_idx in range(len(days)):
        heatmap_data.append([x_idx, y_idx, int(traffic[y_idx, x_idx])])

# Chart configuration
chart_options = {
    "chart": {
        "type": "heatmap",
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#fafafa",
        "marginTop": 180,
        "marginBottom": 180,
        "marginRight": 380,
        "marginLeft": 300,
        "style": {"fontFamily": "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"},
    },
    "title": {
        "text": "Website Traffic · heatmap-basic · highcharts · pyplots.ai",
        "style": {"fontSize": "52px", "fontWeight": "600", "color": "#2c3e50"},
        "y": 30,
    },
    "subtitle": {
        "text": "Visits per hour — weekday business hours show clear peak activity",
        "style": {"fontSize": "30px", "fontWeight": "normal", "color": "#7f8c8d"},
        "y": 75,
    },
    "xAxis": {
        "categories": days,
        "title": {
            "text": "Day of Week",
            "style": {"fontSize": "32px", "fontWeight": "600", "color": "#34495e"},
            "margin": 16,
        },
        "labels": {"style": {"fontSize": "34px", "color": "#34495e"}, "y": 40},
        "lineWidth": 0,
        "tickLength": 0,
    },
    "yAxis": {
        "categories": time_periods,
        "title": {
            "text": "Time Period",
            "style": {"fontSize": "32px", "fontWeight": "600", "color": "#34495e"},
            "margin": 16,
        },
        "labels": {"style": {"fontSize": "30px", "color": "#34495e"}},
        "reversed": True,
        "lineWidth": 0,
        "gridLineWidth": 0,
    },
    "colorAxis": {
        "min": 0,
        "max": 100,
        "stops": [
            [0, "#ffffcc"],
            [0.15, "#ffeda0"],
            [0.30, "#fed976"],
            [0.45, "#feb24c"],
            [0.60, "#fd8d3c"],
            [0.75, "#f03b20"],
            [1, "#bd0026"],
        ],
        "labels": {"style": {"fontSize": "26px", "color": "#34495e"}},
    },
    "legend": {
        "title": {"text": "Visits / hr", "style": {"fontSize": "28px", "fontWeight": "600", "color": "#34495e"}},
        "align": "right",
        "layout": "vertical",
        "verticalAlign": "middle",
        "symbolHeight": 900,
        "symbolWidth": 36,
        "itemStyle": {"fontSize": "24px", "color": "#34495e"},
        "x": -60,
        "margin": 40,
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
            "borderColor": "#fafafa",
            "dataLabels": {"enabled": True, "style": {"fontSize": "28px", "fontWeight": "bold", "textOutline": "none"}},
        }
    ],
}

# Download Highcharts JS and heatmap module
highcharts_url = "https://code.highcharts.com/highcharts.js"
heatmap_url = "https://code.highcharts.com/modules/heatmap.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(heatmap_url, timeout=30) as response:
    heatmap_js = response.read().decode("utf-8")

# Convert options to JSON
options_json = json.dumps(chart_options)

# Generate HTML with inline scripts and adaptive label colors
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="margin:0; padding:0; overflow:hidden; background:#fafafa;">
    <div id="container" style="width:4800px; height:2700px;"></div>
    <script>
        var opts = {options_json};
        opts.series[0].dataLabels.formatter = function() {{
            var v = this.point.value;
            var color = v > 55 ? '#ffffff' : '#333333';
            return '<span style="color:' + color + ';font-size:28px;font-weight:bold">' + v + '</span>';
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
