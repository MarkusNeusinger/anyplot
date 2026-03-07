"""pyplots.ai
bar-tornado-sensitivity: Tornado Diagram for Sensitivity Analysis
Library: highcharts unknown | Python 3.14.3
Quality: 85/100 | Created: 2026-03-07
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

# Color palette
color_low = "#306998"
color_high = "#E8A838"
color_top_low = "#1A4570"
color_top_high = "#D4880A"

chart.options.chart = {
    "type": "bar",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginLeft": 420,
    "marginRight": 140,
    "marginTop": 240,
    "marginBottom": 180,
    "style": {"fontFamily": "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"},
    "plotBackgroundColor": "#f8f9fa",
}

chart.options.title = {
    "text": "bar-tornado-sensitivity \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "700", "color": "#1a1a2e", "letterSpacing": "0.5px"},
    "y": 45,
}

chart.options.subtitle = {
    "text": "NPV Sensitivity Analysis \u2014 Base Case: $12.5M",
    "style": {"fontSize": "34px", "fontWeight": "400", "color": "#555555"},
    "y": 100,
}

chart.options.x_axis = {
    "categories": sorted_params,
    "title": {"text": None},
    "labels": {"style": {"fontSize": "30px", "color": "#2a2a2a", "fontWeight": "500"}},
    "lineWidth": 0,
    "tickWidth": 0,
}

chart.options.y_axis = {
    "title": {
        "text": "Change in NPV ($M)",
        "style": {"fontSize": "30px", "color": "#333333", "fontWeight": "600"},
        "margin": 35,
    },
    "labels": {"style": {"fontSize": "26px", "color": "#555555"}, "format": "{value}"},
    "tickInterval": 1,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0,0,0,0.06)",
    "gridLineDashStyle": "Dot",
    "plotLines": [
        {
            "value": 0,
            "width": 4,
            "color": "#1a1a2e",
            "zIndex": 5,
            "label": {
                "text": "Base Case",
                "align": "center",
                "verticalAlign": "bottom",
                "rotation": 0,
                "style": {"fontSize": "24px", "fontWeight": "bold", "color": "#1a1a2e"},
                "y": -20,
            },
        }
    ],
}

chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "30px", "fontWeight": "500", "color": "#333333"},
    "verticalAlign": "top",
    "layout": "horizontal",
    "align": "center",
    "y": 140,
    "floating": True,
    "symbolRadius": 6,
    "symbolHeight": 18,
    "symbolWidth": 18,
    "itemDistance": 50,
}

chart.options.credits = {"enabled": False}
chart.options.accessibility = {"enabled": False}

chart.options.tooltip = {
    "headerFormat": "<b>{point.key}</b><br/>",
    "pointFormat": "{series.name}: <b>{point.y:.1f} $M</b>",
    "style": {"fontSize": "24px"},
}

chart.options.plot_options = {
    "bar": {
        "grouping": True,
        "borderWidth": 0,
        "pointPadding": 0.05,
        "groupPadding": 0.12,
        "borderRadius": 3,
        "dataLabels": {
            "enabled": True,
            "format": "{y:.1f}",
            "style": {"fontSize": "26px", "fontWeight": "600", "textOutline": "3px white", "color": "#2a2a2a"},
        },
    }
}

# Create data with emphasis on top parameter (darker color)
low_data = [{"y": sorted_low[0], "color": color_top_low}, *[{"y": v} for v in sorted_low[1:]]]
high_data = [{"y": sorted_high[0], "color": color_top_high}, *[{"y": v} for v in sorted_high[1:]]]

low_series = BarSeries()
low_series.name = "Low Scenario"
low_series.data = low_data
low_series.color = color_low

high_series = BarSeries()
high_series.name = "High Scenario"
high_series.data = high_data
high_series.color = color_high

chart.add_series(low_series)
chart.add_series(high_series)

# Serialize via to_dict/JSON for reliable rendering in headless Chrome
config_json = json.dumps(chart.options.to_dict())

# Download Highcharts JS for inline embedding (required for headless Chrome)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
req = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
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

driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 4800, "height": 2700, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(1)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
