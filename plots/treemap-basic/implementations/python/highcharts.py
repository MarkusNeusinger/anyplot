""" pyplots.ai
treemap-basic: Basic Treemap
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Budget allocation by department and project
# Hierarchical structure with parent-child relationships
data = [
    # Parent categories (level 1)
    {"id": "engineering", "name": "Engineering", "color": "#306998"},
    {"id": "marketing", "name": "Marketing", "color": "#FFD43B"},
    {"id": "operations", "name": "Operations", "color": "#9467BD"},
    {"id": "sales", "name": "Sales", "color": "#17BECF"},
    {"id": "hr", "name": "HR", "color": "#8C564B"},
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
chart.options.chart = {"type": "treemap", "width": 4800, "height": 2700, "backgroundColor": "#ffffff"}

# Title
chart.options.title = {
    "text": "Budget Allocation · treemap-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "64px", "fontWeight": "bold"},
}

# Tooltip
chart.options.tooltip = {"style": {"fontSize": "36px"}, "pointFormat": "<b>{point.name}</b>: ${point.value:,.0f}"}

# Treemap series configuration
series_config = {
    "type": "treemap",
    "name": "Budget",
    "layoutAlgorithm": "squarified",
    "allowDrillToNode": True,
    "animationLimit": 1000,
    "dataLabels": {"enabled": True, "style": {"fontSize": "32px", "fontWeight": "bold", "textOutline": "2px contrast"}},
    "levels": [
        {
            "level": 1,
            "dataLabels": {
                "enabled": True,
                "align": "left",
                "verticalAlign": "top",
                "style": {"fontSize": "42px", "fontWeight": "bold", "textOutline": "3px contrast"},
            },
            "borderWidth": 4,
            "borderColor": "#ffffff",
        },
        {
            "level": 2,
            "dataLabels": {"enabled": True, "style": {"fontSize": "28px", "fontWeight": "normal"}},
            "borderWidth": 2,
            "borderColor": "#ffffff",
        },
    ],
    "data": data,
}

chart.options.series = [series_config]

# Disable legend for treemap (colors are visible in rectangles)
chart.options.legend = {"enabled": False}

# Download Highcharts JS and treemap module
highcharts_url = "https://code.highcharts.com/highcharts.js"
treemap_url = "https://code.highcharts.com/modules/treemap.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(treemap_url, timeout=30) as response:
    treemap_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{treemap_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/treemap.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(standalone_html)

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2900")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot_raw.png")
driver.quit()

# Crop to exact 4800x2700 dimensions
img = Image.open("plot_raw.png")
img_cropped = img.crop((0, 0, 4800, 2700))
img_cropped.save("plot.png")
Path("plot_raw.png").unlink()

Path(temp_path).unlink()  # Clean up temp file
