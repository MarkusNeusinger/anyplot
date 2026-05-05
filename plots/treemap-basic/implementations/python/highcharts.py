"""anyplot.ai
treemap-basic: Basic Treemap
Library: highcharts | Python 3.13
Quality: pending | Created: 2025-05-05
"""

import os
import tempfile
import time
from pathlib import Path

import requests
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
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette (positions 1-7)
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

# Data - Budget allocation by department and project
data = [
    # Parent categories (level 1) with Okabe-Ito colors
    {"id": "engineering", "name": "Engineering", "color": OKABE_ITO[0]},
    {"id": "marketing", "name": "Marketing", "color": OKABE_ITO[1]},
    {"id": "operations", "name": "Operations", "color": OKABE_ITO[2]},
    {"id": "sales", "name": "Sales", "color": OKABE_ITO[3]},
    {"id": "hr", "name": "HR", "color": OKABE_ITO[4]},
    # Engineering subcategories
    {"name": "Backend Dev", "parent": "engineering", "value": 45000},
    {"name": "Frontend Dev", "parent": "engineering", "value": 38000},
    {"name": "DevOps", "parent": "engineering", "value": 25000},
    {"name": "QA Testing", "parent": "engineering", "value": 18000},
    # Marketing subcategories
    {"name": "Digital Ads", "parent": "marketing", "value": 32000},
    {"name": "Content", "parent": "marketing", "value": 22000},
    {"name": "Events", "parent": "marketing", "value": 15000},
    {"name": "Branding", "parent": "marketing", "value": 12000},
    # Operations subcategories
    {"name": "Infrastructure", "parent": "operations", "value": 28000},
    {"name": "Logistics", "parent": "operations", "value": 20000},
    {"name": "Facilities", "parent": "operations", "value": 16000},
    # Sales subcategories
    {"name": "Enterprise", "parent": "sales", "value": 35000},
    {"name": "SMB", "parent": "sales", "value": 24000},
    {"name": "Partner", "parent": "sales", "value": 18000},
    # HR subcategories
    {"name": "Recruiting", "parent": "hr", "value": 15000},
    {"name": "Training", "parent": "hr", "value": 12000},
    {"name": "Benefits", "parent": "hr", "value": 10000},
]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "treemap",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginTop": 120,
    "marginBottom": 100,
    "marginLeft": 100,
    "marginRight": 100,
}

# Title
chart.options.title = {
    "text": "treemap-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "color": INK, "fontWeight": "normal"},
}

# Tooltip with formatted values
chart.options.tooltip = {
    "style": {"fontSize": "18px", "color": INK},
    "pointFormat": "<b>{point.name}</b><br/>Budget: ${point.value:,.0f}",
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}

# Treemap series configuration with Okabe-Ito colors
series_config = {
    "type": "treemap",
    "name": "Budget",
    "layoutAlgorithm": "squarified",
    "allowDrillToNode": True,
    "colors": OKABE_ITO,
    "dataLabels": {"enabled": True, "style": {"fontSize": "20px", "color": INK}},
    "levels": [
        {
            "level": 1,
            "dataLabels": {
                "enabled": True,
                "align": "center",
                "verticalAlign": "middle",
                "style": {"fontSize": "24px", "fontWeight": "normal", "color": INK},
            },
            "borderWidth": 3,
            "borderColor": PAGE_BG,
        },
        {
            "level": 2,
            "dataLabels": {"enabled": True, "style": {"fontSize": "18px", "color": INK}},
            "borderWidth": 2,
            "borderColor": PAGE_BG,
        },
    ],
    "data": data,
}

chart.options.series = [series_config]

# Disable legend for treemap (colors are visible in rectangles)
chart.options.legend = {"enabled": False}

# Download Highcharts JS and treemap module with fallback
highcharts_url = "https://code.highcharts.com/highcharts.js"
treemap_url = "https://code.highcharts.com/modules/treemap.js"

try:
    resp = requests.get(highcharts_url, timeout=30)
    resp.raise_for_status()
    highcharts_js = resp.text
except Exception:
    # Fallback to alternate CDN
    resp = requests.get("https://cdnjs.cloudflare.com/ajax/libs/highcharts/10.3.2/highcharts.min.js", timeout=30)
    resp.raise_for_status()
    highcharts_js = resp.text

try:
    resp = requests.get(treemap_url, timeout=30)
    resp.raise_for_status()
    treemap_js = resp.text
except Exception:
    # Fallback to alternate CDN
    resp = requests.get("https://cdnjs.cloudflare.com/ajax/libs/highcharts/10.3.2/modules/treemap.min.js", timeout=30)
    resp.raise_for_status()
    treemap_js = resp.text

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{treemap_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML for interactive version
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot
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
