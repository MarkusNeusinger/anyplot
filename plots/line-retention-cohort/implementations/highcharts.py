""" pyplots.ai
line-retention-cohort: User Retention Curve by Cohort
Library: highcharts unknown | Python 3.14.3
Quality: 82/100 | Created: 2026-03-16
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Retention rates for 5 monthly signup cohorts over 12 weeks
np.random.seed(42)
weeks = list(range(13))
week_labels = [f"Week {w}" for w in weeks]

cohorts = {
    "Jan 2025": {"size": 1245, "decay": 0.18},
    "Feb 2025": {"size": 1102, "decay": 0.16},
    "Mar 2025": {"size": 1380, "decay": 0.14},
    "Apr 2025": {"size": 1510, "decay": 0.12},
    "May 2025": {"size": 1625, "decay": 0.10},
}

retention_data = {}
for cohort, info in cohorts.items():
    rates = [100.0]
    for w in range(1, 13):
        drop = info["decay"] * np.exp(-0.08 * w) + 0.02
        noise = np.random.uniform(-0.015, 0.015)
        rates.append(round(max(rates[-1] * (1 - drop - noise), 5), 1))
    retention_data[cohort] = rates

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 200,
    "marginLeft": 200,
    "marginRight": 180,
    "marginTop": 160,
}

chart.options.title = {
    "text": "line-retention-cohort \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

chart.options.subtitle = {
    "text": "User Retention by Monthly Signup Cohort",
    "style": {"fontSize": "32px", "color": "#666666"},
}

# X-axis
chart.options.x_axis = {
    "categories": week_labels,
    "title": {"text": "Weeks Since Signup", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 0,
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Retained Users (%)", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}, "format": "{value}%"},
    "min": 0,
    "max": 100,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.12)",
    "plotLines": [
        {
            "value": 20,
            "color": "#999999",
            "dashStyle": "Dash",
            "width": 3,
            "label": {
                "text": "20% Retention Target",
                "align": "right",
                "style": {"fontSize": "24px", "color": "#999999", "fontStyle": "italic"},
                "x": -20,
                "y": -12,
            },
        }
    ],
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "30px"},
    "symbolWidth": 80,
    "symbolHeight": 20,
    "layout": "vertical",
    "align": "right",
    "verticalAlign": "middle",
    "x": -30,
}

# Plot options
chart.options.plot_options = {
    "line": {"lineWidth": 5, "marker": {"enabled": True, "radius": 9, "lineWidth": 2, "lineColor": "#ffffff"}}
}

# Colors - cohesive palette starting with Python Blue, older cohorts lighter
colors = ["#a3c4d9", "#7baac4", "#5290ae", "#306998", "#1a4d6e"]

# Add series - older cohorts first (thinner), newest last (thickest)
for i, (cohort, rates) in enumerate(retention_data.items()):
    series = LineSeries()
    series.name = f"{cohort} (n={cohorts[cohort]['size']:,})"
    series.data = rates
    series.color = colors[i]
    series.line_width = 3 + i
    series.marker = {"radius": 5 + i}
    chart.add_series(series)

# Export
highcharts_url = "https://code.highcharts.com/highcharts.js"
req = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

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
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)
