""" pyplots.ai
sunburst-basic: Basic Sunburst Chart
Library: highcharts unknown | Python 3.13.11
Quality: 90/100 | Created: 2025-12-23
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Budget breakdown by department, team, and project
# Using a hierarchical structure with ids for parent references
# Values show significant variation to demonstrate proportional representation
data = [
    # Level 1: Departments (innermost ring)
    {"id": "engineering", "name": "Engineering", "color": "#306998"},
    {"id": "marketing", "name": "Marketing", "color": "#FFD43B"},
    {"id": "operations", "name": "Operations", "color": "#9467BD"},
    # Level 2: Teams - varied sizes
    {"id": "frontend", "name": "Frontend", "parent": "engineering", "value": 280},
    {"id": "backend", "name": "Backend", "parent": "engineering", "value": 350},
    {"id": "devops", "name": "DevOps", "parent": "engineering", "value": 90},
    {"id": "digital", "name": "Digital", "parent": "marketing", "value": 200},
    {"id": "content", "name": "Content", "parent": "marketing", "value": 70},
    {"id": "brand", "name": "Brand", "parent": "marketing", "value": 40},
    {"id": "hr", "name": "HR", "parent": "operations", "value": 60},
    {"id": "finance", "name": "Finance", "parent": "operations", "value": 120},
    {"id": "facilities", "name": "Facilities", "parent": "operations", "value": 30},
    # Level 3: Projects (outermost ring) - significant variation in sizes
    {"name": "React App", "parent": "frontend", "value": 150},
    {"name": "Mobile UI", "parent": "frontend", "value": 90},
    {"name": "Design System", "parent": "frontend", "value": 40},
    {"name": "API v2", "parent": "backend", "value": 180},
    {"name": "Database", "parent": "backend", "value": 120},
    {"name": "Microservices", "parent": "backend", "value": 50},
    {"name": "CI/CD", "parent": "devops", "value": 50},
    {"name": "Cloud Infra", "parent": "devops", "value": 40},
    {"name": "SEO", "parent": "digital", "value": 40},
    {"name": "Social Ads", "parent": "digital", "value": 120},
    {"name": "PPC", "parent": "digital", "value": 40},
    {"name": "Blog", "parent": "content", "value": 45},
    {"name": "Videos", "parent": "content", "value": 25},
    {"name": "Rebrand", "parent": "brand", "value": 25},
    {"name": "Guidelines", "parent": "brand", "value": 15},
    {"name": "Recruiting", "parent": "hr", "value": 40},
    {"name": "Training", "parent": "hr", "value": 20},
    {"name": "Payroll", "parent": "finance", "value": 30},
    {"name": "Audit", "parent": "finance", "value": 90},
    {"name": "Office", "parent": "facilities", "value": 20},
    {"name": "Equipment", "parent": "facilities", "value": 10},
]

# Create chart with sunburst type
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {"type": "sunburst", "width": 4800, "height": 2700, "backgroundColor": "#ffffff"}

# Title
chart.options.title = {
    "text": "sunburst-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle
chart.options.subtitle = {"text": "Budget Allocation by Department, Team, and Project", "style": {"fontSize": "32px"}}

# Credits
chart.options.credits = {"enabled": False}

# Series data
chart.options.series = [
    {
        "type": "sunburst",
        "data": data,
        "name": "Budget",
        "allowDrillToNode": True,
        "cursor": "pointer",
        "dataLabels": {
            "format": "{point.name}",
            "style": {"fontSize": "28px", "textOutline": "3px white", "fontWeight": "500"},
        },
        "levels": [
            {
                "level": 1,
                "colorByPoint": True,
                "dataLabels": {"style": {"fontSize": "42px", "fontWeight": "bold"}, "rotationMode": "circular"},
            },
            {
                "level": 2,
                "colorVariation": {"key": "brightness", "to": 0.15},
                "dataLabels": {"style": {"fontSize": "32px", "fontWeight": "600"}, "rotationMode": "circular"},
            },
            {
                "level": 3,
                "colorVariation": {"key": "brightness", "to": 0.35},
                "dataLabels": {
                    "style": {"fontSize": "28px"},
                    "rotationMode": "circular",
                    "allowOverlap": False,
                    "filter": {"property": "innerArcLength", "operator": ">", "value": 40},
                },
            },
        ],
    }
]

# Tooltip
chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": "<b>{point.name}</b>: ${point.value}K",
    "style": {"fontSize": "24px"},
}

# Download Highcharts JS and sunburst module
highcharts_url = "https://code.highcharts.com/highcharts.js"
sunburst_url = "https://code.highcharts.com/modules/sunburst.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(sunburst_url, timeout=30) as response:
    sunburst_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{sunburst_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save as plot.html for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
