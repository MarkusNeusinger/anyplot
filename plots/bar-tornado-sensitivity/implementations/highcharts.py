"""pyplots.ai
bar-tornado-sensitivity: Tornado Diagram for Sensitivity Analysis
Library: highcharts unknown | Python 3.14.3
Quality: 77/100 | Created: 2026-03-07
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import BarSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


# Data - NPV sensitivity analysis for a capital investment project
base_npv = 12.5  # Base case NPV in $M

parameters = [
    "Discount Rate",
    "Revenue Growth",
    "Material Cost",
    "Labor Cost",
    "Project Duration",
    "Tax Rate",
    "Salvage Value",
    "Inflation Rate",
    "Market Share",
    "Operating Expenses",
]

# Realistic sensitivity: some parameters have inverse effects
# Higher discount rate, costs, tax, duration → lower NPV (low scenario = higher NPV)
# Higher revenue, salvage, market share → higher NPV (low scenario = lower NPV)
low_values = [17.2, 9.2, 14.8, 14.0, 14.2, 13.8, 10.8, 13.2, 9.8, 14.5]
high_values = [8.1, 16.5, 10.3, 11.2, 11.0, 11.4, 13.9, 12.0, 15.5, 10.8]

# Sort by total range (widest bar first)
ranges = [abs(high_values[i] - low_values[i]) for i in range(len(parameters))]
sorted_indices = sorted(range(len(parameters)), key=lambda i: ranges[i], reverse=True)

sorted_params = [parameters[i] for i in sorted_indices]
sorted_low = [round(low_values[i] - base_npv, 1) for i in sorted_indices]
sorted_high = [round(high_values[i] - base_npv, 1) for i in sorted_indices]

# Build chart using highcharts_core
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "bar",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginLeft": 400,
    "marginRight": 120,
    "marginTop": 180,
    "marginBottom": 120,
    "style": {"fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"},
}

chart.options.title = {
    "text": "bar-tornado-sensitivity \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold", "color": "#222222"},
    "y": 40,
}

chart.options.subtitle = {
    "text": "NPV Sensitivity Analysis \u2014 Base Case: $12.5M",
    "style": {"fontSize": "32px", "color": "#555555"},
    "y": 90,
}

chart.options.x_axis = {
    "categories": sorted_params,
    "title": {"text": None},
    "labels": {"style": {"fontSize": "28px", "color": "#333333"}},
    "lineWidth": 0,
    "tickWidth": 0,
}

chart.options.y_axis = {
    "title": {"text": "Change in NPV ($M)", "style": {"fontSize": "28px", "color": "#333333"}, "margin": 20},
    "labels": {"style": {"fontSize": "24px", "color": "#555555"}, "format": "{value}"},
    "tickInterval": 1,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0,0,0,0.08)",
    "plotLines": [
        {
            "value": 0,
            "width": 3,
            "color": "#333333",
            "zIndex": 5,
            "label": {
                "text": "Base Case",
                "align": "right",
                "style": {"fontSize": "22px", "color": "#333333", "fontStyle": "italic"},
                "x": -10,
                "y": -10,
            },
        }
    ],
}

chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "28px", "color": "#333333"},
    "verticalAlign": "top",
    "layout": "horizontal",
    "align": "center",
    "y": 110,
    "floating": True,
    "symbolRadius": 4,
}

chart.options.credits = {"enabled": False}
chart.options.accessibility = {"enabled": False}

chart.options.tooltip = {
    "headerFormat": "<b>{point.key}</b><br/>",
    "pointFormat": "{series.name}: <b>{point.y:.1f} $M</b>",
    "style": {"fontSize": "22px"},
}

chart.options.plot_options = {
    "bar": {
        "grouping": False,
        "borderWidth": 0,
        "pointWidth": 80,
        "pointPadding": 0,
        "groupPadding": 0.15,
        "dataLabels": {
            "enabled": True,
            "format": "{y:.1f}",
            "style": {"fontSize": "22px", "fontWeight": "normal", "textOutline": "2px white", "color": "#333333"},
        },
    }
}

low_series = BarSeries()
low_series.name = "Low Scenario"
low_series.data = sorted_low
low_series.color = "#306998"

high_series = BarSeries()
high_series.name = "High Scenario"
high_series.data = sorted_high
high_series.color = "#FFD43B"

chart.add_series(low_series)
chart.add_series(high_series)

# Serialize via to_dict/JSON (avoids nested array data format from to_js_literal)
config_json = json.dumps(chart.options.to_dict())

# Download Highcharts JS for inline embedding (required for headless Chrome)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
req = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts (not CDN links)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; padding:0; background:#ffffff;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        Highcharts.chart('container', {config_json});
    }});
    </script>
</body>
</html>"""

# Save HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot with Selenium
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")
chrome_options.add_argument("--force-device-scale-factor=1")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

container = driver.find_element(By.ID, "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
