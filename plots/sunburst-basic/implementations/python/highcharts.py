""" anyplot.ai
sunburst-basic: Basic Sunburst Chart
Library: highcharts unknown | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-04
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito categorical palette — first series always #009E73
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

# Total budget for center focal point annotation
TOTAL_BUDGET = 1240  # Engineering 720 + Marketing 310 + Operations 210 ($K)

# Data — Budget breakdown by department, team, and project (values in $K)
data = [
    # Root (center circle) — background-colored so it appears as text-only focal point
    {"id": "root", "name": f"${TOTAL_BUDGET:,}K", "color": PAGE_BG},
    # Level 1: Departments (innermost ring) — Okabe-Ito in canonical order
    {"id": "engineering", "name": "Engineering", "parent": "root", "color": OKABE_ITO[0]},
    {"id": "marketing", "name": "Marketing", "parent": "root", "color": OKABE_ITO[1]},
    {"id": "operations", "name": "Operations", "parent": "root", "color": OKABE_ITO[2]},
    # Level 2: Teams within each department
    {"id": "frontend", "name": "Frontend", "parent": "engineering", "value": 280},
    {"id": "backend", "name": "Backend", "parent": "engineering", "value": 350},
    {"id": "devops", "name": "DevOps", "parent": "engineering", "value": 90},
    {"id": "digital", "name": "Digital", "parent": "marketing", "value": 200},
    {"id": "content", "name": "Content", "parent": "marketing", "value": 70},
    {"id": "brand", "name": "Brand", "parent": "marketing", "value": 40},
    {"id": "hr", "name": "HR", "parent": "operations", "value": 60},
    {"id": "finance", "name": "Finance", "parent": "operations", "value": 120},
    {"id": "facilities", "name": "Facilities", "parent": "operations", "value": 30},
    # Level 3: Projects (outermost ring)
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

# Plot
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "sunburst",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "style": {"color": INK},
}

chart.options.title = {
    "text": "sunburst-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold", "color": INK},
}

chart.options.subtitle = {
    "text": "Budget Allocation by Department, Team, and Project ($K)",
    "style": {"fontSize": "32px", "color": INK_SOFT},
}

chart.options.credits = {"enabled": False}

chart.options.series = [
    {
        "type": "sunburst",
        "data": data,
        "name": "Budget ($K)",
        "allowDrillToNode": True,
        "cursor": "pointer",
        "dataLabels": {
            "format": "{point.name}",
            "style": {"fontSize": "28px", "textOutline": f"3px {PAGE_BG}", "fontWeight": "500", "color": INK},
        },
        "levels": [
            {
                "level": 1,  # Root center — total budget focal point annotation
                "dataLabels": {
                    "style": {"fontSize": "60px", "fontWeight": "bold", "color": INK, "textOutline": "none"},
                    "rotationMode": "horizontal",
                },
            },
            {
                "level": 2,  # Departments
                "colorByPoint": True,
                "dataLabels": {
                    "style": {"fontSize": "44px", "fontWeight": "bold", "color": INK, "textOutline": f"3px {PAGE_BG}"},
                    "rotationMode": "circular",
                },
            },
            {
                "level": 3,  # Teams
                "colorVariation": {"key": "brightness", "to": 0.15},
                "dataLabels": {
                    "style": {"fontSize": "34px", "fontWeight": "600", "color": INK, "textOutline": f"3px {PAGE_BG}"},
                    "rotationMode": "circular",
                },
            },
            {
                "level": 4,  # Projects
                "colorVariation": {"key": "brightness", "to": 0.35},
                "dataLabels": {
                    "style": {"fontSize": "28px", "color": INK, "textOutline": f"3px {PAGE_BG}"},
                    "rotationMode": "circular",
                    "allowOverlap": False,
                    "filter": {"property": "innerArcLength", "operator": ">", "value": 90},
                },
            },
        ],
    }
]

chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": "<b>{point.name}</b>: ${point.value}K",
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "style": {"color": INK, "fontSize": "24px"},
}

# Download Highcharts JS and sunburst module (inline for headless Chrome compatibility)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
sunburst_url = "https://cdn.jsdelivr.net/npm/highcharts/modules/sunburst.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(sunburst_url, timeout=30) as response:
    sunburst_js = response.read().decode("utf-8")

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{sunburst_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML artifact for interactive viewing
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot for PNG artifact
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
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
