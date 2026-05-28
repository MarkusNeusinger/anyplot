""" anyplot.ai
donut-nested: Nested Donut Chart
Library: highcharts unknown | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-08
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.pie import PieSeries
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme-adaptive tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette - first series is always #009E73 (brand green)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Budget allocation: departments (inner) and expense categories (outer)
departments = ["Engineering", "Marketing", "Operations", "Sales"]
dept_values = [4500000, 2800000, 1900000, 2200000]
dept_colors = IMPRINT

# Outer ring: Expense categories with color variants per department
expenses = [
    # Engineering (green family - Okabe-Ito position 1 variants)
    {"name": "Salaries", "y": 2800000, "color": "#009E73"},
    {"name": "Equipment", "y": 900000, "color": "#20B894"},
    {"name": "Training", "y": 450000, "color": "#38D4A3"},
    {"name": "Software", "y": 350000, "color": "#50EEB2"},
    # Marketing (vermillion family - Okabe-Ito position 2 variants)
    {"name": "Advertising", "y": 1400000, "color": "#C475FD"},
    {"name": "Events", "y": 700000, "color": "#E1791D"},
    {"name": "Content", "y": 400000, "color": "#ED9439"},
    {"name": "Research", "y": 300000, "color": "#F9AF56"},
    # Operations (blue family - Okabe-Ito position 3 variants)
    {"name": "Facilities", "y": 800000, "color": "#4467A3"},
    {"name": "IT Support", "y": 600000, "color": "#2287CC"},
    {"name": "Logistics", "y": 500000, "color": "#449CE6"},
    # Sales (reddish purple family - Okabe-Ito position 4 variants)
    {"name": "Commissions", "y": 1100000, "color": "#BD8233"},
    {"name": "Travel", "y": 600000, "color": "#DB8FBB"},
    {"name": "Client Entertainment", "y": 300000, "color": "#EAA5CF"},
    {"name": "CRM Tools", "y": 200000, "color": "#F9BBE3"},
]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration - using square 3600x3600 format for pie charts
chart.options.chart = {"type": "pie", "width": 3600, "height": 3600, "backgroundColor": PAGE_BG}

# Title
chart.options.title = {
    "text": "donut-nested: Budget Allocation Hierarchy",
    "style": {"fontSize": "48px", "fontWeight": "bold", "color": INK},
    "y": 50,
}

# Subtitle
chart.options.subtitle = {
    "text": "Departments (inner) and expense categories (outer)",
    "style": {"fontSize": "32px", "color": INK_SOFT},
    "y": 100,
}

# Tooltip
chart.options.tooltip = {
    "pointFormat": "<b>{point.name}</b>: ${point.y:,.0f} ({point.percentage:.1f}%)",
    "style": {"fontSize": "24px", "color": INK},
}

# Legend disabled for cleaner nested donut
chart.options.legend = {"enabled": False}

# Inner ring (departments) - smaller, centered
inner_series = PieSeries()
inner_series.name = "Departments"
inner_series.data = [
    {"name": dept, "y": val, "color": col} for dept, val, col in zip(departments, dept_values, dept_colors, strict=True)
]
inner_series.size = "45%"
inner_series.inner_size = "20%"
inner_series.data_labels = {
    "enabled": True,
    "format": "<b>{point.name}</b><br>${point.y:,.0f}",
    "distance": -70,
    "style": {"fontSize": "26px", "fontWeight": "bold", "textOutline": "2px " + PAGE_BG},
    "color": INK,
}

# Outer ring (expenses) - larger, surrounding inner
outer_series = PieSeries()
outer_series.name = "Expenses"
outer_series.data = expenses
outer_series.size = "85%"
outer_series.inner_size = "55%"
outer_series.data_labels = {
    "enabled": True,
    "format": "{point.name}",
    "distance": 25,
    "style": {"fontSize": "20px", "fontWeight": "normal", "color": INK},
    "connectorWidth": 2,
}

chart.add_series(inner_series)
chart.add_series(outer_series)

# Download Highcharts JS for inline embedding (try multiple CDNs)
cdn_urls = ["https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js", "https://code.highcharts.com/highcharts.js"]
highcharts_js = None
for url in cdn_urls:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
            break
    except Exception:
        continue

if not highcharts_js:
    raise RuntimeError("Failed to download Highcharts JS from all CDN sources")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML for interactive version (theme-specific)
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
chrome_options.add_argument("--window-size=3600,3700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot_raw.png")
driver.quit()

# Crop to exact 3600x3600 dimensions
img = Image.open("plot_raw.png")
img_cropped = img.crop((0, 0, 3600, 3600))
img_cropped.save(f"plot-{THEME}.png")
Path("plot_raw.png").unlink()

Path(temp_path).unlink()
