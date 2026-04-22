""" pyplots.ai
donut-basic: Basic Donut Chart
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
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


# Data - Budget allocation by category
categories = ["Marketing", "Development", "Operations", "Research", "Support"]
values = [28, 35, 18, 12, 7]
total = sum(values)

# Colorblind-safe colors (Python Blue first, then complementary)
colors = ["#306998", "#FFD43B", "#9467BD", "#17BECF", "#8C564B"]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "pie",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "spacingBottom": 100,
    "spacingTop": 50,
}

# Title
chart.options.title = {
    "text": "donut-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle in center showing total
chart.options.subtitle = {
    "text": f"Total<br><b>${total}M</b>",
    "align": "center",
    "verticalAlign": "middle",
    "style": {"fontSize": "42px"},
    "y": 60,
}

# Colors
chart.options.colors = colors

# Plot options for donut (pie with innerSize)
chart.options.plot_options = {
    "pie": {
        "allowPointSelect": True,
        "cursor": "pointer",
        "innerSize": "55%",  # This creates the donut hole
        "dataLabels": {
            "enabled": True,
            "format": "<b>{point.name}</b>: {point.percentage:.1f}%",
            "style": {"fontSize": "28px"},
            "distance": 30,
        },
        "showInLegend": True,
    }
}

# Legend
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "middle",
    "layout": "vertical",
    "itemStyle": {"fontSize": "28px"},
}

# Create pie series with data
series = PieSeries()
series.name = "Budget"
series.data = [{"name": cat, "y": val} for cat, val in zip(categories, values, strict=True)]

chart.add_series(series)

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
    <div id="container" style="width: 4800px; height: 2700px;"></div>
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
