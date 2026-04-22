""" pyplots.ai
dumbbell-basic: Basic Dumbbell Chart
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Employee satisfaction scores before and after policy changes
categories = [
    "Engineering",
    "Sales",
    "Marketing",
    "Customer Support",
    "Human Resources",
    "Finance",
    "Operations",
    "Research & Development",
]
before_scores = [65, 58, 72, 45, 68, 61, 53, 70]
after_scores = [82, 75, 85, 78, 80, 73, 71, 88]

# Sort by the magnitude of change (descending) to reveal patterns
changes = [after - before for before, after in zip(before_scores, after_scores, strict=True)]
sorted_data = sorted(
    zip(categories, before_scores, after_scores, changes, strict=True), key=lambda x: x[3], reverse=True
)
categories = [item[0] for item in sorted_data]
before_scores = [item[1] for item in sorted_data]
after_scores = [item[2] for item in sorted_data]

# Prepare data for dumbbell chart
dumbbell_data = []
for i, (before, after) in enumerate(zip(before_scores, after_scores, strict=True)):
    dumbbell_data.append({"x": i, "low": before, "high": after})

# Chart options for horizontal dumbbell chart
chart_options = {
    "chart": {
        "type": "dumbbell",
        "inverted": True,  # Horizontal orientation
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "marginLeft": 400,
        "marginBottom": 150,
        "style": {"fontFamily": "Arial, sans-serif"},
    },
    "title": {
        "text": "Employee Satisfaction Before/After · dumbbell-basic · highcharts · pyplots.ai",
        "style": {"fontSize": "52px", "fontWeight": "bold"},
    },
    "subtitle": {
        "text": "Satisfaction scores before and after policy changes by department",
        "style": {"fontSize": "34px", "color": "#666666"},
    },
    "xAxis": {
        "categories": categories,
        "title": {"text": None},  # Categories are self-explanatory
        "labels": {"style": {"fontSize": "32px"}},
    },
    "yAxis": {
        "min": 40,
        "max": 95,
        "title": {"text": "Satisfaction Score", "style": {"fontSize": "36px"}},
        "labels": {"style": {"fontSize": "28px"}},
        "gridLineColor": "#e0e0e0",
        "gridLineDashStyle": "Dash",
    },
    "legend": {
        "enabled": True,
        "align": "right",
        "verticalAlign": "top",
        "layout": "vertical",
        "x": -50,
        "y": 100,
        "itemStyle": {"fontSize": "28px"},
        "symbolHeight": 20,
        "symbolWidth": 40,
    },
    "plotOptions": {
        "dumbbell": {
            "connectorWidth": 5,
            "connectorColor": "#888888",
            "lowColor": "#306998",  # Python Blue for "before"
            "color": "#FFD43B",  # Python Yellow for "after"
            "marker": {"radius": 18},
            "dataLabels": {
                "enabled": True,
                "style": {"fontSize": "24px", "fontWeight": "bold", "textOutline": "none"},
                "y": 0,
            },
        }
    },
    "series": [{"name": "Before → After", "data": dumbbell_data, "lowColor": "#306998", "color": "#FFD43B"}],
}

# Download Highcharts JS and required modules for inline embedding
highcharts_url = "https://code.highcharts.com/highcharts.js"
highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
dumbbell_url = "https://code.highcharts.com/modules/dumbbell.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")
with urllib.request.urlopen(dumbbell_url, timeout=30) as response:
    dumbbell_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
chart_options_json = json.dumps(chart_options)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
    <script>{dumbbell_js}</script>
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
