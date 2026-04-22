""" pyplots.ai
pie-portfolio-interactive: Interactive Portfolio Allocation Chart
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.pie import PieSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Portfolio allocation with drill-down structure
# Main categories (asset classes)
portfolio_data = [
    {"name": "Equities", "y": 55.0, "drilldown": "equities", "color": "#306998"},
    {"name": "Fixed Income", "y": 25.0, "drilldown": "fixed-income", "color": "#FFD43B"},
    {"name": "Alternatives", "y": 12.0, "drilldown": "alternatives", "color": "#9467BD"},
    {"name": "Cash", "y": 8.0, "drilldown": "cash", "color": "#17BECF"},
]

# Drill-down data (sub-holdings within each asset class)
drilldown_series = [
    {
        "type": "pie",
        "id": "equities",
        "name": "Equities",
        "data": [
            ["Apple Inc.", 12.0],
            ["Microsoft Corp.", 10.0],
            ["Amazon.com", 8.0],
            ["Alphabet Inc.", 7.0],
            ["Tesla Inc.", 6.0],
            ["NVIDIA Corp.", 5.0],
            ["Other Equities", 7.0],
        ],
    },
    {
        "type": "pie",
        "id": "fixed-income",
        "name": "Fixed Income",
        "data": [
            ["US Treasury 10Y", 10.0],
            ["Corporate Bonds AAA", 7.0],
            ["Municipal Bonds", 5.0],
            ["High Yield Bonds", 3.0],
        ],
    },
    {
        "type": "pie",
        "id": "alternatives",
        "name": "Alternatives",
        "data": [["Real Estate (REITs)", 5.0], ["Commodities (Gold)", 4.0], ["Private Equity", 3.0]],
    },
    {"type": "pie", "id": "cash", "name": "Cash", "data": [["Money Market Fund", 5.0], ["Savings Account", 3.0]]},
]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {"type": "pie", "width": 4800, "height": 2700, "backgroundColor": "#ffffff"}

# Title
chart.options.title = {
    "text": "pie-portfolio-interactive \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

chart.options.subtitle = {"text": "Click slices to view individual holdings", "style": {"fontSize": "28px"}}

# Tooltip
chart.options.tooltip = {
    "headerFormat": '<span style="font-size: 24px">{series.name}</span><br>',
    "pointFormat": '<span style="color:{point.color}">\u25cf</span> {point.name}: <b>{point.y:.1f}%</b><br/>',
    "style": {"fontSize": "22px"},
}

# Accessibility
chart.options.accessibility = {"announceNewData": {"enabled": True}, "point": {"valueSuffix": "%"}}

# Plot options
chart.options.plot_options = {
    "pie": {
        "allowPointSelect": True,
        "cursor": "pointer",
        "innerSize": "50%",
        "dataLabels": {
            "enabled": True,
            "format": "<b>{point.name}</b>: {point.percentage:.1f}%",
            "style": {"fontSize": "24px", "fontWeight": "normal"},
            "distance": 30,
        },
        "showInLegend": True,
    }
}

# Legend
chart.options.legend = {
    "enabled": True,
    "layout": "vertical",
    "align": "right",
    "verticalAlign": "middle",
    "itemStyle": {"fontSize": "24px"},
    "itemMarginBottom": 10,
}

# Drilldown configuration
chart.options.drilldown = {
    "activeAxisLabelStyle": {"textDecoration": "none", "fontStyle": "normal"},
    "activeDataLabelStyle": {"textDecoration": "none", "fontStyle": "normal"},
    "breadcrumbs": {"position": {"align": "right"}, "style": {"fontSize": "24px"}},
    "series": drilldown_series,
}

# Create main series
series = PieSeries()
series.name = "Asset Classes"
series.data = portfolio_data
series.color_by_point = True

chart.add_series(series)

# Download Highcharts JS and drilldown module
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

drilldown_url = "https://code.highcharts.com/modules/drilldown.js"
with urllib.request.urlopen(drilldown_url, timeout=30) as response:
    drilldown_js = response.read().decode("utf-8")

accessibility_url = "https://code.highcharts.com/modules/accessibility.js"
with urllib.request.urlopen(accessibility_url, timeout=30) as response:
    accessibility_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{drilldown_js}</script>
    <script>{accessibility_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save the HTML for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Setup headless Chrome
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
