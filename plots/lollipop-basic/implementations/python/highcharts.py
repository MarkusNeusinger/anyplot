""" pyplots.ai
lollipop-basic: Basic Lollipop Chart
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Product sales by category, sorted by value for readability
categories = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books", "Toys", "Jewelry", "Automotive"]
values = [8500, 6200, 5100, 4300, 3800, 2900, 2400, 1800]

# Sort data by value (descending) for better visualization
sorted_data = sorted(zip(categories, values, strict=True), key=lambda x: x[1], reverse=True)
categories = [item[0] for item in sorted_data]
values = [item[1] for item in sorted_data]

# Chart options - using scatter for dots and column with very thin width for stems
chart_options = {
    "chart": {
        "type": "scatter",
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "marginBottom": 250,
        "style": {"fontFamily": "Arial, sans-serif"},
    },
    "title": {"text": "lollipop-basic · highcharts · pyplots.ai", "style": {"fontSize": "48px", "fontWeight": "bold"}},
    "xAxis": {
        "categories": categories,
        "title": {"text": "Product Category", "style": {"fontSize": "36px"}},
        "labels": {"style": {"fontSize": "28px"}},
    },
    "yAxis": {
        "min": 0,
        "title": {"text": "Sales (Units)", "style": {"fontSize": "36px"}},
        "labels": {"style": {"fontSize": "28px"}},
        "gridLineColor": "#e0e0e0",
        "gridLineDashStyle": "Dash",
    },
    "legend": {"enabled": False},
    "plotOptions": {
        "scatter": {"marker": {"radius": 20, "symbol": "circle"}},
        "column": {"pointWidth": 4, "borderWidth": 0},
    },
    "series": [
        # Stems (thin columns from 0 to value)
        {"type": "column", "name": "Sales", "data": values, "color": "#306998", "enableMouseTracking": False},
        # Dots (scatter points at the top of each stem)
        {
            "type": "scatter",
            "name": "Sales",
            "data": values,
            "color": "#306998",
            "marker": {"radius": 20, "fillColor": "#306998", "lineWidth": 3, "lineColor": "#ffffff"},
            "dataLabels": {
                "enabled": True,
                "format": "{y:,.0f}",
                "style": {"fontSize": "22px", "fontWeight": "bold"},
                "verticalAlign": "bottom",
                "y": -15,
            },
        },
    ],
}

# Download Highcharts JS for inline embedding
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
chart_options_json = json.dumps(chart_options)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            Highcharts.chart('container', {chart_options_json});
        }});
    </script>
</body>
</html>"""

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save the HTML for interactive viewing
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
