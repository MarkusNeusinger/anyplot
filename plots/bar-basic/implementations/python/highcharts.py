""" pyplots.ai
bar-basic: Basic Bar Chart
Library: highcharts 1.10.3 | Python 3.14
Quality: 94/100 | Created: 2025-12-23
"""

import re
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.annotations import Annotation
from highcharts_core.options.series.bar import ColumnSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Product sales by category (realistic retail scenario, sorted descending)
categories = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books", "Toys"]
values = [4800, 3100, 2200, 1700, 950, 480]
avg_sales = sum(values) / len(values)

# Build chart using highcharts-core Python API
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "column",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 280,
    "marginTop": 140,
    "marginLeft": 220,
    "marginRight": 200,
    "style": {"fontFamily": "Arial, Helvetica, sans-serif"},
}

# Title
chart.options.title = {
    "text": "bar-basic \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "52px", "fontWeight": "bold", "color": "#2c3e50"},
    "margin": 50,
}

# Subtitle for storytelling context
chart.options.subtitle = {
    "text": "Electronics dominates with 4,800 units \u2014 10\u00d7 more than Toys",
    "style": {"fontSize": "32px", "color": "#7f8c8d", "fontWeight": "normal"},
    "margin": 30,
}

# X-axis
chart.options.x_axis = {
    "categories": categories,
    "title": {"text": "Product Category", "style": {"fontSize": "36px", "color": "#555555"}, "margin": 20},
    "labels": {"style": {"fontSize": "30px", "color": "#555555"}},
    "lineColor": "#cccccc",
    "tickColor": "#cccccc",
    "tickLength": 8,
}

# Y-axis with plotLine showing average
chart.options.y_axis = {
    "title": {"text": "Sales (Units)", "style": {"fontSize": "36px", "color": "#555555"}, "margin": 15},
    "labels": {"style": {"fontSize": "28px", "color": "#555555"}, "format": "{value:,.0f}"},
    "max": 5200,
    "endOnTick": False,
    "tickInterval": 1000,
    "gridLineColor": "#e8e8e8",
    "gridLineWidth": 1,
    "gridLineDashStyle": "Dot",
    "plotLines": [
        {
            "value": avg_sales,
            "color": "#e74c3c",
            "width": 3,
            "dashStyle": "LongDash",
            "zIndex": 5,
            "label": {
                "text": f"Average: {avg_sales:,.0f} units",
                "align": "right",
                "x": -30,
                "y": -14,
                "style": {"fontSize": "26px", "color": "#e74c3c", "fontWeight": "bold", "fontStyle": "italic"},
            },
        }
    ],
}

# Tooltip with custom formatting
chart.options.tooltip = {
    "headerFormat": '<span style="font-size:24px;font-weight:bold">{point.key}</span><br/>',
    "pointFormat": '<span style="font-size:22px">Sales: <b>{point.y:,.0f}</b> units</span>',
    "backgroundColor": "rgba(255, 255, 255, 0.95)",
    "borderColor": "#306998",
    "borderRadius": 8,
    "borderWidth": 2,
    "shadow": {"color": "rgba(0,0,0,0.1)", "offsetX": 1, "offsetY": 2, "width": 3},
    "style": {"fontSize": "22px"},
}

# Plot options for column styling
chart.options.plot_options = {
    "column": {
        "pointPadding": 0.12,
        "borderWidth": 0,
        "groupPadding": 0.08,
        "borderRadius": 6,
        "shadow": {"color": "rgba(0,0,0,0.08)", "offsetX": 2, "offsetY": 3, "width": 5},
    }
}

# Highlight top performer with darker shade, rest with standard Python Blue
data_points = [
    {"y": values[0], "color": "#1a4971"}  # Darker shade for top performer
]
for v in values[1:]:
    data_points.append({"y": v, "color": "#306998"})

# Create series using highcharts-core ColumnSeries
series = ColumnSeries.from_dict(
    {
        "data": data_points,
        "name": "Sales",
        "type": "column",
        "dataLabels": {
            "enabled": True,
            "format": "{y:,.0f}",
            "style": {"fontSize": "28px", "fontWeight": "bold", "color": "#2c3e50", "textOutline": "2px white"},
            "y": -8,
        },
    }
)
chart.add_series(series)

# Annotation callout on top performer
chart.options.annotations = [
    Annotation.from_dict(
        {
            "labels": [
                {
                    "point": {"x": 0, "y": 4800, "xAxis": 0, "yAxis": 0},
                    "text": "\u2b50 Top Seller",
                    "y": -45,
                    "style": {"fontSize": "26px", "fontWeight": "bold", "color": "#1a4971"},
                }
            ],
            "labelOptions": {
                "backgroundColor": "rgba(255, 255, 255, 0.92)",
                "borderColor": "#1a4971",
                "borderWidth": 2,
                "borderRadius": 8,
                "padding": 12,
                "shape": "callout",
            },
            "draggable": "",
        }
    )
]

# Disable legend (single series) and credits
chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}

# Download Highcharts JS for inline embedding (required for headless Chrome)
highcharts_url = "https://code.highcharts.com/highcharts.js"
annotations_url = "https://code.highcharts.com/modules/annotations.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")
with urllib.request.urlopen(annotations_url, timeout=30) as response:
    annotations_js = response.read().decode("utf-8")

# Generate HTML using Chart.to_js_literal()
chart_js = chart.to_js_literal()
# Fix format strings: highcharts-core omits quotes around Highcharts format templates
chart_js = re.sub(r"format: (\{[^}]+\})", r"format: '\1'", chart_js)

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{annotations_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{chart_js}</script>
</body>
</html>"""

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save HTML for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with headless Chrome
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

# Clean up temp file
Path(temp_path).unlink()
