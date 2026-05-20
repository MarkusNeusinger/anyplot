""" anyplot.ai
bar-drilldown: Column Chart with Hierarchical Drilling
Library: highcharts unknown | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-20
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import ColumnSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

# Download Highcharts JS and drilldown module (inline required for headless Chrome)
highcharts_url = "https://unpkg.com/highcharts/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=60) as response:
    highcharts_js = response.read().decode("utf-8")

drilldown_url = "https://unpkg.com/highcharts/modules/drilldown.js"
with urllib.request.urlopen(drilldown_url, timeout=60) as response:
    drilldown_js = response.read().decode("utf-8")

# Build chart using highcharts-core Python API
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "column",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "marginBottom": 220,
    "style": {"color": INK},
}

chart.options.title = {
    "text": "bar-drilldown · python · highcharts · anyplot.ai",
    "style": {"fontSize": "66px", "color": INK, "fontWeight": "bold"},
}

chart.options.subtitle = {
    "text": "Sales Revenue by Region — Click columns to drill down",
    "style": {"fontSize": "44px", "color": INK_SOFT},
}

chart.options.x_axis = {
    "type": "category",
    "title": {"text": "Region", "style": {"fontSize": "56px", "color": INK}, "margin": 30},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
}

chart.options.y_axis = {
    "title": {"text": "Revenue ($M)", "style": {"fontSize": "56px", "color": INK}},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}, "format": "${value}M"},
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}
chart.options.colors = OKABE_ITO

chart.options.tooltip = {
    "headerFormat": '<span style="font-size: 44px; font-weight: bold">{series.name}</span><br>',
    "pointFormat": ('<span style="font-size: 40px">{point.name}</span>: <b style="font-size: 40px">${point.y}M</b>'),
}

chart.options.plot_options = {
    "column": {
        "borderRadius": 6,
        "cursor": "pointer",
        "dataLabels": {
            "enabled": True,
            "format": "${y}M",
            "style": {"fontSize": "40px", "fontWeight": "bold", "textOutline": f"2px {PAGE_BG}"},
        },
        "colorByPoint": True,
    },
    "series": {"borderWidth": 0},
}

# Main series: 5 regions (Level 1)
top_series = ColumnSeries()
top_series.name = "Regions"
top_series.data = [
    {"name": "North America", "y": 245, "drilldown": "north-america"},
    {"name": "Europe", "y": 198, "drilldown": "europe"},
    {"name": "Asia Pacific", "y": 176, "drilldown": "asia-pacific"},
    {"name": "Latin America", "y": 87, "drilldown": "latin-america"},
    {"name": "Middle East", "y": 54, "drilldown": "middle-east"},
]
chart.add_series(top_series)

# Drilldown: Level 2 (countries) and Level 3 (cities)
chart.options.drilldown = {
    "breadcrumbs": {
        "position": {"align": "right"},
        "style": {"fontSize": "40px", "color": INK_SOFT},
        "buttonTheme": {"style": {"fontSize": "40px", "fontWeight": "bold", "color": INK}},
        "showFullPath": True,
    },
    "activeAxisLabelStyle": {"textDecoration": "none", "fontStyle": "normal", "fontSize": "44px", "color": INK_SOFT},
    "activeDataLabelStyle": {"textDecoration": "none", "fontStyle": "normal", "fontSize": "40px", "color": INK},
    "series": [
        # Level 2: Countries within each region
        {
            "type": "column",
            "id": "north-america",
            "name": "North America",
            "data": [
                {"name": "United States", "y": 185, "drilldown": "usa"},
                {"name": "Canada", "y": 42, "drilldown": "canada"},
                {"name": "Mexico", "y": 18, "drilldown": "mexico"},
            ],
        },
        {
            "type": "column",
            "id": "europe",
            "name": "Europe",
            "data": [
                {"name": "United Kingdom", "y": 52, "drilldown": "uk"},
                {"name": "Germany", "y": 48, "drilldown": "germany"},
                {"name": "France", "y": 41, "drilldown": "france"},
                {"name": "Italy", "y": 32, "drilldown": "italy"},
                {"name": "Spain", "y": 25, "drilldown": "spain"},
            ],
        },
        {
            "type": "column",
            "id": "asia-pacific",
            "name": "Asia Pacific",
            "data": [
                {"name": "Japan", "y": 58, "drilldown": "japan"},
                {"name": "Australia", "y": 45, "drilldown": "australia"},
                {"name": "South Korea", "y": 38, "drilldown": "south-korea"},
                {"name": "Singapore", "y": 35, "drilldown": "singapore"},
            ],
        },
        {
            "type": "column",
            "id": "latin-america",
            "name": "Latin America",
            "data": [
                {"name": "Brazil", "y": 45, "drilldown": "brazil"},
                {"name": "Argentina", "y": 22, "drilldown": "argentina"},
                {"name": "Chile", "y": 20, "drilldown": "chile"},
            ],
        },
        {
            "type": "column",
            "id": "middle-east",
            "name": "Middle East",
            "data": [
                {"name": "UAE", "y": 28, "drilldown": "uae"},
                {"name": "Saudi Arabia", "y": 18, "drilldown": "saudi-arabia"},
                {"name": "Israel", "y": 8, "drilldown": "israel"},
            ],
        },
        # Level 3: Cities within countries
        {
            "type": "column",
            "id": "usa",
            "name": "United States",
            "data": [
                ["New York", 52],
                ["Los Angeles", 38],
                ["Chicago", 28],
                ["Houston", 24],
                ["Phoenix", 22],
                ["Other", 21],
            ],
        },
        {
            "type": "column",
            "id": "canada",
            "name": "Canada",
            "data": [["Toronto", 18], ["Vancouver", 12], ["Montreal", 8], ["Calgary", 4]],
        },
        {
            "type": "column",
            "id": "mexico",
            "name": "Mexico",
            "data": [["Mexico City", 10], ["Guadalajara", 5], ["Monterrey", 3]],
        },
        {
            "type": "column",
            "id": "uk",
            "name": "United Kingdom",
            "data": [["London", 32], ["Manchester", 10], ["Birmingham", 6], ["Edinburgh", 4]],
        },
        {
            "type": "column",
            "id": "germany",
            "name": "Germany",
            "data": [["Berlin", 15], ["Munich", 14], ["Frankfurt", 12], ["Hamburg", 7]],
        },
        {
            "type": "column",
            "id": "france",
            "name": "France",
            "data": [["Paris", 25], ["Lyon", 8], ["Marseille", 5], ["Nice", 3]],
        },
        {
            "type": "column",
            "id": "italy",
            "name": "Italy",
            "data": [["Milan", 15], ["Rome", 10], ["Turin", 4], ["Florence", 3]],
        },
        {"type": "column", "id": "spain", "name": "Spain", "data": [["Madrid", 12], ["Barcelona", 9], ["Valencia", 4]]},
        {
            "type": "column",
            "id": "japan",
            "name": "Japan",
            "data": [["Tokyo", 32], ["Osaka", 14], ["Nagoya", 8], ["Fukuoka", 4]],
        },
        {
            "type": "column",
            "id": "australia",
            "name": "Australia",
            "data": [["Sydney", 20], ["Melbourne", 15], ["Brisbane", 6], ["Perth", 4]],
        },
        {
            "type": "column",
            "id": "south-korea",
            "name": "South Korea",
            "data": [["Seoul", 28], ["Busan", 6], ["Incheon", 4]],
        },
        {
            "type": "column",
            "id": "singapore",
            "name": "Singapore",
            "data": [["Central", 18], ["East", 10], ["West", 7]],
        },
        {
            "type": "column",
            "id": "brazil",
            "name": "Brazil",
            "data": [["Sao Paulo", 25], ["Rio de Janeiro", 12], ["Brasilia", 5], ["Salvador", 3]],
        },
        {
            "type": "column",
            "id": "argentina",
            "name": "Argentina",
            "data": [["Buenos Aires", 16], ["Cordoba", 4], ["Rosario", 2]],
        },
        {
            "type": "column",
            "id": "chile",
            "name": "Chile",
            "data": [["Santiago", 15], ["Valparaiso", 3], ["Concepcion", 2]],
        },
        {"type": "column", "id": "uae", "name": "UAE", "data": [["Dubai", 18], ["Abu Dhabi", 8], ["Sharjah", 2]]},
        {
            "type": "column",
            "id": "saudi-arabia",
            "name": "Saudi Arabia",
            "data": [["Riyadh", 10], ["Jeddah", 6], ["Dammam", 2]],
        },
        {"type": "column", "id": "israel", "name": "Israel", "data": [["Tel Aviv", 5], ["Jerusalem", 2], ["Haifa", 1]]},
    ],
}

# Generate HTML with inline scripts (CDN won't load from file:// in headless Chrome)
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{drilldown_js}</script>
</head>
<body style="margin:0; padding:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and screenshot for PNG artifact
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=3200,1800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
