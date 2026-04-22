""" pyplots.ai
donut-nested: Nested Donut Chart
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

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


# Data - Budget allocation: departments (inner) and expense categories (outer)
# Inner ring: Department totals
departments = ["Engineering", "Marketing", "Operations", "Sales"]
dept_values = [4500000, 2800000, 1900000, 2200000]
dept_colors = ["#306998", "#FFD43B", "#9467BD", "#17BECF"]

# Outer ring: Expense categories within each department
# Using color variants (lighter shades) for each department's children
expenses = [
    # Engineering (blue family)
    {"name": "Salaries", "y": 2800000, "color": "#306998"},
    {"name": "Equipment", "y": 900000, "color": "#4A8BB3"},
    {"name": "Training", "y": 450000, "color": "#6BA5C9"},
    {"name": "Software", "y": 350000, "color": "#8CBFDF"},
    # Marketing (yellow family)
    {"name": "Advertising", "y": 1400000, "color": "#FFD43B"},
    {"name": "Events", "y": 700000, "color": "#FFE066"},
    {"name": "Content", "y": 400000, "color": "#FFEB99"},
    {"name": "Research", "y": 300000, "color": "#FFF5CC"},
    # Operations (purple family)
    {"name": "Facilities", "y": 800000, "color": "#9467BD"},
    {"name": "IT Support", "y": 600000, "color": "#A982CA"},
    {"name": "Logistics", "y": 500000, "color": "#BE9DD7"},
    # Sales (cyan family)
    {"name": "Commissions", "y": 1100000, "color": "#17BECF"},
    {"name": "Travel", "y": 600000, "color": "#4DCEE0"},
    {"name": "Client Entertainment", "y": 300000, "color": "#83DEF0"},
    {"name": "CRM Tools", "y": 200000, "color": "#B0EEF8"},
]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration - using square 3600x3600 format for pie charts
chart.options.chart = {"type": "pie", "width": 3600, "height": 3600, "backgroundColor": "#ffffff"}

# Title
chart.options.title = {
    "text": "Annual Budget Allocation by Department · donut-nested · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
    "y": 50,
}

# Subtitle
chart.options.subtitle = {
    "text": "Inner: Departments | Outer: Expense Categories",
    "style": {"fontSize": "32px"},
    "y": 100,
}

# Tooltip
chart.options.tooltip = {
    "pointFormat": "<b>{point.name}</b>: ${point.y:,.0f} ({point.percentage:.1f}%)",
    "style": {"fontSize": "24px"},
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
    "style": {"fontSize": "26px", "fontWeight": "bold", "textOutline": "2px white"},
    "color": "#333333",
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
    "style": {"fontSize": "20px", "fontWeight": "normal"},
    "connectorWidth": 2,
}

chart.add_series(inner_series)
chart.add_series(outer_series)

# Download Highcharts JS for inline embedding
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save the HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

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
img_cropped.save("plot.png")
Path("plot_raw.png").unlink()

Path(temp_path).unlink()
