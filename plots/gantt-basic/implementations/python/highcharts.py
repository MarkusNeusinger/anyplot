""" pyplots.ai
gantt-basic: Basic Gantt Chart
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-27
"""

import tempfile
import time
import urllib.request
from datetime import datetime
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Project tasks with start/end dates and categories
tasks = [
    {
        "name": "Requirements Analysis",
        "start": datetime(2025, 1, 6),
        "end": datetime(2025, 1, 17),
        "category": "Planning",
    },
    {"name": "System Design", "start": datetime(2025, 1, 13), "end": datetime(2025, 1, 31), "category": "Planning"},
    {"name": "Database Schema", "start": datetime(2025, 1, 27), "end": datetime(2025, 2, 7), "category": "Development"},
    {"name": "Backend API", "start": datetime(2025, 2, 3), "end": datetime(2025, 3, 7), "category": "Development"},
    {"name": "Frontend UI", "start": datetime(2025, 2, 10), "end": datetime(2025, 3, 14), "category": "Development"},
    {"name": "Integration", "start": datetime(2025, 3, 10), "end": datetime(2025, 3, 21), "category": "Development"},
    {"name": "Unit Testing", "start": datetime(2025, 2, 17), "end": datetime(2025, 3, 14), "category": "Testing"},
    {"name": "System Testing", "start": datetime(2025, 3, 17), "end": datetime(2025, 3, 28), "category": "Testing"},
    {"name": "User Acceptance", "start": datetime(2025, 3, 24), "end": datetime(2025, 4, 4), "category": "Testing"},
    {"name": "Documentation", "start": datetime(2025, 3, 3), "end": datetime(2025, 3, 28), "category": "Deployment"},
    {"name": "Training", "start": datetime(2025, 3, 31), "end": datetime(2025, 4, 11), "category": "Deployment"},
    {"name": "Go Live", "start": datetime(2025, 4, 14), "end": datetime(2025, 4, 18), "category": "Deployment"},
]

# Colors for categories (colorblind-safe)
category_colors = {
    "Planning": "#306998",  # Python Blue
    "Development": "#FFD43B",  # Python Yellow
    "Testing": "#9467BD",  # Purple
    "Deployment": "#17BECF",  # Cyan
}

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "xrange",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "spacingBottom": 120,
    "marginLeft": 420,
    "marginTop": 150,
}

# Set colors at chart level
chart.options.colors = ["#306998", "#FFD43B", "#9467BD", "#17BECF"]

# Title
chart.options.title = {
    "text": "gantt-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
    "y": 60,
}

# X-axis (time)
today_ts = int(datetime(2025, 2, 15).timestamp() * 1000)
chart.options.x_axis = {
    "type": "datetime",
    "dateTimeLabelFormats": {"week": "%e %b", "month": "%b '%y"},
    "title": {"text": "Timeline", "style": {"fontSize": "32px"}},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "plotLines": [
        {
            "value": today_ts,
            "color": "#E53935",
            "width": 4,
            "zIndex": 10,
            "label": {
                "text": "Today (Feb 15)",
                "style": {"fontSize": "26px", "color": "#E53935", "fontWeight": "bold"},
                "rotation": 0,
                "align": "center",
                "y": -20,
            },
        }
    ],
}

# Y-axis (tasks)
task_names = [t["name"] for t in tasks]
chart.options.y_axis = {
    "type": "category",
    "categories": task_names,
    "title": {"text": "Tasks", "style": {"fontSize": "32px"}},
    "labels": {"style": {"fontSize": "26px"}},
    "gridLineWidth": 1,
    "gridLineColor": "#f0f0f0",
    "reversed": True,
}

# Legend configuration - show categories
chart.options.legend = {
    "enabled": True,
    "align": "center",
    "verticalAlign": "bottom",
    "layout": "horizontal",
    "itemStyle": {"fontSize": "32px"},
    "symbolRadius": 4,
    "symbolWidth": 50,
    "symbolHeight": 30,
    "floating": False,
}

# Tooltip configuration
chart.options.tooltip = {
    "headerFormat": '<span style="font-size: 24px; font-weight: bold;">{point.key}</span><br/>',
    "pointFormat": '<span style="font-size: 22px">{point.x:%b %e} - {point.x2:%b %e, %Y}</span>',
}

# Create series for each category (for legend with color coding)
# Order categories to appear properly in legend
category_order = ["Planning", "Development", "Testing", "Deployment"]
series_list = []

for category in category_order:
    color = category_colors[category]
    category_data = []
    for i, task in enumerate(tasks):
        if task["category"] == category:
            category_data.append(
                {
                    "x": int(task["start"].timestamp() * 1000),
                    "x2": int(task["end"].timestamp() * 1000),
                    "y": i,
                    "name": task["name"],
                    "color": color,
                }
            )

    series_list.append(
        {
            "type": "xrange",
            "name": category,
            "color": color,
            "pointWidth": 55,
            "data": category_data,
            "dataLabels": {"enabled": False},
            "borderRadius": 6,
            "borderWidth": 2,
            "borderColor": "#555555",
        }
    )

chart.options.series = series_list

# Download Highcharts JS modules
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

xrange_url = "https://code.highcharts.com/modules/xrange.js"
with urllib.request.urlopen(xrange_url, timeout=30) as response:
    xrange_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{xrange_js}</script>
</head>
<body style="margin:0; padding:0; background: #ffffff;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot with Selenium - use element screenshot for exact dimensions
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=5000,3000")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

# Take screenshot of the chart container element for exact dimensions
container = driver.find_element("id", "container")
container.screenshot("plot.png")

driver.quit()
Path(temp_path).unlink()
