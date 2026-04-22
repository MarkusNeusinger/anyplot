""" pyplots.ai
waterfall-basic: Basic Waterfall Chart
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Quarterly financial breakdown from revenue to net income
categories = [
    "Revenue",
    "Product Costs",
    "Operating Expenses",
    "Marketing",
    "R&D",
    "Other Income",
    "Taxes",
    "Net Income",
]

# Values: positive = increase, negative = decrease
# Revenue (start), costs (negative), income (positive), and final net income (total)
# Using colorblind-safe colors: Python Blue for totals, teal for increases, orange for decreases
values = [
    {"y": 500000, "isIntermediateSum": False, "color": "#306998"},  # Revenue - starting total (Python Blue)
    {"y": -150000, "color": "#E67300"},  # Product Costs (orange - decrease)
    {"y": -80000, "color": "#E67300"},  # Operating Expenses (orange - decrease)
    {"y": -45000, "color": "#E67300"},  # Marketing (orange - decrease)
    {"y": -35000, "color": "#E67300"},  # R&D (orange - decrease)
    {"y": 20000, "color": "#17BECF"},  # Other Income (teal - increase)
    {"y": -52000, "color": "#E67300"},  # Taxes (orange - decrease)
    {"isSum": True, "color": "#306998"},  # Net Income - ending total (Python Blue)
]

# Chart options for Highcharts waterfall
chart_options = {
    "chart": {
        "type": "waterfall",
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "marginBottom": 280,
        "style": {"fontFamily": "Arial, sans-serif"},
    },
    "title": {
        "text": "Quarterly Financial Breakdown · waterfall-basic · highcharts · pyplots.ai",
        "style": {"fontSize": "48px", "fontWeight": "bold"},
    },
    "xAxis": {
        "categories": categories,
        "title": {"text": "Category", "style": {"fontSize": "36px"}},
        "labels": {"style": {"fontSize": "28px"}, "rotation": -45, "y": 40},
    },
    "yAxis": {
        "title": {"text": "Amount ($)", "style": {"fontSize": "36px"}},
        "labels": {"style": {"fontSize": "28px"}, "formatter": "__FORMATTER_PLACEHOLDER__"},
        "gridLineColor": "#e0e0e0",
    },
    "legend": {"enabled": False},
    "tooltip": {"pointFormat": "<b>${point.y:,.0f}</b>", "style": {"fontSize": "24px"}},
    "plotOptions": {
        "waterfall": {
            "lineWidth": 2,
            "lineColor": "#333333",
            "borderWidth": 0,
            "pointPadding": 0.15,
            "dataLabels": {
                "enabled": True,
                "formatter": "__DATALABEL_FORMATTER_PLACEHOLDER__",
                "style": {"fontSize": "24px", "fontWeight": "bold", "textOutline": "2px white"},
            },
        }
    },
    "series": [
        {
            "name": "Financial Breakdown",
            "data": values,
            "upColor": "#17BECF",  # Teal for positive changes (colorblind-safe)
            "color": "#E67300",  # Orange for negative changes (colorblind-safe)
        }
    ],
}

# Download Highcharts JS for inline embedding
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Download highcharts-more.js (needed for waterfall chart)
highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Generate chart options JSON and add custom formatters
chart_options_json = json.dumps(chart_options)

# Replace placeholder with actual JavaScript formatter function for y-axis labels
y_axis_formatter = """function() {
    return '$' + Highcharts.numberFormat(this.value, 0, '.', ',');
}"""
chart_options_json = chart_options_json.replace('"__FORMATTER_PLACEHOLDER__"', y_axis_formatter)

# Replace placeholder with actual JavaScript formatter function for data labels
data_label_formatter = """function() {
    var val = this.y;
    var prefix = val >= 0 ? '+$' : '-$';
    if (this.point.isSum) {
        prefix = '$';
    }
    return prefix + Highcharts.numberFormat(Math.abs(val), 0, '.', ',');
}"""
chart_options_json = chart_options_json.replace('"__DATALABEL_FORMATTER_PLACEHOLDER__"', data_label_formatter)

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
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
